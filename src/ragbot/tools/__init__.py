"""Tool registry.

Tools live in two places:
  ragbot/tools/core.py     generic tools every chatbot gets: search_documents, web_search, get_today, calculator
  ragbot/domain/tools.py   tools for THIS chatbot's structured data (replace with your own)

To add a tool: write a function with @tool(...) in domain/tools.py, list its name in config.yaml under
agent.tools and under the source it belongs to (sources.<name>.tools), add a unit test and a golden question.

The LLM never sees the code, only name, description and parameters. A description or parameters can be a
function of the config, so generic tools describe the configured data instead of a hard-coded domain.
Each tool returns a dict (or list of dicts) with "source" or "sources": the agent turns those into citations.
"""
from dataclasses import dataclass
from typing import Callable

from ragbot.index import Index

TOOLS: dict[str, dict] = {}   # name → {"fn", "description", "parameters", "required"}


@dataclass
class Context:
    index: Index
    cfg: dict


def tool(name: str, description: str | Callable[[dict], str], parameters: dict | Callable[[dict], dict] | None = None,
         required: list[str] | None = None):
    """parameters, e.g. {"query": {"type": "string", "description": "..."}}"""
    def register(fn):
        TOOLS[name] = {"fn": fn, "description": description, "parameters": parameters or {}, "required": required or []}
        return fn
    return register


def spec(name: str, cfg: dict) -> dict:
    """The tool definition sent to the LLM, with config-dependent parts filled in."""
    t = TOOLS[name]
    desc = t["description"](cfg) if callable(t["description"]) else t["description"]
    params = t["parameters"](cfg) if callable(t["parameters"]) else t["parameters"]
    return {"name": name, "description": " ".join(desc.split()),
            "parameters": {"type": "object", "properties": params, "required": t["required"]}}


def load_all():
    """Register the core and domain tools (imported lazily to keep the import graph acyclic)."""
    import ragbot.domain.tools  # noqa: F401
    import ragbot.tools.core  # noqa: F401
    return TOOLS
