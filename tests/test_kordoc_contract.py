"""Contract with the kordoc engine: the fields ingest/sections.py relies on. Rerun after upgrading kordoc."""
import shutil

import pytest

from ragbot.config import load_config

pytestmark = pytest.mark.engine


def test_parse_result_shape():
    if not shutil.which("node"):
        pytest.skip("Node.js not installed")
    from kordoc import KordocClient
    from ragbot.ingest.kordoc_parser import engine_config
    cfg = load_config()
    if not cfg["documents"]["files"]:
        pytest.skip("no documents in config.yaml documents.files yet (tasks/02)")
    # One document rarely has every block type (a law has no tables, a press release no headings),
    # so check the shape per document and the block types across all of them.
    blocks = []
    with KordocClient(engine_config()) as client:
        for name in cfg["documents"]["files"]:
            r = client.parse(str(cfg["documents"]["path"] / name), table_format="gfm")
            assert r.success, name
            assert all("pageNumber" in b for b in r.blocks), name
            assert all({"pageNumber", "markdown"} <= set(p) for p in r.pages), name
            blocks += r.blocks
    assert {"paragraph", "heading", "table"} <= {b["type"] for b in blocks}
    table = next(b for b in blocks if b["type"] == "table")["table"]
    assert {"rows", "cols", "cells"} <= set(table) and "text" in table["cells"][0][0]
