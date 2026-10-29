"""Parse the documents with kordoc and save the result to data/parsed/ (one .json + one .md per file).

The saved files are the contract with the rest of the pipeline: sections.py reads them, never the PDFs.
Open them when an answer looks wrong — most retrieval bugs are visible there first.

Engine: the kordoc Node engine installed in ./node_modules (npm install), driven by the kordoc Python SDK.
"""
import hashlib
import json
import os
from pathlib import Path

from kordoc import KordocClient, KordocConfig

from ragbot.config import PARSED_DIR, ROOT

PARSER_VERSION = 1   # bump to force re-parsing after changing the options below


def engine_config() -> KordocConfig:
    cli = os.getenv("KORDOC_CLI") or str(ROOT / "node_modules" / "kordoc" / "dist" / "cli.js")
    return KordocConfig(node=os.getenv("KORDOC_NODE", "node"), cli=cli)


def _sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def parse_documents(cfg: dict, progress=print) -> list[Path]:
    """Parse every file listed in config.yaml documents.files. Returns the paths of the parsed .json files."""
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    gb = cfg["documents"]
    out_paths, todo = [], []
    for name, lang in gb["files"].items():
        src = gb["path"] / name
        out = PARSED_DIR / f"{Path(name).stem}.json"
        out_paths.append(out)
        stamp = {"sha1": _sha1(src), "ocr": gb["ocr"], "parser_version": PARSER_VERSION}
        if out.exists() and json.loads(out.read_text(encoding="utf-8")).get("stamp") == stamp:
            progress(f"  {name}: unchanged, skipped")
            continue
        todo.append((src, lang, out, stamp))

    if todo:
        with KordocClient(engine_config()) as client:
            for src, lang, out, stamp in todo:
                progress(f"  {src.name}: parsing{' with OCR' if gb['ocr'] else ''}…")
                r = client.parse(str(src), table_format="gfm", ocr=gb["ocr"])
                r.raise_for_error()
                doc = {"stamp": stamp, "source": src.name, "lang": lang, "metadata": r.metadata,
                       "warnings": r.warnings, "pages": r.pages, "blocks": r.blocks}
                out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
                out.with_suffix(".md").write_text(r.markdown, encoding="utf-8")
                low = sorted({w["page"] for w in r.warnings if w.get("code") == "OCR_LOW_CONF"})
                progress(f"    {len(r.blocks)} blocks, {len(r.pages)} pages"
                         + (f", low-confidence OCR pages: {low}" if low else ""))
    return out_paths


def load_parsed(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
