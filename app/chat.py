"""Chat page (opened through streamlit_app.py)."""
import json

import streamlit as st

from ragbot import domain, llm
from ragbot.agent import Chatbot
from ragbot.config import load_config
from ragbot.index import is_stale, load_index

cfg = load_config()

BADGES = {name: card.get("label", name) for name, card in cfg["sources"].items()}
EXAMPLES = cfg["chatbot"].get("examples", [])


@st.cache_resource(show_spinner="Loading…")
def get_bot(fingerprint: str) -> Chatbot:
    return Chatbot(cfg, load_index())


def ready() -> str | None:
    index = load_index()
    if index is None or is_stale(index, cfg) or domain.tables_ready(cfg):
        return None
    return index.manifest["fingerprint"]


def show_details(msg: dict):
    if msg.get("plan"):
        p = msg["plan"]
        st.caption(f"🧭 Planned: {p['primary']}" + (f" → {', '.join(p['fallback'])}" if p["fallback"] else "")
                   + f" — {p['reason']}")
    if msg.get("routes"):
        st.caption("  ·  ".join(BADGES.get(r, r) for r in msg["routes"]))
    if msg.get("sources"):
        st.caption("Sources: " + ", ".join(f"`{s}`" for s in msg["sources"][:8]))
    if msg.get("tool_calls"):
        with st.expander(f"🔧 {len(msg['tool_calls'])} tool call(s) · trace {msg.get('trace_id', '')}"):
            for n, t in enumerate(msg["tool_calls"], 1):
                st.markdown(f"**{n}. {t['name']}** `{json.dumps(t['arguments'], ensure_ascii=False)}`")
                st.json(t["result"], expanded=False)


with st.sidebar:
    st.header("🎓 " + cfg["chatbot"]["name"])
    st.markdown(cfg["chatbot"].get("about", ""))
    if st.button("New conversation", width="stretch"):
        st.session_state.messages = []
        st.rerun()
    with st.expander("System"):
        st.caption(llm.describe())
        st.caption(f"Tools: {', '.join(cfg['agent']['tools'])}")

fingerprint = ready()
if fingerprint is None:
    st.warning("The index or a table database is missing or out of date. Run `python -m ragbot build`, then reload.")
    st.stop()
bot = get_bot(fingerprint)

st.session_state.setdefault("messages", [])
with st.chat_message("assistant"):
    st.markdown(cfg["chatbot"]["greeting"])
    if not st.session_state.messages:
        cols = st.columns(2)
        for i, ex in enumerate(EXAMPLES):
            if cols[i % 2].button(ex, key=f"ex{i}", width="stretch"):
                st.session_state.pending = ex
                st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        show_details(msg)

question = st.chat_input("Ask in any language…") or st.session_state.pop("pending", None)
if question:
    with st.chat_message("user"):
        st.markdown(question)
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    with st.chat_message("assistant"):
        with st.spinner("Looking it up…"):
            try:
                ans = bot.answer(question, history)
            except Exception as e:
                st.error(f"Model API error: {type(e).__name__}: {e}")
                st.stop()
        st.markdown(ans.answer)
        msg = {"role": "assistant", "content": ans.answer, **{k: v for k, v in ans.to_dict().items() if k != "answer"}}
        show_details(msg)
    st.session_state.messages += [{"role": "user", "content": question}, msg]
