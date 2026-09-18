"""Team-owned Streamlit entry point. Run: streamlit run src/ui/app.py"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit Cloud executes this file by path; ensure the repository root is
# importable before loading sibling modules as the ``src.ui`` package.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from .aura_service import connect_aura
    from .chat_graph_page import render_chat, render_graph
    from .data_loader import load_app_data
    from .main_page import render_home, render_recommendations
    from .map_page import render_detail, render_map
except ImportError:  # Supports `streamlit run src/ui/app.py` as well as package imports.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.ui.aura_service import connect_aura
    from src.ui.chat_graph_page import render_chat, render_graph
    from src.ui.data_loader import load_app_data
    from src.ui.main_page import render_home, render_recommendations
    from src.ui.map_page import render_detail, render_map


def main() -> None:
    st.set_page_config(page_title="Festival Explorer", page_icon="🎪", layout="wide")
    data = load_app_data()
    try:
        secrets = st.secrets
    except Exception:
        secrets = {}
    if "aura_driver" not in st.session_state:
        st.session_state["aura_driver"] = connect_aura(secrets)
    data["aura_driver"] = st.session_state["aura_driver"]
    pages = ["메인", "추천", "지도", "축제 상세", "챗봇", "지식그래프"]
    default_page = st.session_state.get("page", "메인")
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #f7fbff; }
    [data-testid="stSidebar"] { display: none; }
    .topbar { background: linear-gradient(90deg, #07345d, #0b5680); padding: .7rem 1rem; border-radius: 0 0 16px 16px; margin: -1rem -1rem 1.2rem; }
    .brand { color: #fff; font-size: 1.35rem; font-weight: 900; letter-spacing: -.04em; }
    .eyebrow { color: #9de7f0; font-size: .72rem; letter-spacing: .18em; font-weight: 800; }
    .festival-card-region { color: #ef5b68; font-size: .78rem; font-weight: 800; margin-top: .45rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #e3eaf2; border-radius: 18px; background: rgba(255,255,255,.88); }
    h1, h2, h3 { color: #123253; letter-spacing: -.045em; }
    .stButton > button { border-radius: 12px; border: 1px solid #dbe7f1; font-weight: 700; }
    footer { visibility: hidden; }
    </style>
    <div class="topbar"><div class="eyebrow">FESTIVAL TOGETHER</div><div class="brand">축제를 발견하세요</div></div>
    """, unsafe_allow_html=True)
    nav_cols = st.columns(len(pages))
    page = default_page if default_page in pages else pages[0]
    for col, candidate in zip(nav_cols, pages):
        if col.button(candidate, key=f"nav-{candidate}", use_container_width=True):
            page = candidate
            st.session_state["page"] = candidate
            st.rerun()
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
