"""Home dashboard and recommendation page for the Streamlit app."""
from __future__ import annotations

import base64
from html import escape
from datetime import date
from pathlib import Path
from typing import Any

from .components import empty_state, festival_card, festival_detail_callback
from .data_loader import summarize_festival
from .recommendations import (
    PRESETS,
    RECOMMENDATION_PAGE_SIZE,
    build_filter_options,
    recommend_festivals,
)


RECOMMENDATION_PAGE = "\ucd94\ucc9c"
MAP_PAGE = "\uc9c0\ub3c4"
CHAT_PAGE = "\ucc57\ubd07"


def _apply_home_styles(st: Any) -> None:
    """Apply the visual language from the home-page design reference."""
    hero_image = Path(__file__).resolve().parents[2] / "assets" / "festival-hero.png"
    hero_uri = ""
    if hero_image.exists():
        encoded = base64.b64encode(hero_image.read_bytes()).decode("ascii")
        hero_uri = f"url('data:image/png;base64,{encoded}')"

    css = """
        <style>
        :root {
            --festival-pink: #f45b73;
            --festival-pink-soft: #fff0f3;
            --festival-blue: #2c78dc;
            --festival-ink: #182942;
            --festival-muted: #71809a;
        }
        .home-hero {
            background-image: linear-gradient(90deg, rgba(255,255,255,.98) 0%, rgba(255,255,255,.82) 43%, rgba(255,255,255,.05) 100%), __HERO_IMAGE__;
            background-position: center right;
            background-size: cover;
            border-radius: 0 0 28px 28px;
            min-height: 15rem;
            padding: 2.2rem 2.4rem 1.8rem;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 82% 5%, rgba(255, 222, 224, .8), transparent 25rem),
                linear-gradient(135deg, #fff 0%, #f8fbff 58%, #fff8f8 100%);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: rgba(255,255,255,.88);
            border-right: 1px solid #edf0f6;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            border-radius: 14px;
            padding: .55rem .7rem;
            color: var(--festival-ink);
            font-weight: 600;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background: #fff0f3;
            color: var(--festival-pink);
        }
        .home-kicker {
            color: var(--festival-pink);
            font-size: .82rem;
            font-weight: 800;
            letter-spacing: .18em;
            margin: .5rem 0 .35rem;
        }
        .home-title {
            color: var(--festival-ink);
            font-size: clamp(2.5rem, 5vw, 4.5rem);
            font-weight: 900;
            letter-spacing: -.07em;
            line-height: 1.05;
            margin: 0;
        }
        .home-title-desc {
            font-size: .38em;
            font-weight: 600;
            letter-spacing: -.03em;
            margin-left: .18em;
            vertical-align: .12em;
        }
        .home-subtitle { color: #536581; font-size: 1.05rem; margin: .8rem 0 1.5rem; }
        .search-card { margin-bottom: 0 !important; }
        div[data-testid="stHorizontalBlock"]:has(.search-button) { gap: 0 !important; }
        .search-button { margin-top: 0 !important; }
        .search-button + div [data-testid="stButton"] button { min-height: 2.5rem; }
        div[class*="st-key-home_search_button"] { transform: translateY(-1.25rem); }
        .section-heading {
            color: var(--festival-ink);
            font-size: 1.55rem;
            font-weight: 850;
            margin: 1.5rem 0 .7rem;
        }
        .search-card, .shortcut-card {
            background: rgba(255,255,255,.9);
            border: 1px solid rgba(240, 223, 230, .75);
            border-radius: 22px;
            box-shadow: 0 14px 35px rgba(45, 60, 95, .08);
            padding: 1.15rem 1.35rem;
        }
        .search-label { color: var(--festival-ink); font-size: 1.35rem; font-weight: 850; margin-bottom: .45rem; }
        .search-hint { color: var(--festival-muted); font-size: .9rem; margin: .45rem 0 0; }
        .chip-row { display:flex; flex-wrap:wrap; gap:.45rem; margin-top:.65rem; }
        .chip { background:#f3f5f9; border-radius:99px; color:#78859a; font-size:.78rem; padding:.35rem .75rem; }
        .chip:first-child { background:#fff0f3; color:var(--festival-pink); }
        [data-testid="stTextInput"] input {
            border: 1px solid #ffb4c1;
            border-radius: 14px;
            color: var(--festival-ink);
            min-height: 2.8rem;
        }
        .search-button button, [data-testid="stButton"] button {
            background: var(--festival-pink);
            border: 0;
            border-radius: 14px;
            color: white;
            font-weight: 800;
            min-height: 2.8rem;
            width: 100%;
        }
        .stat-card {
            border-radius: 20px;
            padding: .9rem 1.1rem;
            min-height: 8rem;
        }
        .stat-card-pink { background: linear-gradient(135deg, #fff1f4, #fff9fa); }
        .stat-card-blue { background: linear-gradient(135deg, #eef5ff, #f7faff); }
        .stat-label { color: #53617a; font-size: .9rem; font-weight: 650; }
        .stat-value { color: var(--festival-ink); font-size: 2.1rem; font-weight: 900; margin-top: .25rem; }
        .shortcut-card { min-height: 8.7rem; }
        .shortcut-card-pink { background: linear-gradient(135deg, #fffaf1, #fff); }
        .shortcut-card-green { background: linear-gradient(135deg, #f0fbf6, #fff); }
        .shortcut-card-purple { background: linear-gradient(135deg, #f8f2ff, #fff); }
        .shortcut-title { color: var(--festival-ink); font-size: 1.05rem; font-weight: 850; margin-bottom: .15rem; }
        .shortcut-copy { color: var(--festival-muted); font-size: .82rem; margin-bottom: .6rem; }
        [data-testid="stButton"] button {
            border-radius: 12px;
            min-height: 2.8rem;
        }
        .shortcut-button button {
            min-height: 8.7rem !important;
            text-align: left;
            white-space: pre-wrap;
            background: linear-gradient(135deg, #fffaf1, #fff);
            border: 1px solid #f1dfcf;
            color: var(--festival-ink);
        }
        footer { visibility: hidden; }
        </style>
        """.replace("__HERO_IMAGE__", hero_uri or "none")
    st.markdown(css, unsafe_allow_html=True)


