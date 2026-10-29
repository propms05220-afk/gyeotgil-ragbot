# 0004 — Send back answers given without any tool call

**Status:** accepted · 2026-10-28

## Context
First full eval (runs/eval_20261028_123207.json): accuracy 0.50, route_accuracy 0.39, guidebook 0.25.
Traces showed that on guidebook questions qwen3-14b **called no tool at all**: it answered from memory and
invented citations (G02: "2.0 … [Source: guidebook ko p.24]"; the guidebook says 1.75 and has 21 pages).
Course questions worked because the prompt said "use ONLY these tools" for courses.

## Decision
1. System prompt: the model is told it does not know CBNU facts, must call a tool first, and may cite only
   sources a tool returned.
2. Harness guardrail in `agent.py`: if the model's first reply contains no tool call, it is sent back once
   with `NUDGE` ("call the right tool now; if it was only small talk, answer normally"). Small talk still
   gets a tool-free answer on the second try.
3. `search_courses` results start with a `summary` line stating the total count, because the model counted
   listed rows (15) instead of `total_matches` (58).

## Result
| run | accuracy | route_accuracy | guidebook | courses |
|---|---|---|---|---|
| before (123207) | 0.50 | 0.39 | 0.25 | 0.78 |
| after (123554) | 0.93 | 0.96 | 0.88 | 1.00 |

## Consequences
- One extra LLM call on small talk.
- The guardrail checks only that *a* tool was used, not that the answer is supported by it. Fabrication after
  a tool call still happens (see tasks/04 known failures, W01).
