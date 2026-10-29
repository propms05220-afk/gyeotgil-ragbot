"""Document vector index: chunks → bge-m3 embeddings → index/ folder; search with optional reranking."""
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ragbot import domain, llm
from ragbot.chunking import chunk_sections
from ragbot.config import INDEX_DIR, PARSED_DIR
from ragbot.ingest.kordoc_parser import load_parsed
from ragbot.ingest.sections import build_sections
from ragbot.schemas import Chunk

LANG_BONUS = 0.05   # added to the score of chunks whose edition matches the question's language


def detect_lang(text: str) -> str:
    if re.search(r"[가-힣]", text):
        return "ko"
    if re.search(r"[一-鿿]", text):
        return "zh"
    return "en"


def _normalize(m):
    m = np.asarray(m, dtype=np.float32)
    return m / np.linalg.norm(m, axis=-1, keepdims=True)


def _parsed_files(cfg: dict):
    return [PARSED_DIR / f"{Path(name).stem}.json" for name in cfg["documents"]["files"]]


def fingerprint(cfg: dict) -> str:
    """Changes whenever parsed data, chunking settings or the embedding model change."""
    stamps = [load_parsed(p)["stamp"] for p in _parsed_files(cfg) if p.exists()]
    payload = json.dumps([stamps, cfg["chunking"], llm.EMBED_MODEL], sort_keys=True)
    return hashlib.sha1(payload.encode()).hexdigest()


class Index:
    def __init__(self, chunks: list[Chunk], vecs: np.ndarray, manifest: dict):
        self.chunks, self.vecs, self.manifest = chunks, vecs, manifest

    def search(self, query: str, k: int, lang: str | None = None) -> list[tuple[Chunk, float]]:
        q = _normalize(llm.embed([query]))[0]
        scores = self.vecs @ q
        if lang:
            mask = np.array([c.lang == lang for c in self.chunks])
            scores = np.where(mask, scores, -np.inf)
        order = [i for i in np.argsort(-scores)[:k] if np.isfinite(scores[i])]
        return [(self.chunks[i], float(scores[i])) for i in order]

    def retrieve(self, query: str, rcfg: dict, lang: str | None = None) -> list[tuple[Chunk, float]]:
        """Embedding top-k; with use_rerank, take `candidates` first and re-sort them with the reranker.
        lang filters to one edition; otherwise the edition matching the query language gets a small bonus."""
        k = rcfg["top_k"]
        hits = self.search(query, max(rcfg["candidates"], k) if rcfg["use_rerank"] else k * 3, lang)
        if rcfg["use_rerank"] and hits:
            scores = llm.rerank(query, [c.text for c, _ in hits])
            hits = [(c, float(s)) for (c, _), s in zip(hits, scores)]
        if rcfg.get("prefer_lang") and not lang:
            qlang = detect_lang(query)
            hits = [(c, s + (LANG_BONUS if c.lang == qlang else 0.0)) for c, s in hits]
        return sorted(hits, key=lambda h: -h[1])[:k]


def build_index(cfg: dict, progress=print) -> Index:
    sections = []
    for p in _parsed_files(cfg):
        if not p.exists():
            raise RuntimeError(f"{p.name} is missing. Run: python -m ragbot ingest")
        sections += build_sections(load_parsed(p), domain.SECTION_RULES)
    chunks = chunk_sections(sections, cfg["chunking"], cfg["documents"]["citation"])
    progress(f"  {len(sections)} sections → {len(chunks)} chunks; embedding…")
    vecs = _normalize(llm.embed([c.text for c in chunks]))
    manifest = {"fingerprint": fingerprint(cfg), "embed_model": llm.EMBED_MODEL, "n_chunks": len(chunks),
                "by_lang": {lang: sum(c.lang == lang for c in chunks) for lang in {c.lang for c in chunks}}}
    INDEX_DIR.mkdir(exist_ok=True)
    np.save(INDEX_DIR / "vectors.npy", vecs)
    (INDEX_DIR / "chunks.json").write_text(json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    (INDEX_DIR / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return Index(chunks, vecs, manifest)


def load_index() -> Index | None:
    try:
        chunks = [Chunk(**c) for c in json.loads((INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))]
        return Index(chunks, np.load(INDEX_DIR / "vectors.npy"),
                     json.loads((INDEX_DIR / "manifest.json").read_text(encoding="utf-8")))
    except FileNotFoundError:
        return None


def is_stale(index: Index, cfg: dict) -> bool:
    return index.manifest.get("fingerprint") != fingerprint(cfg)
