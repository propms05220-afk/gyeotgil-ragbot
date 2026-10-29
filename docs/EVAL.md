# Evaluation

> 참고: 이 문서는 원본 예시 프로젝트(CBNU 유학생 도우미) 기준으로 쓰여 있어 `guidebook`, `courses`, `search_courses` 같은 이름이 나옵니다. 여러분의 프로젝트에서는 `config.yaml` 의 소스 이름과 `domain/tools.py` 의 도구 이름으로 바꿔 읽으세요.

`python -m ragbot eval` runs every question in `eval/golden_qa.jsonl` through the agent and saves
`runs/eval_<timestamp>.json` (per-question answer, tools used, trace id, and the metrics).

The same runs can be started, inspected and compared in the app's **Evaluation** page
(`streamlit run app/streamlit_app.py` → 📊 Evaluation): browse the golden QA, run all or some questions,
see the reference answer next to the bot's answer with a key-point checklist, and diff two runs (fixed / broke).

## Golden QA format (one JSON object per line)

```json
{"id": "C03", "lang": "ko", "route": "courses",
 "question": "회로실험 I (5108004) 수강정원과 현재 수강인원은 몇 명인가요?",
 "reference_answer": "수강정원 30명, 수강인원 28명.", "evidence": "course list · 5108004",
 "key_points": ["30", "28"]}
```

| Field | Meaning |
|---|---|
| `reference_answer` | the correct answer, written and checked by a person (shown for comparison; not used for grading) |
| `evidence` | where it comes from: edition + page, course code, or website rule. Required, so every answer is checkable |

| Field | Meaning |
|---|---|
| `route` | source that should hold the answer: `guidebook`, `courses`, `web`, `none` (small talk), or `any` (not scored, e.g. unanswerable) |
| `lang` | language of the question; the answer should be in the same language |
| `key_points` | all must appear in the answer (ignoring spaces, commas, case) |
| `any_of` | at least one must appear (for several valid spellings) |
| `must_not` | none may appear: catches known fabrications (W01: a D-10 visa needs no "job offer") |
| `unanswerable` | `true` = correct only if the bot says it could not find the answer |

## Metrics

| Metric | Definition |
|---|---|
| `accuracy` | share of questions where the answer passes `key_points` / `any_of` / `unanswerable` |
| `route_accuracy` | share where the expected route is among the routes the agent used (`none` = used no source) |
| `router_accuracy` | share where the router's **planned** primary source equals the expected route. Low router accuracy with high accuracy = right answers, but slowly (wrong source tried first) |
| `by_route`, `by_lang` | accuracy per group, to show where it fails |

`eval/thresholds.yaml` sets the minimums; `ragbot eval` exits 1 below them, and `ragbot check` includes it.

## Rules

- Questions are checked against the data by hand before being added. Write the source (edition and page, or
  course code) in the commit message.
- Never weaken a question or threshold to make a run pass. If a question is wrong, fix it and say why.
- `web` questions: content changes over time, so they check the route and a stable fact only.
- Keyword grading is crude: a correct answer can fail on a different spelling, and a wrong one can pass.
  When a result surprises you, read the answer and trace before changing code.
- API responses are cached in `.cache/`, so re-running gives identical answers. Delete `.cache/chat_*` to
  measure run-to-run variation of the model.
