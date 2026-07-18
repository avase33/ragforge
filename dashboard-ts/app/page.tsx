"use client";

import { useEffect, useRef, useState } from "react";

const ENGINE = process.env.NEXT_PUBLIC_ENGINE_URL || "http://localhost:8000";

type GraphDoc = { doc_id: string; chunks: number; stale: boolean };
type Graph = { docs: GraphDoc[]; edges: { from: string; to: string }[] };
type Context = { id: string; text: string; score: number };
type Answer = {
  answer: string;
  contexts: Context[];
  scores: Record<string, number>;
};

function drawGraph(canvas: HTMLCanvasElement, graph: Graph) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const cx = W / 2;
  const cy = H / 2;
  const R = Math.min(W, H) * 0.32;
  const docs = graph.docs;
  const pos: Record<string, { x: number; y: number }> = {};

  docs.forEach((d, i) => {
    const a = (2 * Math.PI * i) / Math.max(docs.length, 1);
    const x = cx + R * Math.cos(a);
    const y = cy + R * Math.sin(a);
    pos[d.doc_id] = { x, y };
    // chunk satellites
    for (let c = 0; c < d.chunks; c++) {
      const ca = a + (c - (d.chunks - 1) / 2) * 0.22;
      const cr = R + 70;
      const chx = cx + cr * Math.cos(ca);
      const chy = cy + cr * Math.sin(ca);
      pos[`${d.doc_id}#${c}`] = { x: chx, y: chy };
    }
  });

  // edges
  ctx.strokeStyle = "#21313d";
  for (const e of graph.edges) {
    const a = pos[e.from];
    const b = pos[e.to];
    if (!a || !b) continue;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  }
  // chunk nodes
  for (const d of docs) {
    for (let c = 0; c < d.chunks; c++) {
      const p = pos[`${d.doc_id}#${c}`];
      if (!p) continue;
      ctx.fillStyle = "#3b82f6";
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  // doc nodes + labels
  for (const d of docs) {
    const p = pos[d.doc_id];
    ctx.fillStyle = d.stale ? "#ff7b72" : "#4ec9b0";
    ctx.beginPath();
    ctx.arc(p.x, p.y, 9, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#c9d1d9";
    ctx.font = "12px monospace";
    ctx.fillText(d.doc_id, p.x + 12, p.y + 4);
  }
}

export default function Page() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [graph, setGraph] = useState<Graph>({ docs: [], edges: [] });
  const [question, setQuestion] = useState("how do I request time off?");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("connecting");

  const loadGraph = async () => {
    try {
      const res = await fetch(`${ENGINE}/graph`);
      const g = (await res.json()) as Graph;
      setGraph(g);
      setStatus("live");
    } catch {
      setStatus("offline");
    }
  };

  const ask = async () => {
    setBusy(true);
    try {
      const res = await fetch(`${ENGINE}/query`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question, k: 4 }),
      });
      setAnswer((await res.json()) as Answer);
    } catch {
      setAnswer(null);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    loadGraph();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (canvasRef.current) drawGraph(canvasRef.current, graph);
  }, [graph]);

  return (
    <main style={{ padding: 24, maxWidth: 1000, margin: "0 auto" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>ragforge</h1>
        <span style={{ fontSize: 13, color: status === "live" ? "#4ec9b0" : "#ff7b72" }}>
          engine {status} · {graph.docs.length} docs
        </span>
      </header>

      <section style={{ marginTop: 16 }}>
        <div style={{ color: "#8b949e", fontSize: 13, marginBottom: 6 }}>
          knowledge graph (green = doc, blue = chunk)
        </div>
        <canvas
          ref={canvasRef}
          width={960}
          height={420}
          style={{ width: "100%", background: "#0d1117", border: "1px solid #30363d", borderRadius: 10 }}
        />
        <button onClick={loadGraph} style={{ ...btn("#30363d"), marginTop: 8 }}>refresh graph</button>
      </section>

      <section style={{ marginTop: 24 }}>
        <div style={{ color: "#8b949e", fontSize: 13, marginBottom: 6 }}>ask the corpus</div>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            style={{ flex: 1, padding: "8px 10px", background: "#0d1117", border: "1px solid #30363d", borderRadius: 8, color: "#e6edf3" }}
          />
          <button onClick={ask} disabled={busy} style={btn("#238636")}>
            {busy ? "…" : "ask"}
          </button>
        </div>

        {answer && (
          <div style={{ marginTop: 14 }}>
            <div style={{ background: "#0d1117", border: "1px solid #30363d", borderRadius: 8, padding: 14 }}>
              {answer.answer}
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10 }}>
              {Object.entries(answer.scores).map(([k, v]) => (
                <span key={k} style={{ fontSize: 12, color: "#8b949e", border: "1px solid #30363d", borderRadius: 6, padding: "3px 8px" }}>
                  {k}: <b style={{ color: v >= 0.7 ? "#4ec9b0" : v >= 0.4 ? "#ffb454" : "#ff7b72" }}>{v}</b>
                </span>
              ))}
            </div>
            <div style={{ marginTop: 12 }}>
              {answer.contexts.map((c) => (
                <div key={c.id} style={{ fontSize: 13, color: "#8b949e", padding: "6px 0", borderTop: "1px solid #21262d" }}>
                  <b style={{ color: "#58a6ff" }}>{c.id}</b> · {c.score}
                  <div style={{ color: "#c9d1d9" }}>{c.text}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

function btn(bg: string): React.CSSProperties {
  return {
    padding: "8px 14px",
    background: bg,
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 14,
  };
}
