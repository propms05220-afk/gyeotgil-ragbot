"""Command line:  python -m ragbot <command>

  ingest   parse the documents with kordoc → data/parsed/
  tables   structured data → database (domain hook: ragbot/domain/tables.py)
  index    data/parsed/ → index/ (chunks + embeddings)
  build    ingest + tables + index
  ask      answer one question, print tool calls and sources
  eval     run eval/golden_qa.jsonl, print metrics, save runs/eval_*.json, exit 1 if below thresholds
  check    the definition of done: unit tests (+ eval gate unless --fast)
"""
import argparse
import json
import subprocess
import sys

from ragbot.config import load_config


def cmd_ingest(_):
    from ragbot.ingest.kordoc_parser import parse_documents
    print("Parsing documents…")
    parse_documents(load_config())


def cmd_tables(_):
    from ragbot import domain
    print("Building tables…")
    domain.build_tables(load_config())


def cmd_index(_):
    from ragbot.index import build_index
    print("Building document index…")
    m = build_index(load_config()).manifest
    print(f"  done: {m['n_chunks']} chunks {m['by_lang']}")


def cmd_build(args):
    cmd_ingest(args)
    cmd_tables(args)
    cmd_index(args)


def cmd_ask(args):
    from ragbot.agent import Chatbot
    ans = Chatbot().answer(" ".join(args.question))
    if ans.plan:
        print(f"🧭 plan: {ans.plan['primary']} → fallback {ans.plan['fallback']} ({ans.plan['reason']})")
    for t in ans.tool_calls:
        print(f"🔧 {t['name']}({json.dumps(t['arguments'], ensure_ascii=False)})")
    print(f"\n{ans.answer}\n\nroutes={ans.routes}  sources={ans.sources}  trace=runs/…/{ans.trace_id}.json")


def cmd_eval(args):
    from ragbot import evaluate
    result = evaluate.run_eval(only_route=args.route)
    path = evaluate.save(result)
    print(f"\naccuracy {result['accuracy']}  route_accuracy {result['route_accuracy']}  "
          f"router_accuracy {result['router_accuracy']}  (n={result['n']})")
    print(f"by_route {result['by_route']}\nby_lang  {result['by_lang']}\nsaved {path}")
    failures = [] if args.route else evaluate.gate(result)
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


def cmd_check(args):
    marker = ["-m", "not api"] if args.fast else []
    code = subprocess.call([sys.executable, "-m", "pytest", "-q", *marker])
    if code or args.fast:
        return code
    return cmd_eval(argparse.Namespace(route=None))


def main(argv=None):
    p = argparse.ArgumentParser(prog="ragbot", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("ingest", "tables", "index", "build"):
        sub.add_parser(name)
    a = sub.add_parser("ask")
    a.add_argument("question", nargs="+")
    e = sub.add_parser("eval")
    e.add_argument("--route", help="run only the questions of one route (a source name in config.yaml, or none)")
    c = sub.add_parser("check")
    c.add_argument("--fast", action="store_true", help="unit tests only (no API calls, no eval)")
    args = p.parse_args(argv)
    sys.exit(globals()[f"cmd_{args.cmd}"](args) or 0)
