# 05 — 표와 도메인 도구 (선택)

**상태:** 진행 전 · 표가 없는 챗봇은 "해당 없음"으로 표시하고, `tests/test_domain.py` 의 표 테스트 2개를 지우세요.

## 목표
표 데이터를 SQLite 에 넣고, LLM 이 SQL 을 쓰지 않고도 정확한 값(개수, 가격, 일정 …)을 얻을 수 있는 도구를 만든다.

## 파일
- `src/ragbot/domain/tables.py` (`TABLE`, `COLUMNS`, `read_table`)
- `src/ragbot/domain/queries.py` (`SOURCE`, `SEARCH_COLUMNS`, 필터 함수)
- `src/ragbot/domain/tools.py` (`@tool`)
- `config.yaml → tables`, `sources.<표 소스>`, `agent.tools`
- `tests/test_domain.py` (표 부분)

## 완료 조건
- [ ] `config.yaml` 의 `tables:` 블록과 표 소스 카드의 주석을 풀고 채웠다
- [ ] `python -m ragbot tables` 성공. 행 수가 원본과 같다 (`docs/DATA.md` 에 기록)
- [ ] 골든 QA 의 표 질문마다, 그 질문에 답하는 필터가 `queries.py` 에 있다. 사용자 값은 모두 `?` 로 넘긴다
- [ ] 도구 설명에 "언제 쓰는지"와 "언제 쓰지 않는지"가 있다. 결과에 `source` 와 `total_matches` 가 있다
- [ ] 새 도구마다 단위 테스트와, 그 도구가 필요한 골든 질문이 하나 이상 있다
- [ ] `docs/decisions/` 에 표 처리 결정 (예: 열 정리, 두 줄 머리글, 형식 변환)

## 확인
```
python -m ragbot tables
python -m pytest tests/test_domain.py tests/test_tools.py -q
python -m ragbot eval --route <표 소스 이름>
```
