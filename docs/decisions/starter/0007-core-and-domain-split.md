# 0007 — Split the code into a generic core and a replaceable domain package

**Status:** accepted · 2026-10-28

## Context
The project is meant as a template for students' own chatbots, but CBNU details were spread through the core:
tool descriptions (`search_guidebook` listed CBNU topics), the router prompt ("CBNU international student
helper"), guardrail messages ("…CBNU, courses, visas…", "'충북대학교'"), the citation label, the `courses/`
package and config key, the web fallback domain, and the app's badges and example questions.

## Decision
- `src/ragbot/domain/` holds everything specific to this chatbot: `sections.py` (guidebook section rules),
  `tables.py` + `queries.py` (course list → SQLite, filters), `tools.py` (`search_courses`, `get_course`).
  The core calls only `SECTION_RULES`, `build_tables`, `tables_ready`, and the tools registered there.
- `ingest/sections.py` became a generic builder with pluggable `SectionRules` (defaults: kordoc headings).
- `tools.py` became `tools/` (registry + `core.py`). Generic tool descriptions are built from config
  (`documents.description/use_for/not_for`, `web.official_domains`). `search_guidebook` → `search_documents`.
- Config keys: `guidebooks` → `documents` (`editions` → `files`, plus `citation`, `authoritative`, `outline_langs`,
  `description`, `use_for`, `not_for`); `courses` → `tables`; new `chatbot.purpose/about/examples`,
  `router.default_route`, `agent.search_hint`, `sources.*.label`; `{guidebook_sections}` → `{document_outline}`.
- CLI: `ragbot courses` → `ragbot tables`. A tool's route now comes from the source card that lists it.
- `tests/test_core_is_domain_free.py` keeps domain words out of core and app code.

## Result
| run | accuracy | route_acc | router_acc |
|---|---|---|---|
| before split (143055) | 0.935 | 0.968 | 0.897 |
| first run after split (160512) | 0.839 | 0.968 | 0.931 |
| after fixes below (161834) | **0.935** | **1.000** | 0.931 |

The first run exposed two problems. One came from the split: the reworded no-tool nudge made the model reply to
the check itself (X01). The other was an existing gap the split exposed: "does not specify", "no specific mention"
and "…제공되지 않습니다" were not recognised as "not found", so the try-other-sources guardrail did not fire (G04),
and a correct refusal was graded wrong (N02). Both fixes are general (nudge wording; not-found phrases, with tests).
X01's grading key gained "Chungbuk" because a correct greeting said "Chungbuk National University" instead of "CBNU".

## Consequences
- A new chatbot replaces `config.yaml`, `domain/`, `data/`, `eval/golden_qa.jsonl` and the GOAL/DATA docs
  (`docs/ADAPTING.md`); the core, app and harness stay.
- Renaming the tool changed every prompt, so the model-call cache was cold for one run.
