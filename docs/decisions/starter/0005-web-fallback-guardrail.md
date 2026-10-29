# 0005 — Try the web before answering "not found"

**Status:** accepted · 2026-10-28

## Context
User report: "경영정보학과 전화번호" got "not directly listed in the guidebook… contact the Support Center",
in English. The trace showed one `search_guidebook` call and no `web_search`, although the system prompt says
to try the web first. The guidebook's phone directory (section 6) lists offices only, not departments, so the
guidebook really can't answer. The official CBNU phone directory is on the web.

## Decision
- `agent.ABSTAIN` (shared with `evaluate.py`) detects "not found" phrasing in en/ko/zh. It deliberately does
  not match a bare "할 수 없습니다", because correct answers say that too ("you cannot work more than…").
- Guardrail 2 in `agent.py`: if the model is about to give a "not found" answer, `web_search` is enabled, and it
  hasn't been called, the model is sent back once with `WEB_NUDGE`.
- New eval question W03 (the reported question).

## Result
W03 now calls `web_search` and answers in Korean with a URL. N01 (Wi-Fi password) now links the official
Wi-Fi guide instead of a bare "not found". Overall accuracy unchanged within noise; check passes.

## Limits
- `web_search` returns snippets only. The department's number is not in any snippet, so the answer offers a
  related office's number instead of linking the official phone directory. Next step: fetch the text of the top
  official result pages (task 04).
- Confident fabrication (W01) doesn't trigger this guardrail; it needs a grounding check.
