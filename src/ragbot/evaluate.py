"""Evaluation: run the golden QA set (eval/golden_qa.jsonl) through the agent, score it, gate on eval/thresholds.yaml.

Golden QA fields (one JSON object per line):
  id, question, lang (ko|en|zh), route (a source name from config.yaml, or none | any)
  reference_answer: str   the correct answer, written and checked by a human (shown in the UI; not used for grading)
  evidence:         str   where the reference answer comes from (edition + page, table row, or URL rule)
  key_points: [str]   every item must appear in the answer (case/space/comma-insensitive)
  any_of:     [str]   optional: at least one must appear (for answers with several valid spellings)
  must_not:   [str]   optional: none may appear (catches known fabrications, e.g. a requirement the bot tends to invent)
  unanswerable: bool  optional: correct = the bot says it could not find the answer

Metrics
  accuracy         share of questions answered correctly
  route_accuracy   share where the agent used the expected source family (route "none" = no source needed)
  router_accuracy  share where the router PLANNED the expected source first
  by_route / by_lang  accuracy per group, so you can see WHERE it fails
"""
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

from ragbot.agent import ABSTAIN, Chatbot
from ragbot.config import ROOT, RUNS_DIR

QUESTIONS = ROOT / "eval" / "golden_qa.jsonl"
THRESHOLDS = ROOT / "eval" / "thresholds.yaml"


def _norm(s: str) -> str:
    return re.sub(r"[\s,]", "", s).lower()


def explain(answer: str, item: dict) -> dict:
    """Grade one answer and say why: which key points were found or missing, forbidden phrases, abstaining."""
    a = _norm(answer)
    out = {"found": [k for k in item.get("key_points", []) if _norm(k) in a],
           "missing": [k for k in item.get("key_points", []) if _norm(k) not in a],
           "any_of_hit": [k for k in item.get("any_of", []) if _norm(k) in a],
           "must_not_hit": [k for k in item.get("must_not", []) if _norm(k) in a],
           "abstained": bool(ABSTAIN.search(answer))}
    if item.get("unanswerable"):
        out["correct"] = out["abstained"] and not out["must_not_hit"]
        out["reason"] = "said 'not found' as expected" if out["correct"] else "should have said it could not find it"
        return out
    reasons = []
    if out["missing"]:
        reasons.append(f"missing key point(s): {', '.join(out['missing'])}")
    if item.get("any_of") and not out["any_of_hit"]:
        reasons.append(f"none of: {', '.join(item['any_of'])}")
    if out["must_not_hit"]:
        reasons.append(f"contains forbidden claim(s): {', '.join(out['must_not_hit'])}")
    out["correct"] = not reasons
    out["reason"] = "; ".join(reasons) or "all key points present"
    return out


def is_correct(answer: str, item: dict) -> bool:
    return explain(answer, item)["correct"]


def route_ok(routes: list[str], item: dict) -> bool:
    expected = item.get("route", "none")
    if expected == "any":
        return True
    return not routes if expected == "none" else expected in routes


def router_ok(plan: dict | None, item: dict) -> bool | None:
    """Did the router pick the expected source as primary? None = not scored (router off, or route 'any')."""
    if plan is None or item.get("route") == "any":
        return None
    return plan["primary"] == item.get("route")


def load_questions(path: Path = QUESTIONS) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate_item(bot: Chatbot, item: dict) -> dict:
    ans = bot.answer(item["question"])
    why = explain(ans.answer, item)
    return {"id": item["id"], "question": item["question"], "lang": item.get("lang"), "route": item.get("route"),
            "correct": why["correct"], "why": why, "route_ok": route_ok(ans.routes, item),
            "router_ok": router_ok(ans.plan, item), "plan": ans.plan,
            "used_routes": ans.routes, "answer": ans.answer, "sources": ans.sources,
            "tools": [t["name"] for t in ans.tool_calls], "trace_id": ans.trace_id}


def run_eval(questions_path: Path = QUESTIONS, only_route: str | None = None, ids: list[str] | None = None,
             progress=print, on_row=None) -> dict:
    """Run the golden set (or a subset by route or ids). on_row(row, done, total) is called after each question."""
    bot = Chatbot()
    items = [q for q in load_questions(questions_path)
             if (not only_route or q.get("route") == only_route) and (not ids or q["id"] in ids)]
    rows = []
    for item in items:
        row = evaluate_item(bot, item)
        rows.append(row)
        plan = f" →{row['plan']['primary']}" if row["plan"] else ""
        progress(f"{'✅' if row['correct'] else '❌'}{'' if row['route_ok'] else ' ⚠route'}"
                 f"{' ⚠router' if row['router_ok'] is False else ''} "
                 f"{item['id']:>4} [{item.get('route')}/{item.get('lang')}{plan}] {item['question'][:60]}")
        if on_row:
            on_row(row, len(rows), len(items))
    return summarize(rows)


def summarize(rows: list[dict]) -> dict:
    def acc(rs):
        return round(sum(r["correct"] for r in rs) / len(rs), 3) if rs else None
    groups = {"by_route": defaultdict(list), "by_lang": defaultdict(list)}
    for r in rows:
        groups["by_route"][r["route"]].append(r)
        groups["by_lang"][r["lang"]].append(r)
    routed = [r["router_ok"] for r in rows if r.get("router_ok") is not None]
    return {"n": len(rows), "accuracy": acc(rows),
            "route_accuracy": round(sum(r["route_ok"] for r in rows) / len(rows), 3) if rows else None,
            "router_accuracy": round(sum(routed) / len(routed), 3) if routed else None,
            "by_route": {k: acc(v) for k, v in groups["by_route"].items()},
            "by_lang": {k: acc(v) for k, v in groups["by_lang"].items()},
            "rows": rows}


def save(result: dict, label: str = "") -> Path:
    RUNS_DIR.mkdir(exist_ok=True)
    result = {**result, "label": label, "created": datetime.now().isoformat(timespec="seconds")}
    path = RUNS_DIR / f"eval_{datetime.now():%Y%m%d_%H%M%S}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def list_runs() -> list[Path]:
    """Saved eval runs, newest first."""
    return sorted(RUNS_DIR.glob("eval_*.json"), reverse=True)


def load_run(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def gate(result: dict) -> list[str]:
    """Return the list of failed thresholds (empty = pass)."""
    th = yaml.safe_load(THRESHOLDS.read_text(encoding="utf-8"))
    failures = []
    for key in ("accuracy", "route_accuracy"):
        if result[key] is not None and result[key] < th[key]:
            failures.append(f"{key} {result[key]:.2f} < {th[key]}")
    for route, minimum in (th.get("by_route") or {}).items():
        got = result["by_route"].get(route)
        if got is not None and got < minimum:
            failures.append(f"by_route.{route} {got:.2f} < {minimum}")
    return failures
