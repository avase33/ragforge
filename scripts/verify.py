#!/usr/bin/env python3
"""Offline end-to-end verifier for ragforge's engine.

Seeds the built-in corpus, embeds and indexes it, answers a question, and runs
the eval suite — no services, no numpy, no LLM. Exits non-zero on any failure.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine-python"))

PASS, FAIL = 0, 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}")


def main() -> int:
    from ragforge_engine.engine import Engine

    print("ragforge offline verify")
    eng = Engine().seed()
    check("vectors indexed", len(eng.store) > 0)

    res = eng.query("how do I request time off?")
    check("retrieved hr/pto first", res["contexts"][0]["id"].startswith("hr/pto"))
    ans = res["answer"].lower()
    check("answer mentions the HR portal", "portal" in ans)
    check("faithfulness >= 0.5", res["scores"]["faithfulness"] >= 0.5)

    # deletion removes a doc from the index
    before = len(eng.store)
    removed = eng.ingest("hr/pto.md", "delete")
    check("delete removed chunks", removed > 0 and len(eng.store) < before)

    report = Engine().seed().eval_suite()
    check("eval answer hit-rate >= 0.6", report["answer_hit_rate"] >= 0.6)

    print(f"\nRESULT: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
