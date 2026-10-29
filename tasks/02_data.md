# 02 — 데이터 넣고 직접 읽기

**상태:** 완료 · 2026-10-29 (사람 검토 필요: DATA.md 내용, 자료 선택)

## 목표
문서를 kordoc 으로 파싱하고, 파싱 결과를 **직접 읽어서** 데이터의 사실과 빈틈을 기록한다.

## 파일
- `data/docs/`, `data/tables/` (원본. 넣은 뒤로는 읽기 전용)
- `config.yaml → documents` (`files`, `citation`, `authoritative`, `outline_langs`)
- `docs/DATA.md`
- `docs/decisions/0001-….md`

## 완료 조건
- [x] 문서를 `data/docs/` 에 넣고 `config.yaml → documents.files` 에 파일 이름과 언어를 적었다
- [x] `python -m ragbot ingest` 성공, `data/parsed/` 에 파일마다 .json 과 .md 가 있다
- [x] `data/parsed/*.md` 를 처음부터 끝까지 읽었다. 섹션이 어떻게 표시되는지, 사라진 글자·깨진 표·이미지 페이지가 있는지
- [x] `docs/DATA.md` 의 1–4절을 채웠다 (특히 4절: 데이터가 답하지 못하는 것)
- [x] `docs/decisions/0002-data-sources-and-ocr.md`: 어떤 자료를 왜 골랐는지, 파싱 옵션(OCR 등)
  (0001 은 kordoc 계약 테스트 변경 기록)

## 확인
```
python -m ragbot ingest
python -m pytest tests/test_kordoc_contract.py -q
```
