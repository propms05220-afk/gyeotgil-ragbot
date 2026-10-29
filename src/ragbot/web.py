"""Web search for questions the documents and tables do not cover.

Official domains (config.yaml → web.official_domains) are searched first, then the first (main) domain alone, then
the open web; results from non-official sites are marked official=False so the agent can warn the user.
DuckDuckGo (ddgs) is flaky: the same query can return results on one call and "No results found" on the next.
So each query is tried twice, and empty results are never cached (a transient failure must not stick).
Non-empty results are cached in .cache/ like model calls, so evals are repeatable.
"""
import time
from urllib.parse import urlparse

from ddgs import DDGS

from ragbot import llm

ATTEMPTS = 2


def _is_official(url: str, domains: list[str]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in domains)


class _Empty(Exception):
    pass


def _search(query: str, max_results: int) -> list[dict]:
    def call():
        for attempt in range(ATTEMPTS):
            try:
                rows = DDGS().text(query, max_results=max_results)
            except Exception:   # ddgs raises DDGSException("No results found") on transient failures too
                rows = []
            if rows:
                return [{"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
                        for r in rows]
            time.sleep(1 + attempt)
        raise _Empty(query)   # raising keeps the empty result out of the cache
    try:
        return llm.cached("web", {"q": query, "n": max_results}, call)
    except _Empty:
        return []


def web_search(query: str, cfg: dict) -> dict:
    domains, n = cfg["web"]["official_domains"], cfg["web"]["max_results"]
    attempts = [f"{query} (" + " OR ".join(f"site:{d}" for d in domains) + ")", f"{query} site:{domains[0]}"]
    results = []
    for q in attempts:
        results = [r for r in _search(q, n * 2) if _is_official(r["url"], domains)][:n]
        if results:
            break
    official = bool(results)
    if not results:
        results = _search(query, n)
    for r in results:
        r["official"] = _is_official(r["url"], domains)
    out = {"query": query, "official_results": official, "results": results,
           "note": "Web results can be outdated. Cite the URL and tell the user to verify."}
    if not results:
        out["note"] = "No web results. Try different keywords, e.g. in the language of the sites you expect."
    return out
