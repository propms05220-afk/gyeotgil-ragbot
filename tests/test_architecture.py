"""Layer rule from docs/ARCHITECTURE.md: a module may import only the ragbot modules listed for it."""
import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "ragbot"
ALLOWED = {
    "config": set(), "schemas": set(),
    "llm": {"config"},
    "ingest": {"config", "schemas", "ingest"},
    "web": {"llm"},
    "chunking": {"schemas"},
    "domain": {"config", "llm", "schemas", "ingest", "tools", "domain"},   # the replaceable plugin package
    "index": {"config", "llm", "schemas", "chunking", "ingest", "domain"},
    "tools": {"index", "web", "schemas", "tools", "domain"},
    "router": {"llm", "index"},
    "agent": {"config", "llm", "index", "schemas", "tools", "router", "domain"},
    "evaluate": {"config", "agent"},
    "cli": None,   # entry point: may import anything
}


def _layer(path: Path) -> str:
    rel = path.relative_to(SRC).parts
    return rel[0] if len(rel) > 1 else path.stem


def test_import_rules():
    violations = []
    for path in SRC.rglob("*.py"):
        layer = _layer(path)
        if layer.startswith("__") or ALLOWED.get(layer, set()) is None:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            mods = []
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("ragbot"):
                parts = node.module.split(".")
                mods = [parts[1]] if len(parts) > 1 else [a.name for a in node.names]
            for m in mods:
                if m != layer and m not in ALLOWED.get(layer, set()):
                    violations.append(f"{path.relative_to(SRC)} imports ragbot.{m}")
    assert not violations, "Layer rule broken (see docs/ARCHITECTURE.md):\n" + "\n".join(violations)
