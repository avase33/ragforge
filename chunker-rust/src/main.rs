//! HTTP front-end for the semantic chunker (axum).
//!   POST /chunk  { doc_id, text, max_words? }  -> { doc_id, chunks }
//!   GET  /healthz

use axum::{routing::{get, post}, Json, Router};
use ragforge_chunker::{chunk, Chunk};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct ChunkRequest {
    #[serde(default)]
    doc_id: String,
    text: String,
    #[serde(default = "default_max_words")]
    max_words: usize,
}

fn default_max_words() -> usize {
    120
}

#[derive(Serialize)]
struct ChunkResponse {
    doc_id: String,
    chunks: Vec<Chunk>,
}

async fn chunk_handler(Json(req): Json<ChunkRequest>) -> Json<ChunkResponse> {
    let max = req.max_words.max(10);
    Json(ChunkResponse {
        doc_id: req.doc_id,
        chunks: chunk(&req.text, max),
    })
}

async fn healthz() -> Json<serde_json::Value> {
    Json(serde_json::json!({ "status": "ok" }))
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/chunk", post(chunk_handler))
        .route("/healthz", get(healthz));

    let addr = std::env::var("RAGFORGE_CHUNKER_ADDR").unwrap_or_else(|_| "0.0.0.0:8093".into());
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    println!("ragforge-chunker listening on {addr}");
    axum::serve(listener, app).await.unwrap();
}