def _navigate(st: Any, target: str) -> None:
    st.session_state["page"] = target
    st.rerun()


def _page_shortcuts(st: Any) -> None:
    st.markdown('<div class="section-heading">\ub2e4\ub978 \ud398\uc774\uc9c0 \ubc14\ub85c\uac00\uae30</div>', unsafe_allow_html=True)
    shortcut_cols = st.columns(3)
    shortcut_cols[0].markdown('<div class="shortcut-button">', unsafe_allow_html=True)
    if shortcut_cols[0].button("\ucd95\uc81c \ucd94\ucc9c\n\n\ub098\uc5d0\uac8c \ub531 \ub9de\ub294 \ucd95\uc81c\ub97c \ucc3e\uc544\ubcf4\uc138\uc694.", key="home_recommendation_button", use_container_width=True):
        _navigate(st, RECOMMENDATION_PAGE)
    shortcut_cols[1].markdown('<div class="shortcut-button">', unsafe_allow_html=True)
    if shortcut_cols[1].button("\ucd95\uc81c \uc9c0\ub3c4\n\n\uc9c0\ub3c4\uc5d0\uc11c \ucd95\uc81c\ub97c \ud55c\ub208\uc5d0 \ud655\uc778\ud574\ubcf4\uc138\uc694.", key="home_map_button", use_container_width=True):
        _navigate(st, MAP_PAGE)
    shortcut_cols[2].markdown('<div class="shortcut-button">', unsafe_allow_html=True)
    if shortcut_cols[2].button("\ucd95\uc81c \ucc57\ubd07\n\n\ucd95\uc81c\uc5d0 \ub300\ud574 \ubb3c\uc5b4\ubcf4\uc138\uc694.", key="home_chat_button", use_container_width=True):
        _navigate(st, CHAT_PAGE)


def _home_recommendations(st: Any, data: dict[str, Any]) -> None:
    """Show a compact, scrollable recommendation strip on the home page."""
    st.markdown('<div class="section-heading">\ucd95\uc81c \ucd94\ucc9c</div>', unsafe_allow_html=True)
    st.caption("\uc9c0\uae08 \uac00\ubcf4\uae30 \uc88b\uc740 \ucd95\uc81c\ub97c \ud655\uc778\ud574\ubcf4\uc138\uc694.")
    rows = data.get("festivals", [])[:9]
    if not rows:
        return empty_state(st, "\ucd94\ucc9c\ud560 \ucd95\uc81c \ub370\uc774\ud130\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.")

    with st.container(height=390, border=True):
        for start in range(0, len(rows), 3):
            columns = st.columns(3)
            for column, (index, row) in zip(columns, enumerate(rows[start:start + 3], start=start)):
                with column:
                    festival_card(st, row, f"home-recommend-{index}", lambda selected: festival_detail_callback(st, selected))


