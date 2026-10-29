"""Grading rules and the question file (no API)."""
import json

from ragbot.config import load_config
from ragbot.evaluate import QUESTIONS, explain, is_correct, route_ok, router_ok


def test_key_points_ignore_spaces_case_commas():
    assert is_correct("You can work 25 hours per week.", {"key_points": ["25hours"]})
    assert is_correct("신청비는 35,000원입니다", {"key_points": ["35000원"]})


def test_any_of():
    assert is_correct("Room N10 #151", {"key_points": ["N10"], "any_of": ["151", "N10-151"]})


def test_unanswerable():
    assert is_correct("Sorry, I could not find that in the guidebook.", {"unanswerable": True})
    assert not is_correct("It costs 5,000 won.", {"unanswerable": True})


def test_route_ok():
    assert route_ok(["guidebook"], {"route": "guidebook"})
    assert route_ok([], {"route": "none"}) and not route_ok(["web"], {"route": "none"})
    assert route_ok(["web"], {"route": "any"})


def test_router_ok():
    assert router_ok({"primary": "web"}, {"route": "web"}) is True
    assert router_ok({"primary": "guidebook"}, {"route": "web"}) is False
    assert router_ok(None, {"route": "web"}) is None and router_ok({"primary": "web"}, {"route": "any"}) is None


def test_not_found_phrases():
    for text in ["The provided information does not directly list the number of departments.",
                 "경영정보학과의 전화번호는 제공된 자료에서 직접적으로 확인할 수 없습니다.",
                 "The password is not directly provided on the official websites.",
                 "The guidebook does not specify the number of hours.",
                 "There is no specific mention of a required score.",
                 "해당 정보는 공식 웹사이트에서 제공되지 않습니다."]:
        assert is_correct(text, {"unanswerable": True}), text
    # a correct answer that says "cannot" must not count as "not found"
    assert not is_correct("1학년은 TOPIK 3급이 없으면 주 10시간을 초과해 일할 수 없습니다.", {"unanswerable": True})


def test_must_not_catches_fabrication():
    item = {"any_of": ["D-10"], "must_not": ["job offer"]}
    assert is_correct("For a D-10 visa, apply at hikorea.go.kr.", item)
    why = explain("For a D-10 visa you first need a job offer.", item)
    assert not why["correct"] and why["must_not_hit"] == ["job offer"]


def test_explain_lists_missing_key_points():
    why = explain("Capacity is 30.", {"key_points": ["30", "28"]})
    assert why["found"] == ["30"] and why["missing"] == ["28"] and not why["correct"]


def test_golden_file_is_valid():
    rows = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [q["id"] for q in rows]
    routes = {*load_config()["sources"], "none", "any"}
    assert len(ids) == len(set(ids))
    for q in rows:
        assert q.get("reference_answer") and q.get("evidence"), f"{q['id']}: golden QA needs reference_answer and evidence"
        assert q["route"] in routes, f"{q['id']}: route must be a source in config.yaml or none/any"
        assert q["lang"] in {"ko", "en", "zh"}
        assert q.get("key_points") or q.get("any_of") or q.get("unanswerable") or q["route"] == "web"
