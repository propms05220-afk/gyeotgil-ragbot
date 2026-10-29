"""The core must not know which chatbot it is. Domain words belong in config.yaml and src/ragbot/domain/.

If this fails, move the string into config.yaml (wording) or the domain package (logic), so the next
project can reuse the core by replacing only config.yaml, domain/, data/ and eval/.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = [p for p in (ROOT / "src" / "ragbot").rglob("*.py") if "domain" not in p.relative_to(ROOT / "src").parts]
CORE += list((ROOT / "app").glob("*.py"))
# 앞의 단어들은 원본 예시 프로젝트의 것, 뒤의 단어들은 이 챗봇(가족돌봄청년 지원제도)의 것입니다.
DOMAIN_TERMS = ["CBNU", "Chungbuk", "충북", "guidebook", "course", "TOPIK", "visa", "hikorea", "❒", "학사", "외국인",
                "자기돌봄비", "가족돌봄", "위기아동", "청년미래센터", "보도자료", "약칭", "제1조"]


def test_core_has_no_domain_terms():
    hits = []
    for path in CORE:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for term in DOMAIN_TERMS:
                if term.lower() in line.lower():
                    hits.append(f"{path.relative_to(ROOT)}:{n}: '{term}' in {line.strip()[:80]}")
    assert not hits, "Domain wording in core code:\n" + "\n".join(hits)
