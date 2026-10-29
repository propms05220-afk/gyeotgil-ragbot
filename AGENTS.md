# AGENTS.md — TODO 챗봇 이름

이 저장소에서 일하는 코딩 에이전트(Claude Code, Codex, Cursor …)를 위한 지시문입니다.
사람은 README.md 부터 읽으세요.

> 학생에게: 이 파일은 템플릿입니다. 일반 규칙(명령어, 완료 기준, 경계, 아키텍처)은 이미 채워져 있습니다.
> `TODO` 표시된 부분(목표, 데이터 사실, 디버깅 지도)은 뼈대가 돌아간 뒤 `tasks/07_agents_md.md` 에서 채웁니다.
> 실제 명령어와 파일, 실제로 겪은 문제를 적어야 에이전트에게 쓸모가 있기 때문입니다.

## 목표

TODO(07): 한두 문단. 누구의 어떤 질문에, 어떤 소스로, 어떤 방식(출처, 사용자의 언어, 모르면 "찾을 수 없음")으로 답하는지.
질문마다 **라우터가 먼저 답이 있을 소스를 정하고**, 에이전트가 그 소스를 검색하며, "찾을 수 없음" 전에 나머지 소스도 찾아봅니다.

1. **TODO 문서** (비정형): `data/docs/…`
2. **TODO 표** (정형, 선택): `data/tables/…`
3. **웹**: 공식 사이트 우선. 나머지 둘이 다루지 않는 모든 것.

각 소스가 다루는 것과 다루지 않는 것은 `config.yaml → sources` (소스 카드)에 있습니다.
목표, 사용자, 성공 수치, 범위 밖은 `docs/GOAL.md` 에 있습니다. 동작을 바꾸기 전에 읽으세요.

## 명령어

Python 3.11 환경에서 저장소 루트에서 실행합니다.

| 명령 | 하는 일 |
|---|---|
| `python -m ragbot build` | ingest + tables + index (데이터, `chunking`, `tables` 설정 변경 후) |
| `python -m ragbot ingest` | kordoc 이 문서를 파싱 → `data/parsed/*.json` + `*.md` (파일 해시로 캐시) |
| `python -m ragbot tables` | 도메인 hook: 표 → SQLite (표가 없으면 건너뜀) |
| `python -m ragbot index` | `data/parsed/` → `index/` (청크 + bge-m3 임베딩) |
| `python -m ragbot ask "질문"` | 답 하나와 도구 호출, 라우팅, 출처, trace 파일 이름 |
| `python -m ragbot eval [--route R]` | 골든 QA → 지표, `runs/eval_*.json` 저장; `eval/thresholds.yaml` 미달이면 exit 1 |
| `python -m ragbot check --fast` | 단위 테스트만 (API 호출 없음). 코드 변경마다 실행 |
| `python -m ragbot check` | **완료 기준**: 단위 테스트와 평가 기준 |
| `streamlit run app/streamlit_app.py` | 채팅 UI + 📊 평가 페이지 |

## 완료 기준

작업은 다음이 **모두** 성립할 때만 완료입니다:
1. `python -m ragbot check` 통과 (테스트와 평가 기준).
2. `tasks/` 의 해당 작업 카드의 완료 조건을 충족하고 체크했다.
3. 새 도구에는 단위 테스트와, 그 도구가 필요한 골든 질문이 하나 이상 있다.
4. 동작이나 데이터 계약을 바꿨다면 `docs/decisions/` 에 짧은 기록이 있다.

변경 전후의 평가 수치를 보고하세요 (accuracy, route_accuracy, router_accuracy, by_route, by_lang).

## 경계

**절대 하지 말 것**
- `data/docs/` 와 `data/tables/` 의 원본 파일 수정 (읽기 전용 원본 데이터);
- `docs/GOAL.md` 나 `eval/golden_qa.jsonl` 을 사람 대신 처음부터 작성하기. 비어 있으면 멈추고 사람에게 요청할 것
  (무엇이 정답인지는 사람이 정합니다);
- 실행을 통과시키려고 `eval/` 의 `reference_answer`, 채점 키(`key_points`, `any_of`, `must_not`), `eval/thresholds.yaml` 수정.
  대신 질문을 추가하고, 각 질문에는 데이터에서 직접 확인한 `reference_answer` + `evidence` 를 붙일 것;
- 평가 질문의 답이나 특정 질문 전용 규칙을 프롬프트나 코드에 넣기 (숨겨진 질문으로도 평가합니다);
- LLM이 SQL을 쓰게 하기. 표 질의는 `src/ragbot/domain/queries.py` 의 필터를 거칠 것;
- 도메인 단어를 코어 코드에 넣기. `config.yaml` 이나 `src/ragbot/domain/` 에 둘 것
  (`tests/test_core_is_domain_free.py` 가 검사);
- `.env` 나 API 키를 커밋하거나 출력하기;
- 결정 기록 없이 `src/ragbot/schemas.py` 의 필드 변경.

