"""Team-owned Streamlit entry point. Run: streamlit run src/ui/app.py"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import sys
from pathlib import Path

# Streamlit Cloud executes this file by path; ensure the repository root is
# importable before loading sibling modules as the ``src.ui`` package.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from .chat_graph_page import render_chat, render_graph
    from .data_loader import load_app_data
    from .main_page import render_home, render_recommendations
    from .map_page import render_detail, render_map
except ImportError:  # Supports `streamlit run src/ui/app.py` as well as package imports.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.ui.chat_graph_page import render_chat, render_graph
    from src.ui.data_loader import load_app_data
    from src.ui.main_page import render_home, render_recommendations
    from src.ui.map_page import render_detail, render_map


def main() -> None:
    st.set_page_config(page_title="Festival Explorer", page_icon="🎪", layout="wide")
    data = load_app_data()
    pages = ["메인", "추천", "지도", "축제 상세", "챗봇", "지식그래프"]
    default_page = st.session_state.get("page", "메인")
    page = st.sidebar.radio("페이지", pages, index=pages.index(default_page) if default_page in pages else 0)
    st.session_state["page"] = page
    if page == "메인": render_home(st, data)
    elif page == "추천": render_recommendations(st, data)
    elif page == "지도": render_map(st, data)
    elif page == "축제 상세":
        selected = st.session_state.get("selected_festival")
        if selected is not None: render_detail(st, selected, data["triples"])
        elif data["festivals"]: render_detail(st, data["festivals"][0], data["triples"])
        else: st.info("축제 데이터를 찾을 수 없습니다.")
    elif page == "챗봇": render_chat(st, data)
    else: render_graph(st, data)


if __name__ == "__main__": main()
