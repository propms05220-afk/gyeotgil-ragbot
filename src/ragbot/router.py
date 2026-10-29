"""Router: before any search, decide which source should hold the answer.

One LLM call reads the source cards in config.yaml (what each source covers and does NOT cover) and returns
  {"primary": "<a source name>|none", "fallback": [...], "reason": "..."}
The agent then starts with the primary source's tools. The plan is stored on the Answer and in the trace,
and the eval scores it separately (router_accuracy), so a wrong decision is distinguishable from a bad search.
"""
import json
import re

from ragbot import llm
from ragbot.index import Index

PROMPT = """You route questions for {name}: {purpose}
Decide which source most likely contains the answer, using what each source covers and does NOT cover.

{cards}

none: ONLY greetings, thanks, small talk, or questions about what this helper can do.
      Never choose none for a request for information, even if you think no source has it.

Rules:
- If no source card clearly covers a factual question, choose {default}.
- Read each "does NOT cover" list carefully. If the primary candidate explicitly does not cover the question, pick another.
- primary: the single best source. fallback: other sources worth trying if primary lacks the answer (may be empty).
- A question can need two sources (e.g. a rule from the documents and a value from a table).

Conversation so far (may be empty):
{history}

Question: {question}

Reply with ONLY a JSON object: {{"primary": "...", "fallback": ["..."], "reason": "one short sentence"}}"""


def document_outline(index: Index, langs: list[str] | None = None) -> str:
    """Section and subsection titles from the index: the documents' real coverage map.
    Section titles alone are often too vague; the router must see the subsections too."""
    tree: dict[str, dict] = {}
    for c in index.chunks:
        if (not langs or c.lang in langs) and c.path and not c.path[0].startswith("("):
            subs = tree.setdefault(c.path[0], {})
            if len(c.path) > 1:
                title = re.sub(r"^\W+", "", c.path[1]).split("(")[0].strip()[:40]   # drop leading bullet symbols
                subs.setdefault(title, None)
    return "\n".join(f"      - {sec}: {'; '.join(subs)}" if subs else f"      - {sec}" for sec, subs in tree.items())


def source_cards(cfg: dict, index: Index) -> str:
    outline = document_outline(index, cfg["documents"].get("outline_langs"))
    out = []
    for name, card in cfg["sources"].items():
        covers = card["covers"].replace("{document_outline}", outline).strip()
        out.append(f"{name}:\n  covers: {covers}\n  does NOT cover: {card['not_covers'].strip()}")
    return "\n\n".join(out)


def route(question: str, cfg: dict, index: Index, history: list[dict] | None = None) -> dict:
    """Returns {"primary", "fallback", "reason"}; on any failure, a permissive plan over all sources."""
    sources = list(cfg["sources"])
    rc = cfg.get("router", {})
    hist = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in (history or [])[-4:])
    prompt = PROMPT.format(name=cfg["chatbot"]["name"], purpose=cfg["chatbot"]["purpose"].strip(),
                           cards=source_cards(cfg, index), default=rc.get("default_route", sources[-1]),
                           history=hist or "(none)", question=question)
    try:
        text = llm.chat([{"role": "user", "content": prompt}])["content"]
        plan = json.loads(text[text.find("{"): text.rfind("}") + 1])
        primary = plan.get("primary")
        if primary not in [*sources, "none"]:
            raise ValueError(f"unknown route {primary!r}")
        fallback = [r for r in plan.get("fallback") or [] if r in sources and r != primary]
        return {"primary": primary, "fallback": fallback, "reason": str(plan.get("reason", ""))}
    except Exception as e:
        return {"primary": sources[0], "fallback": sources[1:],
                "reason": f"router failed ({type(e).__name__}); trying all sources"}
