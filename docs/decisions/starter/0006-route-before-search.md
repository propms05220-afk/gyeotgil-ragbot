# 0006 — Decide the source before searching (router + source cards)

**Status:** accepted · 2026-10-28 · supersedes the fixed "guidebook first" priority

## Context
The agent always searched the guidebook first. Questions the guidebook can't answer by design paid for it:
"How many departments does CBNU have?" → one guidebook search, a hit on the phone-directory section
(which lists offices, not departments), then "not directly listed… contact the Support Center".
The answer was on the web all along. Feedback from the project owner: identify the route first.

## Decision
1. **Source cards** in `config.yaml → sources`: per source, the tools, what it `covers` and what it
   does `not_covers`. The guidebook card gets its section *and subsection* titles from the index automatically
   (section titles alone, e.g. "2 학사 안내", were too vague: probation questions were routed to `none`).
2. **Router** (`src/ragbot/router.py`): one LLM call → `{"primary", "fallback", "reason"}`. Stored as
   `Answer.plan` and in the trace. `router.enabled: false` restores the old behaviour.
3. **The plan orders, it never removes.** The agent gets all tools, primary first; the plan is in the system prompt.
4. **Guardrail 2 generalised:** before a "not found" answer, every source not yet tried is searched, in plan
   order. A wrong route is recovered from; a right route that lacks the answer falls through to the next source.
5. Guardrail 1 (no tool call) stays on even for `none`, because the router sometimes labels real questions as small talk.
6. The answer language is detected from the question's script and stated in the prompt (short Korean
   questions got English answers).
7. `ddgs` web search retries and walks down official sites → cbnu.ac.kr → open web; empty results are not cached.

## Result (29 scored questions + 2 "any")
| run | accuracy | route_acc | router_acc | guidebook | web |
|---|---|---|---|---|---|
| before router (133423) | 0.93 | 0.97 | — | 0.88 | 1.00 |
| router, tools restricted to plan (135046) | 0.84 | 0.87 | 0.83 | 0.71 | 1.00 |
| router, full section map, all tools (135415) | 0.90 | 0.90 | 0.90 | 0.79 | 1.00 |
| + try untried sources before "not found" (140001) | **0.97** | 0.97 | 0.90 | 0.93 | 1.00 |

The restricted-tools run is kept as a lesson: a router that removes sources turns every routing mistake into a wrong answer.

## Consequences
- One extra LLM call per question (router), plus up to one retry when a source lacks the answer.
- Router accuracy (0.90) is now its own metric; misroutes still cost latency, so improving the cards pays off.
- Students adapting the project to their data mainly rewrite the source cards.
