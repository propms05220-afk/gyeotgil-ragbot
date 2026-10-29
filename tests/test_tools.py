"""Tool registry and pure tools (no API)."""
import pytest

from ragbot.config import load_config
from ragbot.tools import TOOLS, load_all, spec
from ragbot.tools.core import calculator

load_all()
CFG = load_config()


def test_every_configured_tool_is_registered():
    assert set(CFG["agent"]["tools"]) <= set(TOOLS)


def test_every_source_tool_is_enabled():
    for name, card in CFG["sources"].items():
        assert set(card["tools"]) <= set(CFG["agent"]["tools"]), f"source {name} lists a tool not in agent.tools"


@pytest.mark.parametrize("name", sorted(TOOLS))
def test_tool_spec_shape(name):
    s = spec(name, CFG)
    assert s["name"] == name and len(s["description"]) > 40
    params = s["parameters"]
    assert params["type"] == "object" and set(params["required"]) <= set(params["properties"])
    assert all("description" in p or "enum" in p for p in params["properties"].values())


def test_document_tool_describes_configured_documents():
    assert CFG["documents"]["description"].strip() in spec("search_documents", CFG)["description"]


def test_calculator():
    assert calculator(None, "(3*3 + 2*2) / 2")["result"] == 6.5


def test_calculator_rejects_code():
    with pytest.raises(ValueError):
        calculator(None, "__import__('os')")
