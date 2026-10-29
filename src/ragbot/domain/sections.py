"""나의 문서가 섹션을 표시하는 방식 (tasks/04). 근거: docs/DATA.md 1절, docs/decisions/0003.

법률·시행령 (law_*, decree_*):
  - kordoc heading 은 맨 위의 법령 이름 하나뿐 → 섹션 = 법령 약칭 ("위기아동청년법", "위기아동청년법 시행령")
  - 조문은 heading 이 아니라 "제11조(자기돌봄비) ① …" 로 시작하는 문단 → 하위 섹션 = "제11조(자기돌봄비)"
  - 장 ("제1장 총칙") 도 하위 섹션으로 끊는다. 본문이 없어 청크는 생기지 않고, 앞 조문에 섞이지만 않게 한다.
보도자료 (mohw_press_*):
  - heading 이 없다. 1행 표 ["광부", "보도자료"] → 섹션 "보도자료", 1행 표 ["붙임1", "", "제목"] → 섹션 "붙임1 제목"
  - "□ (대상자) …" 네모 머리표 → 하위 섹션
  - "< 가족돌봄아동·청년 주요 연계 서비스 >" 같은 꺾쇠 줄은 하위 섹션으로 쓰지 않는다. 대부분 표 하나의 캡션인데,
    섹션은 다음 제목까지 이어지므로 표 뒤의 다른 본문까지 그 캡션 아래로 들어가 버린다 (본문 한 줄로 남긴다).
고시 (notice_*, 2026-10-29 추가):
  - 첫 줄 "보건복지부고시 제2026-61호" → 섹션 (발령문·날짜가 여기에 들어감)
  - "… 고시 제정안" 줄(문단이나 heading) → 섹션 = 고시 이름 ("제정안" 은 뺌), 그 아래 제N조 는 법령과 같은 하위 섹션
  - 기준 중위소득 고시: "2026년 기준 중위소득 및 …" → 섹션, "1. 기준 중위소득" 같은 짧은 번호 제목 문단 → 하위 섹션
잡음:
  - 법령 PDF 로고를 OCR 한 짧은 글자 ("HE i", "L -L F", "모E:"), 보도자료 체계도 그림을 OCR 한 조각 글자
    → 글꼴 정보가 없는(OCR) 문단 중 아주 짧거나, 짧은 줄이 여러 개인 것은 버린다.
  - 보도자료 4쪽 사진 틀이 만든 빈 표 → 버린다.

block 은 data/parsed/*.json 의 블록 하나입니다: {"type": "heading"|"paragraph"|"table"|"list"|"image",
"text", "level", "pageNumber", "style": {"fontName"}, "table": {"rows", "cols", "cells"}, ...}
"""
import re

from ragbot.ingest.sections import SectionRules, clean

_SHORT_NAME = re.compile(r"\(\s*약칭\s*:\s*([^)]+?)\s*\)")
_ARTICLE = re.compile(r"^(제\d+조(?:의\d+)?\([^)]*\))\s*(.*)$", re.S)
_CHAPTER = re.compile(r"^제\d+장\s+\S")
_BOX = re.compile(r"^□\s*\(([^)]{1,20})\)\s*(.*)$", re.S)
_NOTICE_NO = re.compile(r"^보건복지부\s?고시\s?(제\d{4}-\d+호)$")
_NOTICE_NAME = re.compile(r"^(.{4,60}고시)\s*제정안$")
_MEDIAN_TITLE = re.compile(r"^\d{4}년 기준 중위소득 및 .{4,40}$")
_NUMBERED_TITLE = re.compile(r"^\d\.\s+[^.]{2,28}$")   # "1. 기준 중위소득" (본문 호 "1. … 할 것" 은 더 길거나 마침표로 끝남)


def section_title(block: dict) -> str | None:
    """이 블록이 새 섹션의 제목이면 그 제목을, 아니면 None을 돌려줍니다."""
    if block["type"] in ("heading", "paragraph"):
        text = clean(block.get("text", "")).strip("*").strip()
        m = _NOTICE_NO.match(text)
        if m:
            return f"보건복지부고시 {m.group(1)}"
        m = _NOTICE_NAME.match(text)
        if m:
            return m.group(1)
        if block["type"] == "paragraph" and _MEDIAN_TITLE.match(text):
            return text
    if block["type"] == "heading":
        text = clean(block["text"])
        m = _SHORT_NAME.search(text)
        return m.group(1) if m else text
    if block["type"] == "table" and block["table"]["rows"] == 1:
        cells = [clean(c["text"]) for c in block["table"]["cells"][0]]
        if cells and cells[0].startswith("붙임"):
            return " ".join(c for c in cells if c)
        if "보도자료" in cells:
            return "보도자료"
    return None


def is_subsection(text: str, block: dict) -> bool:
    """이 제목/문단이 하위 섹션을 시작하는지."""
    if block["type"] != "paragraph":
        return False
    return bool(_ARTICLE.match(text) or _CHAPTER.match(text) or _BOX.match(text)
                or (_NUMBERED_TITLE.match(text) and not text.endswith(("것", "다"))))


def split_inline_title(text: str) -> tuple[str, str] | None:
    """"제11조(자기돌봄비) ① 법 …" → ("제11조(자기돌봄비)", "① 법 …"), "□ (대상자) 34세 …" → ("대상자", "34세 …")."""
    for pattern in (_ARTICLE, _BOX):
        m = pattern.match(text)
        if m:
            return m.group(1), m.group(2)
    return None


def is_noise(block: dict) -> bool:
    """빈 표, 그리고 OCR 로 읽힌(글꼴 정보 없는) 문단 중 로고 잔해나 그림 조각 글자."""
    if block["type"] == "table":
        return not any(clean(c["text"]) for row in block["table"]["cells"] for c in row)
    if block["type"] != "paragraph" or (block.get("style") or {}).get("fontName"):
        return False
    text = clean(block.get("text", ""))
    if len(text) <= 6:
        return True
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return len(lines) >= 4 and sum(map(len, lines)) / len(lines) < 10


SECTION_RULES = SectionRules(section_title, is_subsection, split_inline_title, is_noise)
