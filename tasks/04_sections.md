# 04 — 섹션 규칙과 청크

**상태:** 진행 중 · 2026-10-29 (골든 QA 가 생기면 마지막 항목 확인)

## 목표
모든 청크가 그 자체로 의미가 통하도록, 문서의 섹션 구조를 올바르게 잡는다 (breadcrumb: "섹션 > 하위 섹션").

## 파일
- `src/ragbot/domain/sections.py`
- `config.yaml → chunking`
- `tests/test_domain.py` (섹션 부분), `tests/test_core_is_domain_free.py` (`DOMAIN_TERMS`)

## 완료 조건
- [x] `python -m ragbot index` 후 `index/chunks.json` 을 열어 path 가 문서의 목차와 맞는지 확인했다
- [x] 기본 규칙이 맞지 않으면 `domain/sections.py` 의 함수를 고쳤고, 그 이유가 `docs/DATA.md` 에 있다
- [x] `tests/test_domain.py` 의 섹션 테스트 2개의 skip 을 지우고, 내 문서의 실제 값으로 채웠다. 통과한다
- [x] `DOMAIN_TERMS` 에 내 도메인의 단어 3개 이상을 추가했다
- [ ] 골든 질문 3개에 대해 `python -m ragbot ask` 를 실행하고, trace 의 `search_documents` 결과에 맞는 문단이 있는지 봤다
  (골든 QA 가 아직 없어 GOAL.md 후보 질문 3개로 대신 실행: 2개는 맞는 조문을 찾음, 1개는 라우터 실패로 웹만 검색 → tasks/06)

## 확인
```
python -m ragbot index
python -m pytest tests/test_domain.py tests/test_ingest.py tests/test_core_is_domain_free.py -q
```
