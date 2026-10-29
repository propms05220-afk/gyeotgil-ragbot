"""Evaluation page: the golden QA set, running it, inspecting results, and comparing runs."""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from ragbot import evaluate as ev
from ragbot.config import RUNS_DIR, load_config

BAR = "#2a78d6"   # single-series bar color (dataviz reference palette, slot 1)
ROUTE_LABEL = {**{name: card.get("label", name) for name, card in load_config()["sources"].items()},
               "none": "💬 Small talk", "any": "❓ Not answerable"}

golden = ev.load_questions()
by_id = {q["id"]: q for q in golden}

st.title("📊 Evaluation")
st.markdown(
    "How do we know the chatbot is good? We ask it questions whose **correct answers we already know** "
    "(the *golden QA set*), grade every answer the same way, and compare runs. "
    "Changing a prompt, a chunk size or a tool is only an improvement if these numbers say so.")

with st.expander("How a question is graded"):
    st.markdown("""
| Field in the golden QA | Meaning |
|---|---|
| **reference_answer** | The correct answer, written and checked by a person. Shown for comparison; not used for grading. |
| **evidence** | Where the reference answer comes from: document + page, table row, or website rule. |
| **key_points** | Every one must appear in the bot's answer (spaces, commas and case ignored). |
| **any_of** | At least one must appear: for answers with several valid spellings (“8” or “eight”). |
| **must_not** | None may appear: catches known fabrications, such as a requirement the bot tends to invent. |
| **unanswerable** | Correct only if the bot says it could not find the answer. |
| **route** | The source that should hold the answer. *Route OK* = the bot used it; *Router OK* = it planned it first. |

Keyword grading is crude: a right answer can fail on a different spelling, and a wrong one can pass.
**Always read the failed and surprising answers** before changing code.
""")


# ---------------------------------------------------------------- helpers
def why_of(row: dict) -> dict:
    """Grading explanation; older runs saved before `why` existed are re-graded against the current golden set."""
    if row.get("why"):
        return row["why"]
    item = by_id.get(row["id"])
    return ev.explain(row["answer"], item) if item else {"correct": row["correct"], "reason": "(not in golden set)"}


