# Architecture

> 참고: 이 문서는 원본 예시 프로젝트(CBNU 유학생 도우미) 기준으로 쓰여 있어 `guidebook`, `courses`, `search_courses` 같은 이름이 나옵니다. 여러분의 프로젝트에서는 `config.yaml` 의 소스 이름과 `domain/tools.py` 의 도구 이름으로 바꿔 읽으세요.

## Core and domain

The code is split so that a different chatbot reuses the core unchanged:

| Part | What | Changes per chatbot? |
|---|---|---|
| **Core** — `src/ragbot/` except `domain/`, `app/` | parsing, chunking, index, retrieval, web search, router, agent loop, guardrails, evaluation, UI | No. Takes all wording from `config.yaml` |
| **Domain** — `src/ragbot/domain/` | how the documents mark sections; structured data → database; tools over that data | Yes, replace |
| **Configuration** — `config.yaml` | persona, system prompt, source cards, document description, citation label, web domains, tools | Yes, rewrite |
| **Data & truth** — `data/`, `eval/golden_qa.jsonl`, `docs/GOAL.md`, `docs/DATA.md` | the knowledge and the definition of a correct answer | Yes, replace |

`tests/test_core_is_domain_free.py` fails if domain words (CBNU, guidebook, course, …) appear in core code.
How to adapt the template: `docs/ADAPTING.md`.

## Pipeline

```
                    ┌─────────────── offline: python -m ragbot build ───────────────┐
documents (config documents.files) ──kordoc (SDK + Node engine, OCR)──▶ data/parsed/{name}.json + .md
                                     │ ingest/sections.py + domain.SECTION_RULES: section/subsection paths
                                     ▼
                              Section[] ──chunking.py──▶ Chunk[] ──llm.embed (bge-m3)──▶ index/
structured data ──domain.build_tables (here: 2-row header, schedule parsing, name translation)──▶ SQLite
                    └───────────────────────────────────────────────────────────────┘

                    ┌─────────────── online: per question ───────────────┐
question ──▶ router.py (source cards in config.yaml) ──▶ plan {primary, fallback, reason}
         ──▶ agent.py (all tools, primary first; guardrails) ──LLM chooses tools──▶
               tools/core.py    search_documents → index.retrieve (embed → rerank → language bonus)
                                web_search → web.py (official domains first)
                                get_today, calculator
               domain/tools.py  search_courses / get_course → domain/queries.py (parameterised SQL)
         ◀── Answer{answer, sources, routes, tool_calls, plan, trace_id}  + runs/<date>/<trace_id>.json
```

## Modules and the layer rule

A module may import only from layers to its left. `tests/test_architecture.py` fails if this is broken.

| Layer | Modules | May import |
|---|---|---|
| 0 | `config`, `schemas` | — |
| 1 | `llm` | config |
| 2 | `ingest/`, `web` | config, schemas, llm |
| 3 | `chunking` | schemas |
| 4 | `domain/` (plugin) | config, llm, schemas, ingest, tools |
| 5 | `index` | config, llm, schemas, chunking, ingest, domain |
| 6 | `tools/` | index, web, schemas, domain |
| 7 | `router` | llm, index |
| 8 | `agent` | config, llm, index, schemas, tools, router, domain |
| 9 | `evaluate` | config, agent |
| 10 | `cli`, `app/` | anything |

Why: an agent fixing "wrong course time" should only need `domain/`; one fixing retrieval should only need
`chunking`/`index`. Tangled imports make every fix touch everything.

## Contracts

- **kordoc → sections**: `data/parsed/*.json` with `blocks[]` (`type`, `text`, `pageNumber`, `level`, `table.cells`),
  `pages[]`, `warnings[]`. Pinned by `tests/test_kordoc_contract.py`.
- **Domain hooks** (`domain/__init__.py`): `SECTION_RULES`, `build_tables(cfg)`, `tables_ready(cfg)`, and tools
  registered with `@tool` in `domain/tools.py`.
- **Between layers**: dataclasses in `schemas.py` (`Section`, `Chunk`, `Answer`).
- **Tool results** are dicts with `source`/`sources`; the agent turns them into citations, and the source card
  that lists the tool becomes the answer's `route`.
- **Answer** is what the app shows and what `evaluate.py` scores.

## Where to change what

| To change | Edit |
|---|---|
| Which source a question goes to first | `config.yaml` → `sources` (covers / not_covers) |
| Chatbot persona, answer and language rules | `config.yaml` → `chatbot` |
| What the document search tool says it covers | `config.yaml` → `documents.description / use_for / not_for` |
| What happens when a source lacks the answer | guardrails in `agent.py` (decisions 0004–0006) |
| Chunk size / overlap / table handling | `config.yaml` → `chunking`, then `ragbot index` |
| Retrieval depth, reranker, language preference | `config.yaml` → `retrieval` |
| How the documents' structure is detected | `src/ragbot/domain/sections.py` (+ `tests/test_ingest.py`) |
| Structured data loading and filters | `src/ragbot/domain/tables.py`, `queries.py` (+ `tests/test_domain_tables.py`) |
| A new tool | `domain/tools.py` + `config.yaml` (agent.tools, sources) + test + golden question |
| New source documents | `data/…` + `config.yaml documents.files`, then `ragbot build` |
