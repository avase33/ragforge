// Package pipeline turns a document change into indexed vectors: it chunks the
// text via the Rust service and upserts the chunks into the Python engine. A
// bounded queue + worker pool decouples change detection from processing.
package pipeline

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"sync/atomic"
	"time"

	"ragforge/crawler/internal/config"
)

// Event is one document change (see proto/protocol.md).
type Event struct {
	DocID  string `json:"doc_id"`
	Action string `json:"action"` // "upsert" | "delete"
	Text   string `json:"text,omitempty"`
}

type chunk struct {
	Index      int     `json:"index"`
	Text       string  `json:"text"`
	NSentences int     `json:"n_sentences"`
	Cohesion   float64 `json:"cohesion"`
}

type chunkResponse struct {
	DocID  string  `json:"doc_id"`
	Chunks []chunk `json:"chunks"`
}

// Pipeline holds the worker pool and downstream clients.
type Pipeline struct {
	cfg       config.Config
	http      *http.Client
	jobs      chan Event
	processed int64
	failed    int64
}

func New(cfg config.Config) *Pipeline {
	p := &Pipeline{
		cfg:  cfg,
		http: &http.Client{Timeout: 5 * time.Second},
		jobs: make(chan Event, 512),
	}
	for i := 0; i < max(cfg.Workers, 1); i++ {
		go p.worker()
	}
	return p
}

// Submit enqueues a change, dropping it if the pool is saturated.
func (p *Pipeline) Submit(e Event) bool {
	select {
	case p.jobs <- e:
		return true
	default:
		return false
	}
}

func (p *Pipeline) worker() {
	for e := range p.jobs {
		if err := p.process(e); err != nil {
			atomic.AddInt64(&p.failed, 1)
			continue
		}
		atomic.AddInt64(&p.processed, 1)
	}
}

func (p *Pipeline) postJSON(url string, in, out any) error {
	body, err := json.Marshal(in)
	if err != nil {
		return err
	}
	resp, err := p.http.Post(url, "application/json", bytes.NewReader(body))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		io.Copy(io.Discard, resp.Body)
		return io.EOF
	}
	if out == nil {
		io.Copy(io.Discard, resp.Body)
		return nil
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

func (p *Pipeline) process(e Event) error {
	if e.Action == "delete" {
		return p.postJSON(p.cfg.EngineURL+"/ingest",
			map[string]any{"doc_id": e.DocID, "action": "delete"}, nil)
	}
	var cr chunkResponse
	if err := p.postJSON(p.cfg.ChunkerURL+"/chunk",
		map[string]any{"doc_id": e.DocID, "text": e.Text, "max_words": p.cfg.MaxWords},
		&cr); err != nil {
		return err
	}
	return p.postJSON(p.cfg.EngineURL+"/ingest",
		map[string]any{"doc_id": e.DocID, "action": "upsert", "chunks": cr.Chunks}, nil)
}

// Stats reports processing counters and queue depth.
func (p *Pipeline) Stats() (processed, failed int64, queued int) {
	return atomic.LoadInt64(&p.processed), atomic.LoadInt64(&p.failed), len(p.jobs)
}
