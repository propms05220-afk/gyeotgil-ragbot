"""Web app entry point.  Run from the project root:  streamlit run app/streamlit_app.py

Two pages: the chat for students, and the evaluation page that shows how the chatbot is measured.
"""
import streamlit as st

from ragbot.config import load_config

st.set_page_config(page_title=load_config()["chatbot"]["name"], page_icon="🎓", layout="wide")
st.navigation([
    st.Page("chat.py", title="Chat", icon="💬", default=True),
    st.Page("evaluation.py", title="Evaluation", icon="📊"),
]).run()
