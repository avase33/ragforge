import math

from ragforge_engine.embeddings import HashingEmbedder, cosine
from ragforge_engine.engine import Engine
from ragforge_engine.evaluate import evaluate
from ragforge_engine.store import VectorStore


def test_embedding_is_deterministic_and_normalized():
    e = HashingEmbedder(256)
    a = e.embed("database index query performance")
    b = e.embed("database index query performance")
    assert a == b
    assert abs(math.sqrt(sum(x * x for x in a)) - 1.0) < 1e-6


def test_embedding_similarity_reflects_content():
    e = HashingEmbedder(256)
    same = cosine(e.embed("database index query"), e.embed("database index query"))
    diff = cosine(e.embed("database index query"), e.embed("cats dogs kittens"))
    assert same > 0.99
    # unrelated text shares no terms; at most a rare single hash collision
    assert diff < 0.5
    assert same > diff + 0.4


def test_store_search_delete():
    e = HashingEmbedder(128)
    s = VectorStore()
    s.upsert("d1", 0, "databases store structured data", e.embed("databases store structured data"))
    s.upsert("d2", 0, "cats are wonderful pets", e.embed("cats are wonderful pets"))
    hits = s.search(e.embed("structured database storage"), 1)
    assert hits[0][0].doc_id == "d1"
    assert s.delete_doc("d1") == 1
    assert len(s) == 1


def test_evaluate_metrics_known_values():
    scores = evaluate("question about cats", "cats are nice. dogs bark.", ["cats are nice pets"])
    assert scores["context_precision"] == 1.0
    assert scores["context_recall"] == 0.5
    assert scores["faithfulness"] == 0.5
    assert scores["answer_relevance"] == 0.5


def test_engine_query_finds_right_doc():
    eng = Engine().seed()
    res = eng.query("how do I request time off?")
    assert res["contexts"][0]["id"].startswith("hr/pto")
    ans = res["answer"].lower()
    assert "portal" in ans and "leave" in ans
    assert res["scores"]["faithfulness"] >= 0.5


def test_eval_suite_answers_hit():
    report = Engine().seed().eval_suite()
    assert report["answer_hit_rate"] >= 0.6
    assert report["mean_scores"]["context_precision"] > 0.0
