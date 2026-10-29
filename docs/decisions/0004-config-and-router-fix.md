# 0004 — config.yaml 채움 (챗봇, 소스 카드, 웹 공식 도메인); 라우터 실패 원인 수정

**상태:** 채택 · 2026-10-29 · 기준 점수(baseline)는 **아직 없음** (골든 QA 미작성, tasks/03)

## 배경
`python -m ragbot ask` 를 3개 질문으로 실행하니 라우터가 매번 `router failed (ValueError)` 였다.
라우터 LLM(qwen3-14b)의 원문 응답:
`{"primary": "붙임2 위기아동‧청년 지원 제도 개요", ...}` — 소스 이름 `docs` 대신 **문서 목차의 섹션 이름**을 골랐다.
`docs` 카드의 covers 가 TODO 문장 + 목차뿐이라, 목차 항목이 선택지처럼 보였다.
웹 검색은 `official_domains: example.com` 이라 엉뚱한 결과(example.com)를 돌려줬다.

## 결정
`config.yaml` 의 TODO 를 모두 채웠다 (`grep -n TODO config.yaml` → 없음).
- `chatbot`: 이름 "곁길 지원제도 안내", 목적, 소개, 예시 질문 2개(GOAL.md 후보 질문과 겹치지 않게), 인사말.
- `system_prompt`: 템플릿 일반 규칙 + docs/GOAL.md 의 규칙 — 도구 먼저, 조건과 단서("다만")를 끝까지 적용,
  자격은 최종 판정하지 않음(센터·시군구청이 결정), 출처에 조문 표기, 지역 사업 섞지 않기, 모르면 129·센터·시군구청,
  위기 신호에는 109 먼저. 특정 평가 질문의 답은 넣지 않았다.
- `sources.docs.covers`: 문서 이름·날짜·주제를 쓰고 **"아래 섹션 제목은 docs 의 일부이지 별도 소스가 아니다"** 를 명시.
  `not_covers`: DATA.md 4절 빈틈 (서류, 중위소득 금액, 고시 세부 기준, 센터 연락처, 지역 사업, 학교 학사, 일자리).
- `sources.web.covers`, `documents.description/use_for/not_for`, `web.official_domains`
  (law.go.kr, mohw.go.kr, korea.kr, bokjiro.go.kr).

## 결과
| | 전 | 후 |
|---|---|---|
| 라우터 (질문 3개 + 연락처 질문 + 인사) | 5/5 ValueError | 0 실패: 정책 질문 → docs, 센터 전화번호 → web, 인사 → none |
| 답 (ask 3개, 사람이 판정) | 1/3 맞음 (Q3 은 웹만 검색) | 1/3 맞음 (3개 모두 docs 에서 맞는 조문을 찾음) |
| accuracy / route_accuracy / router_accuracy / by_route / by_lang | 측정 불가 | 측정 불가 — `eval/golden_qa.jsonl` 이 비어 있음 |

틀린 2개는 검색이 아니라 **답 생성**의 문제다 (trace 에 맞는 조문이 있음):
- 군 복무 후 35세: 시행령 제11조 ① 1호 단서(병역 기간 가산)를 적용하지 않고 "대상 아님" 이라고 답함.
- 38세 형과 동거: 법 제13조 ① 1호 나목(35세 이상 다른 가족 구성원 없을 것)을 쓰지 않고 시행령 제11조만 인용.
→ tasks/08 에서 골든 QA 로 측정한 뒤 다룬다 (프롬프트·검색 개수·모델 중 무엇이 원인인지).

## 대안
- 라우터 프롬프트(코어 `router.py`)에 "소스 이름만 고르라" 를 추가: 소스 카드를 고치는 것으로 해결되어 코어는 두었다.
- 시스템 프롬프트에 "병역 기간이면 나이 상한을 늘려라" 같은 규칙: 특정 질문 전용 규칙이라 금지 (AGENTS.md 경계).
