"""Load config.yaml and resolve paths relative to the project root."""
import copy
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PARSED_DIR = DATA_DIR / "parsed"
INDEX_DIR = ROOT / "index"
RUNS_DIR = ROOT / "runs"
CACHE_DIR = ROOT / ".cache"


def load_config(path: str | Path = ROOT / "config.yaml") -> dict:
    cfg = copy.deepcopy(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
    cfg["documents"]["path"] = (ROOT / cfg["documents"]["dir"]).resolve()
    cfg["chatbot"]["today"] = str(cfg["chatbot"]["today"] or date.today().isoformat())
    return cfg
