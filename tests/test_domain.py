"""나의 도메인 테스트: 섹션 규칙(tasks/04)과 표·도구(tasks/05). API 호출 없이 실행됩니다.

처음에는 모두 skip 입니다. 각 작업 카드를 할 때 @pytest.mark.skip 줄을 지우고, 내 데이터에서 직접 확인한
사실로 assert 를 채우세요. 테스트가 "내 데이터에 대한 사실"을 고정해 두어야, 나중에 코딩 에이전트가 규칙을
바꿔도 망가진 것을 바로 알 수 있습니다. 완성된 예시: rag_chatbot_starter/tests/test_ingest.py,
tests/test_domain_tables.py
"""
import json

import pytest

from ragbot.config import PARSED_DIR, load_config
from ragbot.domain import SECTION_RULES
from ragbot.ingest.sections import build_sections

CFG = load_config()


def _sections(stem: str):
    path = PARSED_DIR / f"{stem}.json"
    if not path.exists():
        pytest.skip("data/parsed missing — run: python -m ragbot ingest")
    return build_sections(json.loads(path.read_text(encoding="utf-8")), SECTION_RULES)


# ---------------------------------------------------------------- 섹션 규칙 (tasks/04)
def test_all_top_sections_found():
    titles = {s.path[0] for s in _sections("mohw_press_20260326")}
    assert titles == {"보도자료", "붙임1 「위기아동청년법」 시행에 따라 달라지는 점", "붙임2 위기아동‧청년 지원 제도 개요"}
    # 법률은 법령 약칭 아래에 제1조~제32조가 하위 섹션으로 하나씩
    law = _sections("law_20260326")
    assert {s.path[0] for s in law} == {"위기아동청년법"}
    articles = [s.path[1] for s in law if len(s.path) == 2]
    assert len(articles) == 32 and articles[0] == "제1조(목적)" and articles[-1] == "제32조(과태료)"


def test_one_subsection_has_its_body():
    secs = _sections("decree_20260326")
    sec = next(s for s in secs if s.path == ["위기아동청년법 시행령", "제11조(자기돌봄비)"])
    assert "13세 이상 34세 이하" in sec.text and "이용권" in sec.text and sec.page == 2
    # 다음 조문이 섞이지 않는다
    assert "시설급여" not in sec.text


def test_notice_sections():
    secs = _sections("notice_selfcare_2026-61")
    sec = next(s for s in secs if s.path == ["자기돌봄비 지원 기준 등에 관한 고시", "제3조(자기돌봄비 이용권의 지원횟수 및 지급액)"])
    assert "1회에 한하여 200만원" in sec.text
    median = _sections("notice_median_income_2025-135")
    table = next(s for s in median if s.kind == "table" and s.path[-1] == "1. 기준 중위소득")
    assert "2,564,238" in table.text   # 2026년 1인가구 기준 중위소득 (원/월)


def test_ocr_noise_dropped():
    for stem in ("law_20260326", "decree_20260326"):
        text = "\n".join(s.text for s in _sections(stem))
        assert "HE i" not in text and "L -L F" not in text and "모E:" not in text
    assert all(s.text.strip("|- \n") for s in _sections("mohw_press_20260326"))   # 빈 표 없음


# ---------------------------------------------------------------- 표와 도구 (tasks/05, 선택)
@pytest.mark.skip(reason="TODO(05): 표가 있으면 채우고, 없으면 이 테스트를 지우세요")
def test_table_loads():
    from ragbot.domain.tables import file_path, read_table
    df = read_table(file_path(CFG))
    assert len(df) == 0   # TODO: 실제 행 수
    assert {"TODO_col"} <= set(df.columns)


@pytest.mark.skip(reason="TODO(05): 표가 있으면 채우고, 없으면 이 테스트를 지우세요")
def test_search_finds_a_known_row():
    from ragbot.domain.queries import search_rows
    from ragbot.domain.tables import db_path
    if not db_path(CFG).exists():
        pytest.skip("database missing — run: python -m ragbot tables")
    out = search_rows(db_path(CFG), keyword="TODO 이 표에 확실히 있는 단어")
    assert out["total_matches"] > 0
