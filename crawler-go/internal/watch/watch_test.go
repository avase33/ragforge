package watch

import (
	"os"
	"path/filepath"
	"testing"
)

func write(t *testing.T, path, content string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestDetectsAddModifyDelete(t *testing.T) {
	dir := t.TempDir()
	w := New(dir)

	a := filepath.Join(dir, "a.md")
	write(t, a, "hello world")

	// add
	ev := w.Scan()
	if len(ev) != 1 || ev[0].Action != "upsert" || ev[0].DocID != "a.md" {
		t.Fatalf("add: %+v", ev)
	}

	// no change
	if ev := w.Scan(); len(ev) != 0 {
		t.Fatalf("expected no changes, got %+v", ev)
	}

	// modify
	write(t, a, "hello world again")
	ev = w.Scan()
	if len(ev) != 1 || ev[0].Action != "upsert" {
		t.Fatalf("modify: %+v", ev)
	}

	// delete
	os.Remove(a)
	ev = w.Scan()
	if len(ev) != 1 || ev[0].Action != "delete" || ev[0].DocID != "a.md" {
		t.Fatalf("delete: %+v", ev)
	}
	if w.Tracked() != 0 {
		t.Fatalf("tracked should be 0, got %d", w.Tracked())
	}
}

func TestIgnoresNonText(t *testing.T) {
	dir := t.TempDir()
	w := New(dir)
	write(t, filepath.Join(dir, "image.png"), "not text")
	if ev := w.Scan(); len(ev) != 0 {
		t.Fatalf("png should be ignored, got %+v", ev)
	}
}