**먼저 사람에게 물을 것**: 생성된 데이터(`data/parsed/`, `index/`, `.cache/`) 삭제, 의존성 추가,
LLM이나 임베딩 모델 변경, 소스 우선순위 규칙 변경.

## 아키텍처 (자세히: docs/ARCHITECTURE.md)

```
                                    질문 ─▶ 라우터 (소스 카드) ─▶ 계획 {primary, fallback, reason}
                                                                                │
문서 ─kordoc─▶ data/parsed ─sections─▶ chunks ─bge-m3─▶ index/ ─▶ search_documents ─┐   ▼
표 ─load─▶ SQLite ───────────────────────────────────────────────▶ 도메인 도구 ─────┼─▶ 에이전트 ─▶ Answer (+plan)
DuckDuckGo (공식 사이트 우선) ────────────────────────────────────▶ web_search ─────┘
```

에이전트 가드레일 (프롬프트가 아니라 코드): (1) 도구를 하나도 쓰지 않은 답은 한 번 되돌려 보냄;
(2) "찾을 수 없음" 답은 아직 안 찾아본 모든 소스를 계획 순서대로 찾도록 한 번 되돌려 보냄.
계획은 순서만 정하고, 소스를 없애지 않습니다.

코어와 도메인: `src/ragbot/domain/` 은 이 챗봇에만 해당하는 모든 것(섹션 규칙, 표와 그 도구)을,
나머지 `src/ragbot/` 는 범용 코드이며 문구는 `config.yaml` 에서 가져옵니다. `docs/ADAPTING.md` 참고.

층(layer) 규칙, `tests/test_architecture.py` 가 검사: `config, schemas → llm → ingest/web → chunking → domain →
index → tools → router → agent → evaluate → cli/app`. 모듈은 자기 왼쪽 층에서만 import 합니다.

## 일하는 방법

1. `tasks/` 에서 카드 **하나**를 고릅니다 (완료되지 않은 가장 낮은 번호). 작업을 섞지 않습니다.
   01 과 03 은 사람의 작업입니다. 그 카드가 열려 있으면 코드를 바꾸지 말고 사람에게 알리세요.
2. 코드를 바꾸기 전에 문제를 증거로 재현합니다: `python -m ragbot ask` 나 `eval --route …` 를 실행하고 `runs/` 의 trace 를 엽니다.
3. 원인을 고치는 가장 작은 변경을 합니다. 변경마다 `python -m ragbot check --fast`.
4. 평가를 다시 돌리고 마지막 `runs/eval_*.json` 과 비교합니다. 다른 소스의 점수를 떨어뜨린 수정은 완료가 아닙니다.

## 디버깅 지도: 증상 → 볼 곳

| 증상 | 볼 곳 | 흔한 원인 |
|---|---|---|
| 평가 출력에 `⚠router`: 계획이 엉뚱한 소스를 고름 | trace → `answer.plan.reason` | `config.yaml → sources` 소스 카드 (특히 `not_covers`); `router.py` 프롬프트 |
| 소스는 맞지만 느림 (2–3개 소스 검색) | trace → 도구 호출 순서 | 같음: 라우터가 처음에 빗나감; router_accuracy 확인 |
| PDF에는 있는데 검색되지 않음 | `data/parsed/*.md` | 파싱에서 사라짐 (이미지 페이지 → OCR, 표 분리) |
| 검색된 문단에 맥락이 없음 (섹션 이름 없이 "서류: 여권…") | `index/chunks.json` breadcrumb | `domain/sections.py` 의 섹션 규칙 |
| 맞는 문단이 6위 이하 | trace → `search_documents` 결과 | `retrieval` 설정, 질의 표현, 재순위화 |
| 맞는 소스를 찾았지만 도구 인자가 틀림 | trace → 도구 호출 | 도구 설명 (`config.yaml documents.*`, `domain/tools.py`), 시스템 프롬프트 |
| 표의 값이 틀림 | trace → 도메인 도구 결과 | `domain/queries.py` 필터, `domain/tables.py` 파싱; LLM 탓이 아님 |
| 답의 언어가 틀리거나 출처가 없음 | trace 의 마지막 메시지 | `config.yaml` 시스템 프롬프트 |
| 아무것도 못 찾았는데 자신 있게 답함 | trace: 빈 결과, 확신에 찬 답 | 시스템 프롬프트의 기권 규칙; `unanswerable` 평가 질문 추가 |
| TODO(07): 내 프로젝트에서 실제로 겪은 증상 | | |

## 에이전트가 틀리기 쉬운 데이터 사실 (자세히: docs/DATA.md)

- TODO(07): 데이터를 읽으며 발견한, 겉보기와 다른 사실을 적으세요. 예(원본 프로젝트):
  "섹션 제목은 제목이 아니라 1행 표다", "일부 페이지는 이미지라 OCR로 읽었고 `low_confidence` 로 표시된다",
  "표에 학과 열이 없다", "수업시간은 시각이 아니라 교시 번호다".
