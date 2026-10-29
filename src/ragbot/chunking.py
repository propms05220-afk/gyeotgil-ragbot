"""Split document sections into chunks that keep their heading path.

Each chunk's embedded text starts with a breadcrumb line, e.g.
  [handbook en p.12] 7 Leave of absence > Required documents
so a chunk that only says "passport, 1 photo" can still be found by "documents for leave of absence".
"""
from ragbot.schemas import Chunk, Section


def split_lines(text: str, max_chars: int, overlap: int) -> list[str]:
    """Pack whole lines into pieces of at most max_chars; carry trailing lines (≤ overlap chars) forward."""
    pieces, cur = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        while len(line) > max_chars:   # a single over-long line is cut by characters
            if cur:
                pieces.append("\n".join(cur))
                cur = []
            pieces.append(line[:max_chars])
            line = line[max_chars - overlap:]
        if cur and len("\n".join(cur + [line])) > max_chars:
            pieces.append("\n".join(cur))
            keep = []
            for prev in reversed(cur):
                if len("\n".join([prev] + keep)) > overlap:
                    break
                keep.insert(0, prev)
            cur = keep
        cur.append(line)
    if cur:
        pieces.append("\n".join(cur))
    return pieces


def split_table(md: str, max_chars: int) -> list[str]:
    """Split a markdown table by rows, repeating the header (first 2 lines) in every piece."""
    lines = md.splitlines()
    header, rows = lines[:2], lines[2:]
    pieces, cur = [], []
    for row in rows:
        if cur and len("\n".join(header + cur + [row])) > max_chars:
            pieces.append("\n".join(header + cur))
            cur = []
        cur.append(row)
    if cur or not pieces:
        pieces.append("\n".join(header + cur))
    return pieces


def chunk_sections(sections: list[Section], cfg: dict, label: str = "doc") -> list[Chunk]:
    max_chars, overlap = cfg["max_chars"], cfg["overlap_chars"]
    chunks: list[Chunk] = []
    for s in sections:
        if s.kind == "table" and cfg["table_as_chunk"]:
            bodies = split_table(s.text, max_chars)
        else:
            bodies = split_lines(s.text, max_chars, overlap)
        for body in bodies:
            crumb = f"[{label} {s.lang} p.{s.page}] " + " > ".join(s.path)
            chunks.append(Chunk(len(chunks), s.source, s.lang, s.path, s.page, s.kind,
                                f"{crumb}\n{body}", s.low_confidence))
    return chunks
