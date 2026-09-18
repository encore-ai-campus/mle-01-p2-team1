"""Home dashboard and recommendation page for the Streamlit app."""
from __future__ import annotations

import base64
from datetime import date
from pathlib import Path
from typing import Any

from .components import empty_state, festival_card, festival_detail_callback
from .recommendations import PRESETS, build_filter_options, recommend_festivals


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
        .home-subtitle { color: #536581; font-size: 1.05rem; margin: .8rem 0 1.5rem; }
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
    st.markdown('<div class="home-hero"><div class="home-kicker">FESTIVAL TOGETHER</div><div class="home-title">\uc6b0\ub9ac \ub3d9\ub124 \ucd95\uc81c \ud0d0\uc0c9</div><div class="home-subtitle">\uc9c0\uc5ed\uacfc \ud14c\ub9c8\uc5d0 \ub9de\ub294 \ucd95\uc81c\ub97c \uac80\uc0c9\ud558\uace0, \uc6d0\ud558\ub294 \ud398\uc774\uc9c0\ub85c \ubc14\ub85c \uc774\ub3d9\ud574\ubcf4\uc138\uc694.</div></div>', unsafe_allow_html=True)


    st.markdown('<div class="search-card"><div class="search-label">\ucd95\uc81c \uac80\uc0c9</div><div class="search-hint">\ub2e4\uc591\ud55c \ucd95\uc81c\ub97c \uac80\uc0c9\ud574\ubcf4\uc138\uc694.</div>', unsafe_allow_html=True)
    search_cols = st.columns([5, 1])
    query = search_cols[0].text_input("\ucd95\uc81c \uac80\uc0c9", placeholder="\ucd95\uc81c\uba85, \uc9c0\uc5ed, \ud14c\ub9c8\ub97c \uac80\uc0c9\ud574\ubcf4\uc138\uc694", label_visibility="collapsed", key="home_search_input")
    search_cols[1].markdown('<div class="search-button">', unsafe_allow_html=True)
    search_clicked = search_cols[1].button("\uac80\uc0c9", key="home_search_button")
    search_cols[1].markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="chip-row"><span class="chip">\uc608\uc2dc</span><span class="chip">\ubc9a\uaf43</span><span class="chip">\uc11c\uc6b8</span><span class="chip">\uba39\uac70\ub9ac</span><span class="chip">\ubb38\ud654\uc608\uc220</span><span class="chip">\uc5ec\ub984</span><span class="chip">\uac00\uc871</span></div></div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-heading">\ucd95\uc81c \ub370\uc774\ud130 \uac1c\uc694</div>', unsafe_allow_html=True)
    metric_cols = st.columns(2)
    metric_cols[0].markdown(f'<div class="stat-card stat-card-pink"><div class="stat-label">\ucd1d \ucd95\uc81c \uac1c\uc218</div><div class="stat-value">{len(data.get("festivals", []))}</div></div>', unsafe_allow_html=True)
    metric_cols[1].markdown(f'<div class="stat-card stat-card-blue"><div class="stat-label">\uc9c0\uc2dd\uadf8\ub798\ud504 \uad00\uacc4 \uac1c\uc218</div><div class="stat-value">{len(data.get("triples", []))}</div></div>', unsafe_allow_html=True)
    _home_recommendations(st, data)
    _page_shortcuts(st)
    st.caption("\uc67c\ucabd \uba54\ub274\uc5d0\uc11c\ub3c4 \ucd94\ucc9c, \uc9c0\ub3c4, \ucc57\ubd07 \ud398\uc774\uc9c0\ub97c \uc5f4 \uc218 \uc788\uc2b5\ub2c8\ub2e4.")


def render_recommendations(st: Any, data: dict[str, Any]) -> None:
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
    rows, total = recommend_festivals(
        festivals,
        region=selected_region,
        theme=selected_theme,
        month=selected_month,
        audience=selected_audience,
        fee=selected_fee,
        preset=selected_preset,
        today=date.today(),
        limit=4,
    )
    st.caption(f"총 {total}개 중 {len(rows)}개 추천")
    if not rows:
        return empty_state(st, "조건에 맞는 축제가 없습니다.")

    for start in range(0, len(rows), 2):
        columns = st.columns(2)
        for column, (index, row) in zip(columns, enumerate(rows[start : start + 2], start=start)):
            with column:
                _render_recommendation_card(st, row, f"recommend-{index}")


def _format_recommendation_period(row: dict[str, Any]) -> str:
    def display(value: Any) -> str:
        text = str(value or "").replace("-", "")
        if len(text) >= 8 and text[:8].isdigit():
            return f"{text[:4]}.{text[4:6]}.{text[6:8]}"
        return text or "일정 정보 없음"

    return f"{display(row.get('start_date'))} ~ {display(row.get('end_date'))}"


def _render_recommendation_card(st: Any, row: dict[str, Any], key: str) -> None:
    with st.container(border=True):
        st.subheader(str(row.get("name") or "축제명 정보 없음"))
        st.caption(
            f":material/location_on: {row.get('region') or '지역 정보 없음'}  ·  "
            f":material/calendar_month: {_format_recommendation_period(row)}"
        )
        st.markdown(f"**요금**  {row.get('usage_fee') or '요금 정보 없음'}")
        labels = [*row.get("themes", [])[:2], *row.get("audiences", [])[:2]]
        if labels:
            st.caption(" · ".join(f"#{label}" for label in labels))
        if st.button("상세 보기", key=key, width="stretch"):
            festival_detail_callback(st, row)