def render_home(st: Any, data: dict[str, Any]) -> None:
    """Render search, overview, and shortcuts on the main page."""
    _apply_home_styles(st)
    st.markdown('<div class="home-hero"><div class="home-kicker">FESTIVAL TOGETHER</div><div class="home-title">\ucd95\uc9c0\ubc95<span class="home-title-desc">(\ucd95\uc81c \uc9c0\uc2dd\uc744 \ucc3e\ub294 \ubc29\ubc95)</span></div><div class="home-subtitle">\uc9c0\uc5ed\uacfc \ud14c\ub9c8\uc5d0 \ub9de\ub294 \ucd95\uc81c\ub97c \uac80\uc0c9\ud558\uace0, \uc6d0\ud558\ub294 \ud398\uc774\uc9c0\ub85c \ubc14\ub85c \uc774\ub3d9\ud574\ubcf4\uc138\uc694.</div></div>', unsafe_allow_html=True)


    st.markdown('<div class="search-card"><div class="search-label">\ucd95\uc81c \uac80\uc0c9</div><div class="search-hint">\ub2e4\uc591\ud55c \ucd95\uc81c\ub97c \uac80\uc0c9\ud574\ubcf4\uc138\uc694.</div></div>', unsafe_allow_html=True)
    search_cols = st.columns([6, 1])
    query = search_cols[0].text_input("\ucd95\uc81c \uac80\uc0c9", placeholder="\ucd95\uc81c\uba85, \uc9c0\uc5ed, \ud14c\ub9c8\ub97c \uac80\uc0c9\ud574\ubcf4\uc138\uc694", label_visibility="collapsed", key="home_search_input")
    search_cols[1].markdown('<div class="search-button">', unsafe_allow_html=True)
    search_clicked = search_cols[1].button("\uac80\uc0c9", key="home_search_button")
    search_cols[1].markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="chip-row"><span class="chip">\uc608\uc2dc</span><span class="chip">\ubc9a\uaf43</span><span class="chip">\uc11c\uc6b8</span><span class="chip">\uba39\uac70\ub9ac</span><span class="chip">\ubb38\ud654\uc608\uc220</span><span class="chip">\uc5ec\ub984</span><span class="chip">\uac00\uc871</span></div>', unsafe_allow_html=True)
    if search_clicked or query.strip():
        normalized_query = query.strip().casefold()
        matches = [
            row for row in data.get("festivals", [])
            if normalized_query in str(row).casefold()
        ]
        st.caption(f"\uac80\uc0c9 \uacb0\uacfc {len(matches)}\uac1c")
        if matches:
            for i, row in enumerate(matches[:10]):
                festival_card(st, row, f"home-search-{i}", lambda selected: festival_detail_callback(st, selected))
        else:
            empty_state(st, "\uac80\uc0c9\ud55c \ucd95\uc81c\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.")

    _home_recommendations(st, data)



