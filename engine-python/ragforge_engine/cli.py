"""ragforge-engine CLI: `demo`, `eval`, `serve`."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="ragforge-engine")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_demo = sub.add_parser("demo", help="seed docs and answer a question")
    p_demo.add_argument("--question", default="how do I request time off?")
    sub.add_parser("eval", help="seed docs and run the eval suite")
    p_serve = sub.add_parser("serve", help="run the FastAPI engine server")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.cmd == "demo":
        from .engine import Engine

        eng = Engine().seed()
        res = eng.query(args.question)
        print(f"Q: {args.question}\nA: {res['answer']}\n")
        print("contexts:")
        for c in res["contexts"]:
            print(f"  [{c['score']:.3f}] {c['id']}")
        print(f"\nscores: {res['scores']}")
        return 0

    if args.cmd == "eval":
        from .engine import Engine

        report = Engine().seed().eval_suite()
        print(f"answer hit-rate: {report['answer_hit_rate']}")
        print(f"mean scores:     {report['mean_scores']}")
        return 0

    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("ragforge_engine.service:app", host=args.host, port=args.port)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
