// Package watch detects document changes on disk by content hash: new or
// modified files become "upsert" events, vanished files become "delete" events.
// It is the offline stand-in for Slack/Notion/GitHub webhooks.
package watch

import (
	"crypto/sha256"
	"encoding/hex"
	"io/fs"
	"os"
	"path/filepath"
	"sync"

	"ragforge/crawler/internal/pipeline"
)

var textExts = map[string]bool{".md": true, ".markdown": true, ".txt": true}

type Watcher struct {
	dir   string
	mu    sync.Mutex
	known map[string]string // doc_id -> content hash
}

func New(dir string) *Watcher {
	return &Watcher{dir: dir, known: make(map[string]string)}
}

func hash(b []byte) string {
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:8])
}

// Scan walks the watch directory and returns the change events since last call.
func (w *Watcher) Scan() []pipeline.Event {
	w.mu.Lock()
	defer w.mu.Unlock()

	seen := make(map[string]bool)
	var events []pipeline.Event

	_ = filepath.WalkDir(w.dir, func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		if !textExts[filepath.Ext(path)] {
			return nil
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		rel, err := filepath.Rel(w.dir, path)
		if err != nil {
			return nil
		}
		rel = filepath.ToSlash(rel)
		seen[rel] = true
		h := hash(data)
		if w.known[rel] != h {
			w.known[rel] = h
			events = append(events, pipeline.Event{DocID: rel, Action: "upsert", Text: string(data)})
		}
		return nil
	})

	for id := range w.known {
		if !seen[id] {
			delete(w.known, id)
			events = append(events, pipeline.Event{DocID: id, Action: "delete"})
		}
	}
	return events
}

// Tracked returns how many documents are currently indexed.
func (w *Watcher) Tracked() int {
	w.mu.Lock()
	defer w.mu.Unlock()
	return len(w.known)
}
