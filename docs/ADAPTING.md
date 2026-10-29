# 무엇을 유지하고, 무엇을 바꾸는가

이 템플릿은 범용 RAG 에이전트입니다. CBNU 유학생 도우미(`rag_chatbot_starter`)는 그 한 가지 설정이었고,
여러분의 챗봇은 또 하나의 설정입니다. 아래 표의 🔁 와 ✏️ 만 바꾸고 ✅ 는 그대로 둡니다.
단계별 순서는 `tasks/` 의 카드(00 → 08)를 따르세요.

```
my-agent/
├── AGENTS.md  CLAUDE.md  README.md        ✏️ 수정    명령어는 유지; 목표, 데이터 사실, 디버깅 지도를 채움 (tasks/07)
├── docs/
│   ├── GOAL.md  DATA.md                   🔁 작성    나의 사용자·목표·범위 밖; 나의 데이터의 사실과 빈틈
│   ├── ARCHITECTURE.md  EVAL.md  ADAPTING.md  ✅ 유지
│   └── decisions/                         🔁 새로 시작 (0001 = 나의 데이터/파서 선택); starter/ 는 코어 결정 참고용
├── tasks/                                 ✏️ 수정    같은 단계, 나의 완료 조건
├── config.yaml                            🔁 작성    페르소나, 프롬프트, 소스 카드, 문서, 표, 웹, 도구
├── data/                                  🔁 작성    나의 문서(docs/)와 표(tables/) (data/parsed/ 는 생성됨)
├── src/ragbot/
│   ├── domain/                            🔁 작성    sections.py · tables.py · queries.py · tools.py
│   └── (나머지 전부)                       ✅ 유지    범용 코어
├── app/                                   ✅ 유지    문구와 예시는 config.yaml 에서
├── eval/golden_qa.jsonl                   🔁 작성    나의 질문, 참고 답변, 근거
├── eval/thresholds.yaml                   ✏️ 수정    나의 목표와 소스 이름
└── tests/
    ├── test_domain.py                     🔁 작성    나의 섹션 규칙과 표에 대한 테스트
    └── (나머지)                            ✅ 유지    아키텍처, 평가, 도구, kordoc 계약, 도메인 없는 코어
```

## 건드리지 않아도 되는 것

라우터, 에이전트 루프와 가드레일, 검색, 웹 검색, 평가, 앱은 범용입니다. 그 안에 내 도메인의 단어를 넣고 싶어진다면
대신 `config.yaml` 에 넣으세요. `tests/test_core_is_domain_free.py` 가 알려 줍니다
(`DOMAIN_TERMS` 목록에 내 도메인의 단어를 추가하세요).

코어를 꼭 바꿔야 한다면(예: 지원 언어 추가는 `index.detect_lang` 과 `agent.LANG_NAMES`) 결정 기록을 남기세요.

## 세 가지 소스 유형은 대부분의 챗봇에 들어맞는다

| 챗봇 | 문서 | 표 | 웹 |
|---|---|---|---|
| CBNU 유학생 도우미 (예시) | 안내책자 | 개설 강좌 목록 | cbnu.ac.kr, hikorea.go.kr |
| 인사 도우미 | 사내 규정집 | 휴가 잔여일, 조직도 | 고용노동부 |
| 병원 안내 | 환자 안내문 | 진료 일정, 진료과 | 건강보험 사이트 |
| 제품 지원 | 매뉴얼, FAQ | 제품 카탈로그, 가격 | 릴리스 노트 |
| 도서관 도우미 | 이용 안내 | 도서 목록, 운영 시간 | 도서관 홈페이지 |

표가 없는 챗봇도 괜찮습니다. 문서 + 웹 두 소스로 시작하세요 (템플릿의 기본 상태).