def render_recommendations(st: Any, data: dict[str, Any]) -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-recommend-card-"]) {
            height: 280px !important;
            min-height: 280px !important;
            overflow: hidden;
            overflow-y: hidden;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-recommend-card-"])
        > div[data-testid="stVerticalBlock"] {
            min-height: 280px !important;
            height: 280px !important;
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-recommend-card-"])
        [data-testid="stButton"] {
            margin-top: auto !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-recommend-card-"]) h3 {
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            overflow: hidden;
            min-height: 2.4rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-recommend-card-"])
        [data-testid="stCaptionContainer"] {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .recommendation-summary {
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            overflow: hidden;
            color: #5e6b80;
            font-size: .84rem;
            line-height: 1.45;
            min-height: 3.1rem;
            margin: .35rem 0 .2rem;
        }
        .recommendation-labels {
            min-height: 1.6rem;
            color: #8a94a6;
            font-size: .82rem;
            line-height: 1.4;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin: .2rem 0 .35rem;
        }
        .st-key-recommendation-pagination [data-testid="stHorizontalBlock"] {
            justify-content: center !important;
            gap: .25rem !important;
        }
        .st-key-recommendation-pagination [data-testid="stColumn"] {
            flex: 0 0 auto !important;
            width: auto !important;
        }
        .st-key-recommendation-pagination [data-testid="stButton"] button {
            min-width: 2.35rem !important;
            width: auto !important;
            padding-left: .55rem !important;
            padding-right: .55rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("축제 추천")
    st.caption("지역과 테마, 기간, 대상층을 조합해 지금 가기 좋은 축제를 찾아보세요.")

    festivals = data.get("festivals", [])
    options = build_filter_options(festivals)
    with st.container(border=True):
        filter_row = st.columns(4)
        selected_region = filter_row[0].selectbox(
            "지역",
            options["regions"],
            key="recommend_region",
        )
        selected_theme = filter_row[1].selectbox(
            "테마",
            options["themes"],
            key="recommend_theme",
        )
        selected_month = filter_row[2].selectbox(
            "기간",
            options["months"],
            key="recommend_month",
        )
        selected_audience = filter_row[3].selectbox(
            "대상층",
            options["audiences"],
            key="recommend_audience",
        )
        selected_fee = st.segmented_control(
            "요금",
            options["fees"],
            default="전체",
            key="recommend_fee",
            width="stretch",
        )

    selected_preset = st.segmented_control(
        "추천 유형",
        PRESETS,
        default="전체",
        key="recommend_preset",
        width="stretch",
    )
    selected_preset = selected_preset or "전체"
    selected_fee = selected_fee or "전체"
    filter_signature = (
        selected_region,
        selected_theme,
        selected_month,
        selected_audience,
        selected_fee,
        selected_preset,
    )
    if st.session_state.get("recommend_filter_signature") != filter_signature:
        st.session_state["recommend_filter_signature"] = filter_signature
        st.session_state["recommend_page"] = 1

    page = max(int(st.session_state.get("recommend_page", 1)), 1)
    rows, total = recommend_festivals(
        festivals,
        region=selected_region,
        theme=selected_theme,
        month=selected_month,
        audience=selected_audience,
        fee=selected_fee,
        preset=selected_preset,
        today=date.today(),
        limit=RECOMMENDATION_PAGE_SIZE,
        offset=(page - 1) * RECOMMENDATION_PAGE_SIZE,
    )
    total_pages = max(1, (total + RECOMMENDATION_PAGE_SIZE - 1) // RECOMMENDATION_PAGE_SIZE)
    if page > total_pages:
        st.session_state["recommend_page"] = total_pages
        st.rerun()

    st.caption(f"총 {total}개 중 {len(rows)}개 추천 · {page} / {total_pages}페이지")
    if not rows:
        return empty_state(st, "조건에 맞는 축제가 없습니다.")

    for start in range(0, len(rows), 2):
        columns = st.columns(2)
        for column, (index, row) in zip(columns, enumerate(rows[start : start + 2], start=start)):
            with column:
                _render_recommendation_card(st, row, f"recommend-{index}")

    _render_recommendation_pagination(st, page, total_pages)


def _render_recommendation_pagination(st: Any, page: int, total_pages: int) -> None:
    if total_pages <= 1:
        return

    start = max(1, min(page - 2, total_pages - 4))
    page_numbers = list(range(start, min(total_pages, start + 4) + 1))
    with st.container(key="recommendation-pagination"):
        st.markdown('<div class="recommendation-pagination-anchor"></div>', unsafe_allow_html=True)
        columns = st.columns(len(page_numbers) + 2, gap="small")
        if columns[0].button("이전", disabled=page <= 1, key="recommend-page-prev"):
            st.session_state["recommend_page"] = page - 1
            st.rerun()
        for column, page_number in zip(columns[1:-1], page_numbers):
            with column:
                if st.button(
                    str(page_number),
                    key=f"recommend-page-{page_number}",
                    type="primary" if page_number == page else "secondary",
                ):
                    st.session_state["recommend_page"] = page_number
                    st.rerun()
        if columns[-1].button("다음", disabled=page >= total_pages, key="recommend-page-next"):
            st.session_state["recommend_page"] = page + 1
            st.rerun()


def _format_recommendation_period(row: dict[str, Any]) -> str:
    def display(value: Any) -> str:
        text = str(value or "").replace("-", "")
        if len(text) >= 8 and text[:8].isdigit():
            return f"{text[:4]}.{text[4:6]}.{text[6:8]}"
        return text or "일정 정보 없음"

    return f"{display(row.get('start_date'))} ~ {display(row.get('end_date'))}"


def _render_recommendation_card(st: Any, row: dict[str, Any], key: str) -> None:
    with st.container(border=True, key=f"recommend-card-{key}"):
        st.markdown('<span class="recommendation-card-anchor"></span>', unsafe_allow_html=True)
        st.subheader(str(row.get("name") or "축제명 정보 없음"))
        st.caption(
            f":material/location_on: {row.get('region') or '지역 정보 없음'}  ·  "
            f":material/calendar_month: {_format_recommendation_period(row)}"
        )
        summary = str(row.get("summary") or "").strip() or summarize_festival(str(row.get("text") or ""))
        if not summary:
            theme_labels = row.get("theme_categories") or row.get("themes", [])
            summary = (
                f"{' · '.join(str(label) for label in theme_labels[:2])} 테마 축제입니다."
                if theme_labels
                else "축제 상세 정보를 확인해 보세요."
            )
        st.markdown(
            f'<div class="recommendation-summary">{escape(summary)}</div>',
            unsafe_allow_html=True,
        )
        theme_labels = row.get("theme_categories") or row.get("themes", [])
        labels = [*theme_labels[:2], *row.get("audiences", [])[:2]]
        label_text = " · ".join(f"#{label}" for label in labels)
        label_class = "recommendation-labels"
        if not labels:
            label_class += " recommendation-labels-empty"
        st.markdown(
            f'<div class="{label_class}">{escape(label_text) or "&nbsp;"}</div>',
            unsafe_allow_html=True,
        )
        if st.button("상세 보기", key=key, width="stretch"):
            festival_detail_callback(st, row)
