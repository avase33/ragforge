// Command ragforge-crawler watches document sources (a directory + webhooks),
// detects add/modify/delete by content hash, and drives each change through the
// Rust semantic chunker and the Python vector engine via a worker pool.
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"ragforge/crawler/internal/config"
	"ragforge/crawler/internal/pipeline"
	"ragforge/crawler/internal/watch"
)

func main() {
	cfg := config.Load()
	pipe := pipeline.New(cfg)
	watcher := watch.New(cfg.WatchDir)

	// periodic filesystem scan
	if cfg.ScanInterval > 0 {
		go func() {
			t := time.NewTicker(time.Duration(cfg.ScanInterval) * time.Second)
			defer t.Stop()
			for {
				for _, e := range watcher.Scan() {
					pipe.Submit(e)
				}
				<-t.C
			}
		}()
	}

	mux := http.NewServeMux()

	mux.HandleFunc("POST /webhook", func(w http.ResponseWriter, r *http.Request) {
		var e pipeline.Event
		if err := json.NewDecoder(r.Body).Decode(&e); err != nil || e.DocID == "" {
			http.Error(w, "bad event", http.StatusBadRequest)
			return
		}
		if e.Action == "" {
			e.Action = "upsert"
		}
		ok := pipe.Submit(e)
		writeJSON(w, map[string]any{"queued": ok})
	})

	mux.HandleFunc("POST /scan", func(w http.ResponseWriter, _ *http.Request) {
		events := watcher.Scan()
		for _, e := range events {
			pipe.Submit(e)
		}
		writeJSON(w, map[string]any{"changes": len(events)})
	})

	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) {
		processed, failed, queued := pipe.Stats()
		writeJSON(w, map[string]any{
			"status":    "ok",
			"tracked":   watcher.Tracked(),
			"processed": processed,
			"failed":    failed,
			"queued":    queued,
		})
	})

	log.Printf("ragforge-crawler on %s (watch=%s chunker=%s engine=%s)",
		cfg.Addr, cfg.WatchDir, cfg.ChunkerURL, cfg.EngineURL)
	if err := http.ListenAndServe(cfg.Addr, mux); err != nil {
		log.Fatal(err)
	}
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(v)
}
