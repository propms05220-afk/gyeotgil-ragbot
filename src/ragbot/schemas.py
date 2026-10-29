"""Data contracts between pipeline layers. Changing a field here needs a decision record (docs/decisions/)."""
from dataclasses import asdict, dataclass, field


@dataclass
class Section:
    """One document section after parsing: the unit that chunking splits further."""
    source: str                 # file name, e.g. "handbook_en.pdf"
    lang: str                   # edition language: ko | en | zh
    path: list[str]             # heading path, e.g. ["7 Leave of absence", "Required documents"]
    page: int                   # first page of the section
    text: str                   # markdown body (tables as GFM)
    kind: str = "text"          # text | table
    low_confidence: bool = False  # true if the page text came from OCR flagged as low confidence


@dataclass
class Chunk:
    chunk_id: int
    source: str
    lang: str
    path: list[str]
    page: int
    kind: str
    text: str                   # what gets embedded: breadcrumb line + body
    low_confidence: bool = False

    def citation(self, label: str) -> str:
        """e.g. citation("handbook") → "handbook en p.12"; the label comes from config documents.citation."""
        return f"{label} {self.lang} p.{self.page}"


@dataclass
class Answer:
    answer: str
    sources: list[str] = field(default_factory=list)   # citations, e.g. "handbook ko p.12", "product list", URLs
    routes: list[str] = field(default_factory=list)    # which sources were used: names of config.yaml sources
    tool_calls: list[dict] = field(default_factory=list)
    trace_id: str = ""
    plan: dict | None = None   # router decision {"primary", "fallback", "reason"} (decision 0006)

    def to_dict(self) -> dict:
        return asdict(self)
