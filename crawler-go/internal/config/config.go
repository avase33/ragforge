package config

import (
	"os"
	"strconv"
)

type Config struct {
	Addr         string
	ChunkerURL   string
	EngineURL    string
	WatchDir     string
	Workers      int
	MaxWords     int
	ScanInterval int // seconds; 0 disables periodic scanning
}

func getenv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func atoi(s string, def int) int {
	if v, err := strconv.Atoi(s); err == nil {
		return v
	}
	return def
}

func Load() Config {
	return Config{
		Addr:         getenv("RAGFORGE_ADDR", ":8080"),
		ChunkerURL:   getenv("RAGFORGE_CHUNKER_URL", "http://localhost:8093"),
		EngineURL:    getenv("RAGFORGE_ENGINE_URL", "http://localhost:8000"),
		WatchDir:     getenv("RAGFORGE_WATCH_DIR", "./corpus"),
		Workers:      atoi(os.Getenv("RAGFORGE_WORKERS"), 4),
		MaxWords:     atoi(os.Getenv("RAGFORGE_MAX_WORDS"), 120),
		ScanInterval: atoi(os.Getenv("RAGFORGE_SCAN_INTERVAL"), 5),
	}
}