def group_counts(rows: list[dict], key: str) -> dict:
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def accuracy_chart(acc: dict, counts: dict, title: str):
    df = pd.DataFrame([{"group": ROUTE_LABEL.get(k, k), "accuracy": v, "questions": counts.get(k, 0)}
                       for k, v in acc.items() if v is not None])
    base = alt.Chart(df).encode(
        y=alt.Y("group:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220, ticks=False, domain=False)),
        x=alt.X("accuracy:Q", scale=alt.Scale(domain=[0, 1]), title=None,
                axis=alt.Axis(format="%", tickCount=5, domain=False, ticks=False)))
    bars = base.mark_bar(size=20, cornerRadiusEnd=4, color=BAR).encode(
        tooltip=[alt.Tooltip("group:N", title=title), alt.Tooltip("accuracy:Q", format=".0%"), "questions:Q"])
    labels = base.mark_text(align="left", dx=6, fontSize=13).encode(text=alt.Text("accuracy:Q", format=".0%"))
    return (bars + labels).properties(title=title, height=max(44 * len(df), 120))


def run_label(path: Path) -> str:
    r = ev.load_run(path)
    stamp = path.stem.replace("eval_", "")
    name = f"{stamp[:8]} {stamp[9:11]}:{stamp[11:13]}"
    return f"{name} · {r.get('label') or 'unlabelled'} · n={r['n']} · accuracy {r['accuracy']:.0%}"


def find_trace(trace_id: str) -> Path | None:
    return next(RUNS_DIR.rglob(f"{trace_id}.json"), None) if trace_id else None


tab_gold, tab_run, tab_results, tab_compare = st.tabs(["📚 Golden QA", "▶️ Run evaluation", "🔍 Results",
                                                        "↔️ Compare runs"])

# ---------------------------------------------------------------- golden QA
with tab_gold:
    st.markdown(f"**{len(golden)} questions** with checked answers, in `eval/golden_qa.jsonl`. "
                "Add questions real students ask; never change a reference answer to make a run pass.")
    c1, c2 = st.columns(2)
    routes = c1.multiselect("Source", sorted({q["route"] for q in golden}), format_func=lambda r: ROUTE_LABEL.get(r, r))
    langs = c2.multiselect("Language", sorted({q["lang"] for q in golden}))
    shown = [q for q in golden if (not routes or q["route"] in routes) and (not langs or q["lang"] in langs)]
    st.dataframe(pd.DataFrame([{
        "id": q["id"], "source": ROUTE_LABEL.get(q["route"], q["route"]), "lang": q["lang"], "question": q["question"],
        "reference answer": q.get("reference_answer", ""), "evidence": q.get("evidence", ""),
        "grading": ("unanswerable" if q.get("unanswerable") else
                    " · ".join(filter(None, ["all: " + ", ".join(q["key_points"]) if q.get("key_points") else "",
                                             "one of: " + ", ".join(q["any_of"]) if q.get("any_of") else "",
                                             "not: " + ", ".join(q["must_not"]) if q.get("must_not") else ""])))}
        for q in shown]), hide_index=True, width="stretch",
        column_config={"question": st.column_config.TextColumn(width="large"),
                       "reference answer": st.column_config.TextColumn(width="large")})

# ---------------------------------------------------------------- run
with tab_run:
    st.markdown("Runs the chatbot on the golden questions and grades every answer. "
                "Each question takes several seconds (router + searches + answer); answers are cached, so an "
                "unchanged question repeats instantly.")
    scope = st.radio("Questions", ["All", "One source", "Pick questions"], horizontal=True)
    ids = None
    if scope == "One source":
        route = st.selectbox("Source", sorted({q["route"] for q in golden}), format_func=lambda r: ROUTE_LABEL.get(r, r))
        ids = [q["id"] for q in golden if q["route"] == route]
    elif scope == "Pick questions":
        ids = st.multiselect("Questions", [q["id"] for q in golden],
                             format_func=lambda i: f"{i} · {by_id[i]['question'][:70]}")
    label = st.text_input("Label for this run", placeholder="e.g. chunk size 600, reranker off")
    n = len(ids) if ids is not None else len(golden)
    if st.button(f"Run {n} question(s)", type="primary", disabled=n == 0):
        bar = st.progress(0.0, "Starting…")
        live = st.empty()
        done_rows = []

        def on_row(row, done, total):
            done_rows.append(row)
            bar.progress(done / total, f"{done}/{total}: {row['id']}")
            live.dataframe(pd.DataFrame([{"id": r["id"], "result": "✅" if r["correct"] else "❌",
                                          "why": r["why"]["reason"]} for r in done_rows]),
                           hide_index=True, width="stretch")
        try:
            result = ev.run_eval(ids=ids, progress=lambda *_: None, on_row=on_row)
        except Exception as e:
            st.error(f"{type(e).__name__}: {e}")
            st.stop()
        path = ev.save(result, label)
        st.session_state.selected_run = path.name
        failures = ev.gate(result) if ids is None else []
        st.success(f"Saved {path.name}: accuracy {result['accuracy']:.0%}. Open the **Results** tab.")
        if ids is None:
            if failures:
                st.error("Below the thresholds in eval/thresholds.yaml: " + "; ".join(failures))
            else:
                st.info("Passes the thresholds in eval/thresholds.yaml.")

# ---------------------------------------------------------------- results
runs = ev.list_runs()
with tab_results:
    if not runs:
        st.info("No runs yet. Start one in the **Run evaluation** tab.")
    else:
        names = [p.name for p in runs]
        default = names.index(st.session_state.get("selected_run")) if st.session_state.get("selected_run") in names else 0
        path = runs[st.selectbox("Run", range(len(runs)), index=default, format_func=lambda i: run_label(runs[i]))]
        run = ev.load_run(path)
        rows = run["rows"]

        m = st.columns(4)
        m[0].metric("Answer accuracy", f"{run['accuracy']:.0%}", help="Answers that pass the grading rules")
        m[1].metric("Route accuracy", f"{run['route_accuracy']:.0%}", help="Used the source that holds the answer")
        m[2].metric("Router accuracy", f"{run['router_accuracy']:.0%}" if run.get("router_accuracy") is not None else "—",
                    help="Planned the right source first (fewer wasted searches)")
        m[3].metric("Questions", run["n"])

        c1, c2 = st.columns(2)
        c1.altair_chart(accuracy_chart(run["by_route"], group_counts(rows, "route"), "Accuracy by source"),
                        width="stretch")
        c2.altair_chart(accuracy_chart(run["by_lang"], group_counts(rows, "lang"), "Accuracy by language"),
                        width="stretch")

        only_fail = st.toggle("Show only failed questions")
        table = [{"id": r["id"], "result": "✅" if r["correct"] else "❌",
                  "source": ROUTE_LABEL.get(r["route"], r["route"]), "lang": r["lang"],
                  "planned first": (r.get("plan") or {}).get("primary", "—"),
                  "used": ", ".join(r.get("used_routes") or []) or "—",
                  "route": "✅" if r["route_ok"] else "⚠️", "why": why_of(r)["reason"], "question": r["question"]}
                 for r in rows if not (only_fail and r["correct"])]
        st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch",
                     column_config={"question": st.column_config.TextColumn(width="large"),
                                    "why": st.column_config.TextColumn(width="medium")})

        st.subheader("Inspect one question")
        pick = st.selectbox("Question", [r["id"] for r in rows],
                            format_func=lambda i: f"{i} · {'✅' if next(r for r in rows if r['id'] == i)['correct'] else '❌'}"
                                                  f" · {next(r for r in rows if r['id'] == i)['question'][:80]}")
        row = next(r for r in rows if r["id"] == pick)
        item, why = by_id.get(pick, {}), why_of(row)
        st.markdown(f"**{row['question']}**")
        left, right = st.columns(2)
        with left:
            st.markdown("##### 🥇 Reference answer (golden)")
            st.info(item.get("reference_answer", "(not in the current golden set)"))
            st.caption(f"Evidence: {item.get('evidence', '—')}")
        with right:
            st.markdown("##### 🤖 Chatbot answer")
            (st.success if row["correct"] else st.error)(row["answer"])
            if row.get("sources"):
                st.caption("Sources: " + ", ".join(f"`{s}`" for s in row["sources"][:6]))

        st.markdown("##### Grading")
        lines = [f"{'✅' if k in why.get('found', []) else '❌'} key point **{k}**" for k in item.get("key_points", [])]
        if item.get("any_of"):
            lines.append(f"{'✅' if why.get('any_of_hit') else '❌'} at least one of: "
                         + ", ".join(f"**{k}**" for k in item["any_of"]))
        lines += [f"{'❌ contains' if k in why.get('must_not_hit', []) else '✅ does not contain'} forbidden **{k}**"
                  for k in item.get("must_not", [])]
        if item.get("unanswerable"):
            lines.append(f"{'✅' if why.get('abstained') else '❌'} says it could not find the answer")
        st.markdown("\n".join(f"- {line}" for line in lines) or "-")
        st.caption(f"Verdict: {why.get('reason', '')}")

        st.markdown("##### Routing and tools")
        plan = row.get("plan") or {}
        st.markdown(f"- Expected source: **{ROUTE_LABEL.get(row['route'], row['route'])}**\n"
                    f"- Router planned first: **{plan.get('primary', '—')}**"
                    + (f" — _{plan['reason']}_" if plan.get("reason") else "") + "\n"
                    f"- Sources actually used: **{', '.join(row.get('used_routes') or []) or 'none'}**\n"
                    f"- Tools called: {' → '.join(f'`{t}`' for t in row.get('tools') or []) or 'none'}")
        trace = find_trace(row.get("trace_id"))
        if trace:
            with st.expander(f"Full trace ({trace.relative_to(RUNS_DIR.parent).as_posix()})"):
                st.json(json.loads(trace.read_text(encoding="utf-8"))["answer"]["tool_calls"], expanded=False)

