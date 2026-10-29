"""Chat page (opened through streamlit_app.py)."""
import json

import streamlit as st

from ragbot import domain, llm
from ragbot.agent import Chatbot
from ragbot.config import load_config
from ragbot.index import is_stale, load_index

cfg = load_config()

BADGES = {name: card.get("label", name) for name, card in cfg["sources"].items()}

# UI language: the app's own words live here; the chatbot's words (name, about, greeting, examples) come from
# config.yaml chatbot.* (Korean) and chatbot.translations.en. Answers follow the language of the question.
LANGS = {"한국어": "ko", "English": "en"}
UI = {
    "ko": {"new": "새 대화", "system": "시스템", "tools": "도구", "input": "질문을 입력하세요 (한국어·영어)",
           "thinking": "찾아보는 중…", "planned": "🧭 계획", "sources": "출처", "calls": "도구 호출",
           "api_error": "모델 API 오류", "stale": "인덱스나 표 데이터베이스가 없거나 오래됐어요. "
                                               "`python -m ragbot build` 를 실행한 뒤 새로고침하세요."},
    "en": {"new": "New conversation", "system": "System", "tools": "Tools", "input": "Ask in Korean or English…",
           "thinking": "Looking it up…", "planned": "🧭 Planned", "sources": "Sources", "calls": "tool call(s)",
           "api_error": "Model API error", "stale": "The index or a table database is missing or out of date. "
                                                   "Run `python -m ragbot build`, then reload."},
}


def text(key: str) -> str:
    """The chatbot's own wording in the chosen language, falling back to the default (Korean) config value."""
    lang = st.session_state.get("lang_code", "ko")
    return cfg["chatbot"].get("translations", {}).get(lang, {}).get(key) or cfg["chatbot"].get(key, "")


@st.cache_resource(show_spinner="Loading…")
def get_bot(fingerprint: str) -> Chatbot:
    return Chatbot(cfg, load_index())


def ready() -> str | None:
    index = load_index()
    if index is None or is_stale(index, cfg) or domain.tables_ready(cfg):
        return None
    return index.manifest["fingerprint"]


def show_details(msg: dict, ui: dict):
    if msg.get("plan"):
        p = msg["plan"]
        st.caption(f"{ui['planned']}: {p['primary']}" + (f" → {', '.join(p['fallback'])}" if p["fallback"] else "")
                   + f" — {p['reason']}")
    if msg.get("routes"):
        st.caption("  ·  ".join(BADGES.get(r, r) for r in msg["routes"]))
    if msg.get("sources"):
        st.caption(f"{ui['sources']}: " + ", ".join(f"`{s}`" for s in msg["sources"][:8]))
    if msg.get("tool_calls"):
        with st.expander(f"🔧 {len(msg['tool_calls'])} {ui['calls']} · trace {msg.get('trace_id', '')}"):
            for n, t in enumerate(msg["tool_calls"], 1):
                st.markdown(f"**{n}. {t['name']}** `{json.dumps(t['arguments'], ensure_ascii=False)}`")
                st.json(t["result"], expanded=False)


with st.sidebar:
    choice = st.radio("언어 / Language", list(LANGS), horizontal=True, key="lang")
    st.session_state.lang_code = LANGS[choice]
    ui = UI[st.session_state.lang_code]
    st.header("🎓 " + text("name"))
    st.markdown(text("about"))
    if st.button(ui["new"], width="stretch"):
        st.session_state.messages = []
        st.rerun()
    with st.expander(ui["system"]):
        st.caption(llm.describe())
        st.caption(f"{ui['tools']}: {', '.join(cfg['agent']['tools'])}")

fingerprint = ready()
if fingerprint is None:
    st.warning(ui["stale"])
    st.stop()
bot = get_bot(fingerprint)

st.session_state.setdefault("messages", [])
with st.chat_message("assistant"):
    st.markdown(text("greeting"))
    if not st.session_state.messages:
        cols = st.columns(2)
        for i, ex in enumerate(text("examples") or []):
            if cols[i % 2].button(ex, key=f"ex{i}", width="stretch"):
                st.session_state.pending = ex
                st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        show_details(msg, ui)

question = st.chat_input(ui["input"]) or st.session_state.pop("pending", None)
if question:
    with st.chat_message("user"):
        st.markdown(question)
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    with st.chat_message("assistant"):
        with st.spinner(ui["thinking"]):
            try:
                ans = bot.answer(question, history)
            except Exception as e:
                st.error(f"{ui['api_error']}: {type(e).__name__}: {e}")
                st.stop()
        st.markdown(ans.answer)
        msg = {"role": "assistant", "content": ans.answer, **{k: v for k, v in ans.to_dict().items() if k != "answer"}}
        show_details(msg, ui)
    st.session_state.messages += [{"role": "user", "content": question}, msg]
