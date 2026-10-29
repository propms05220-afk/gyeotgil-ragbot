# 0001 — kordoc 계약 테스트는 모든 문서를 합쳐서 블록 종류를 확인한다

**상태:** 채택 · 2026-10-29

## 배경
`tests/test_kordoc_contract.py` 는 `config.yaml → documents.files` 의 **첫 문서 하나**만 파싱해서
`paragraph`, `heading`, `table` 블록이 모두 있는지 확인했다. 우리 자료에는 셋을 다 가진 문서가 없다.

| 문서 | heading | table | paragraph |
|---|---|---|---|
| `law_20260326.pdf` (위기아동청년법) | ✅ | ❌ | ✅ |
| `decree_20260326.pdf` (시행령) | ✅ | ❌ | ✅ |
| `mohw_press_20260326.pdf` (보도자료) | ❌ | ✅ | ✅ |

그래서 kordoc 이 정상인데도 `check --fast` 가 실패했다 (어느 문서를 첫 번째로 두어도 실패).

## 결정
`tests/test_kordoc_contract.py` 를 바꿨다.
- 파일마다: 파싱 성공, 모든 블록에 `pageNumber`, 모든 페이지에 `pageNumber`·`markdown` (전과 같은 검사).
- 모든 문서를 합쳐서: `paragraph`, `heading`, `table` 블록이 있는지, 표 블록의 `rows/cols/cells` 구조.

검사 항목은 줄이지 않았고, "한 문서 안에" 라는 가정만 "전체 문서에서" 로 바꿨다.
데이터 계약(`schemas.py`, `data/parsed/` 형식)은 바뀌지 않았다.

## 결과
| | 전 | 후 |
|---|---|---|
| `check --fast` | 23 passed, 1 failed, 4 skipped | 24 passed, 4 skipped |
| 평가 지표 | 아직 없음 (골든 QA 전) | 같음 |

테스트 시간은 문서 3개를 모두 파싱하므로 약 3초 → 10초.

## 대안
- 표가 있는 문서를 첫 번째로 두기: 보도자료는 heading 이 없어 여전히 실패.
- `heading` 이나 `table` 검사 빼기: 계약 검사가 약해져서 하지 않음.
- 테스트용 문서 추가: 원본 데이터가 아닌 파일을 `data/docs/` 에 넣게 되어 하지 않음.