# ---------------------------------------------------------------- compare
with tab_compare:
    if len(runs) < 2:
        st.info("Run the evaluation at least twice to compare.")
    else:
        st.markdown("Pick a **before** and an **after** run. A change is an improvement only if it fixes questions "
                    "without breaking others.")
        c1, c2 = st.columns(2)
        a_i = c1.selectbox("Before", range(len(runs)), index=1, format_func=lambda i: run_label(runs[i]), key="cmp_a")
        b_i = c2.selectbox("After", range(len(runs)), index=0, format_func=lambda i: run_label(runs[i]), key="cmp_b")
        a, b = ev.load_run(runs[a_i]), ev.load_run(runs[b_i])
        ra, rb = {r["id"]: r for r in a["rows"]}, {r["id"]: r for r in b["rows"]}
        shared = [i for i in rb if i in ra]
        sub_a = ev.summarize([ra[i] for i in shared])
        sub_b = ev.summarize([rb[i] for i in shared])
        st.caption(f"Compared on the {len(shared)} questions both runs contain.")

        def delta(key):
            if sub_a[key] is None or sub_b[key] is None:
                return None
            return f"{(sub_b[key] - sub_a[key]) * 100:+.0f} pts"
        m = st.columns(3)
        for col, key, name in zip(m, ["accuracy", "route_accuracy", "router_accuracy"],
                                  ["Answer accuracy", "Route accuracy", "Router accuracy"]):
            col.metric(name, f"{sub_b[key]:.0%}" if sub_b[key] is not None else "—", delta(key))

        fixed = [i for i in shared if not ra[i]["correct"] and rb[i]["correct"]]
        broke = [i for i in shared if ra[i]["correct"] and not rb[i]["correct"]]
        k1, k2 = st.columns(2)
        k1.markdown(f"#### ✅ Fixed ({len(fixed)})")
        for i in fixed:
            k1.markdown(f"- **{i}** {rb[i]['question'][:80]}")
        k2.markdown(f"#### ❌ Broke ({len(broke)})")
        for i in broke:
            k2.markdown(f"- **{i}** {rb[i]['question'][:80]} — _{why_of(rb[i])['reason']}_")
        if not fixed and not broke:
            st.caption("No question changed result between these runs.")
