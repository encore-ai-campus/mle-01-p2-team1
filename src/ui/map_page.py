"""Owner 2: map, preview carousel, and festival detail page."""

from __future__ import annotations

import base64
import json
import math
import os
import re
from pathlib import Path
from typing import Any
from html import escape

import plotly.graph_objects as go
import pydeck as pdk
import streamlit.components.v1 as components
from dotenv import load_dotenv
from PIL import Image

try:
    from .components import empty_state, festival_card, festival_detail_callback
    from .data_loader import festival_name, festival_text, load_json
except ImportError:
    from src.ui.components import empty_state, festival_card, festival_detail_callback
    from src.ui.data_loader import festival_name, festival_text, load_json


def _meta(row: dict[str, Any]) -> dict[str, Any]:
    """festival row 안의 metadata를 안전하게 가져옵니다."""
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _value(row: dict[str, Any], key: str, default: Any = "") -> Any:
    """최상위 필드와 metadata를 모두 확인합니다."""
    canonical_keys = {
        "event_start": "start_date",
        "event_end": "end_date",
        "eventplace": "event_place",
        "usetimefestival": "usage_fee",
        "agelimit": "age_limit",
    }
    value = row.get(key)

    if value not in (None, ""):
        return value

    return row.get(canonical_keys.get(key, key), _meta(row).get(key, default))


def _festival_region(row: dict[str, Any]) -> str:
    """주소에서 시/도 단위 지역명을 추출합니다."""

    address = str(
        _value(row, "address")
        or _value(row, "region")
        or _value(row, "location")
        or ""
    )

    region_map = {
        "서울특별시": "서울",
        "부산광역시": "부산",
        "대구광역시": "대구",
        "인천광역시": "인천",
        "광주광역시": "광주",
        "대전광역시": "대전",
        "울산광역시": "울산",
        "세종특별자치시": "세종",
        "경기도": "경기",
        "강원특별자치도": "강원",
        "강원도": "강원",
        "충청북도": "충북",
        "충청남도": "충남",
        "전북특별자치도": "전북",
        "전라북도": "전북",
        "전라남도": "전남",
        "경상북도": "경북",
        "경상남도": "경남",
        "제주특별자치도": "제주",
        "포항시": "경북",
    }

    for full_name, short_name in region_map.items():
        if full_name in address:
            return short_name

    return "미분류"


def _festival_region(row: dict[str, Any]) -> str:
    """Return a usable region even when the normalized region field is empty."""
    address = str(
        _value(row, "address")
        or _value(row, "region")
        or _value(row, "location")
        or ""
    ).strip()
    if not address:
        return "\ubbf8\ubd84\ub958"

    first_token = address.split()[0]
    if first_token.startswith("\ud3ec\ud56d") or "\ud3ec\ud56d" in address:
        return "\uacbd\ubd81"

    province_prefixes = (
        ("\uac15\uc6d0", "\uac15\uc6d0"),
        ("\uacbd\uae30", "\uacbd\uae30"),
        ("\uacbd\ubd81", "\uacbd\ubd81"),
        ("\uacbd\ub0a8", "\uacbd\ub0a8"),
        ("\ucda9\ubd81", "\ucda9\ubd81"),
        ("\ucda9\ub0a8", "\ucda9\ub0a8"),
        ("\uc804\ubd81", "\uc804\ubd81"),
        ("\uc804\ub0a8", "\uc804\ub0a8"),
        ("\ucda9\uccad\ubd81", "\ucda9\ubd81"),
        ("\ucda9\uccad\ub0a8", "\ucda9\ub0a8"),
        ("\uc804\ub77c\ubd81", "\uc804\ubd81"),
        ("\uc804\ub77c\ub0a8", "\uc804\ub0a8"),
        ("\uacbd\uc0c1\ubd81", "\uacbd\ubd81"),
        ("\uacbd\uc0c1\ub0a8", "\uacbd\ub0a8"),
        ("\uc11c\uc6b8", "\uc11c\uc6b8"),
        ("\ubd80\uc0b0", "\ubd80\uc0b0"),
        ("\ub300\uad6c", "\ub300\uad6c"),
        ("\uc778\ucc9c", "\uc778\ucc9c"),
        ("\uad11\uc8fc", "\uad11\uc8fc"),
        ("\ub300\uc804", "\ub300\uc804"),
        ("\uc6b8\uc0b0", "\uc6b8\uc0b0"),
        ("\uc138\uc885", "\uc138\uc885"),
        ("\uc81c\uc8fc", "\uc81c\uc8fc"),
    )
    for prefix, normalized in province_prefixes:
        if first_token.startswith(prefix):
            return normalized

    short_names = {
        "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc": "\uc11c\uc6b8",
        "\ubd80\uc0b0\uad11\uc5ed\uc2dc": "\ubd80\uc0b0",
        "\ub300\uad6c\uad11\uc5ed\uc2dc": "\ub300\uad6c",
        "\uc778\ucc9c\uad11\uc5ed\uc2dc": "\uc778\ucc9c",
        "\uad11\uc8fc\uad11\uc5ed\uc2dc": "\uad11\uc8fc",
        "\ub300\uc804\uad11\uc5ed\uc2dc": "\ub300\uc804",
        "\uc6b8\uc0b0\uad11\uc5ed\uc2dc": "\uc6b8\uc0b0",
        "\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc": "\uc138\uc885",
        "\uc81c\uc8fc\ud2b9\ubcc4\uc790\uce58\ub3c4": "\uc81c\uc8fc",
    }
    return short_names.get(first_token, first_token)


def _event_months(row: dict[str, Any]) -> set[int]:
    """
    행사 시작일~종료일 사이에 포함되는 월을 반환합니다.

    예:
    20260425 ~ 20260510
    -> {4, 5}
    """

    start = str(
        _value(row, "start_date")
        or _value(row, "event_start")
        or _value(row, "eventstartdate")
        or ""
    ).replace("-", "")

    end = str(
        _value(row, "end_date")
        or _value(row, "event_end")
        or _value(row, "eventenddate")
        or start
    ).replace("-", "")

    try:
        start_month = int(start[4:6])
        end_month = int(end[4:6])
    except (ValueError, IndexError):
        return set()

    if start_month <= end_month:
        return set(range(start_month, end_month + 1))

    return {start_month, end_month}


def _festival_image(row: dict[str, Any]) -> str | None:
    """축제 이미지 URL 후보를 찾습니다."""

    candidates = [
        "firstimage",
        "firstimage2",
        "image_url",
        "image",
        "thumbnail",
        "thumbnail_url",
    ]

    for key in candidates:
        value = _value(row, key)

        if value:
            return str(value)

    return None


def _fallback_image_uri() -> str:
    """외부 이미지가 막혀도 상세 화면에 보여줄 로컬 fallback 이미지."""
    image_path = Path(__file__).resolve().parents[2] / "assets" / "festival-hero.png"
    try:
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except OSError:
        return ""


def _render_knowledge_graph(st: Any, triples: list[dict[str, Any]], festival: str) -> None:
    """축제와 연결된 triple을 간단한 인터랙티브 네트워크로 렌더링합니다."""
    related = [
        triple for triple in triples
        if isinstance(triple, dict)
        and (triple.get("subject") == festival or triple.get("object") == festival)
    ][:20]
    related = related or [triple for triple in triples if isinstance(triple, dict)][:20]
    if not related:
        st.info("연결된 지식그래프 정보가 없습니다.")
        return

    edges: list[tuple[str, str, str]] = []
    nodes: list[str] = []
    for triple in related:
        subject = str(triple.get("subject") or "알 수 없음")
        object_ = str(triple.get("object") or "알 수 없음")
        relation = str(triple.get("relation") or "관련")
        edges.append((subject, object_, relation))
        nodes.extend((subject, object_))
    nodes = list(dict.fromkeys(nodes))

    figure = go.Figure()
    positions = {
        node: (
            0.5 + 0.42 * math.cos(2 * math.pi * i / max(len(nodes), 1)),
            0.5 + 0.42 * math.sin(2 * math.pi * i / max(len(nodes), 1)),
        )
        for i, node in enumerate(nodes)
    }
    for subject, object_, relation in edges:
        x0, y0 = positions[subject]
        x1, y1 = positions[object_]
        figure.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None], mode="lines",
            line={"color": "#cbd5e1", "width": 1.5}, hoverinfo="none", showlegend=False,
        ))
        figure.add_annotation(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=relation,
            showarrow=False, font={"size": 10, "color": "#64748b"},
            bgcolor="rgba(255,255,255,.8)",
        )
    figure.add_trace(go.Scatter(
        x=[positions[node][0] for node in nodes],
        y=[positions[node][1] for node in nodes],
        mode="markers+text", text=nodes, textposition="top center",
        marker={"size": 24, "color": ["#f97316" if node == festival else "#2563eb" for node in nodes], "line": {"width": 2, "color": "white"}},
        hovertemplate="%{text}<extra></extra>", showlegend=False,
    ))
    figure.update_layout(
        height=420, margin={"l": 0, "r": 0, "t": 20, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248,250,252,.8)",
        xaxis={"visible": False, "range": [0, 1]}, yaxis={"visible": False, "range": [0, 1]},
    )
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def _format_date(value: Any) -> str:
    """20260515 -> 2026.05.15"""

    value = str(value or "").replace("-", "")

    if len(value) >= 8 and value[:8].isdigit():
        return f"{value[:4]}.{value[4:6]}.{value[6:8]}"

    return value or "-"


def _festival_programs(row: dict[str, Any], metadata: dict[str, Any]) -> str:
    """프로그램 필드가 없으면 축제 설명에 포함된 프로그램 구간을 사용합니다."""
    programs = row.get("programs") or row.get("program") or metadata.get("programs") or metadata.get("program")
    if programs:
        return str(programs)

    description = festival_text(row)
    sections = [section.strip() for section in description.split("\n\n") if section.strip()]
    for section in sections[1:]:
        if "프로그램" in section or section.lstrip().startswith(("1.", "1)")):
            return section.replace("\u200b", "")
    # 별도 프로그램 제목이 없는 축제는 두 번째 설명 문단의 활동 목록을 사용합니다.
    if len(sections) > 1:
        fallback = sections[1].replace("\u200b", "")
        fallback = re.split(r"\*\s*이용요금", fallback, maxsplit=1)[0].strip()
        if fallback:
            return fallback
    return ""


def _festival_description(row: dict[str, Any]) -> str:
    """프로그램 목록을 제외한 축제 소개 문단만 반환합니다."""
    description = festival_text(row).replace("\u200b", "")
    sections = [section.strip() for section in description.split("\n\n") if section.strip()]
    if len(sections) > 1 and any(
        "이용요금" in section or
        "프로그램" in section or section.lstrip().startswith(("1.", "1)"))
        for section in sections[1:]
    ):
        return sections[0]
    return description


def _format_programs(programs: str) -> str:
    """번호가 붙은 프로그램 항목을 줄 단위로 정리합니다."""
    formatted = programs.replace("\u200b", "")
    # 날짜(예: 9. 30.(수), 10.25.(일))는 번호로 오인하지 않고,
    # 번호 뒤에 실제 한글/영문 항목명이 시작되는 경우만 줄바꿈합니다.
    formatted = re.sub(r"\s+(?=\d+\.\s+[가-힣A-Za-z])", "\n", formatted)
    return formatted.strip()


def _list_items(value: str) -> list[str]:
    """하이픈/줄바꿈으로 이어진 문자열을 읽기 쉬운 항목 목록으로 만듭니다."""
    items: list[str] = []
    for line in value.replace("\u200b", "").splitlines():
        parts = re.split(r"\s*-\s*(?=[가-힣A-Za-z])", line.strip())
        items.extend(part.strip(" -") for part in parts if part.strip(" -"))
    return items


def _list_markup(value: str) -> str:
    items = _list_items(value)
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _program_markup(programs: str) -> str:
    """번호가 있는 프로그램 제목은 굵게, 세부 내용은 일반체로 표시합니다."""
    lines = _format_programs(programs).splitlines()
    cards: list[tuple[str, list[str]]] = []
    current_heading = ""
    current_items: list[str] = []

    def flush() -> None:
        if current_heading:
            cards.append((current_heading, current_items.copy()))

    for line in lines:
        line = line.strip(" -")
        if not line:
            continue
        numbered = re.match(r"^(\d+\.\s*)(.*)$", line)
        if numbered:
            flush()
            number, body = numbered.groups()
            parts = re.split(r"\s+-\s+(?=[가-힣A-Za-z])", body, maxsplit=1)
            current_heading = number + parts[0]
            current_items = []
            if len(parts) == 2:
                current_items.extend(_list_items(parts[1]))
        elif current_heading:
            current_items.append(line)
    flush()

    rendered = []
    for heading, items in cards:
        subitems = "".join(f'<div class="program-subitem">{escape(item)}</div>' for item in items)
        rendered.append(
            f'<div class="program-item-card"><div class="program-heading">{escape(heading)}</div>{subitems}</div>'
        )
    if not rendered:
        fallback_items = [item.strip() for item in re.split(r",\s*", programs) if item.strip()]
        rendered.append(
            '<div class="program-item-card">'
            + "".join(f'<div class="program-subitem">{escape(item)}</div>' for item in fallback_items)
            + '</div>'
        )
    return '<div class="program-grid">' + "".join(rendered) + "</div>"


def _render_map_plotly(st: Any, data: dict[str, Any]) -> None:
    """전국 축제 탐색 지도 페이지."""

    st.title("🗺️ 놀러갈지도")
    st.caption("지역과 기간을 선택하면 해당 축제만 지도에 표시됩니다.")

    festivals = data.get("festivals", [])

    if not festivals:
        empty_state(st)
        return

    # ---------------------------------------------------------
    # 전체 레이아웃
    # ---------------------------------------------------------
    filter_col, map_col = st.columns([1, 3])

    # ---------------------------------------------------------
    # 왼쪽 검색 필터
    # ---------------------------------------------------------
    with filter_col:
        st.subheader("🔎 검색 필터")

        regions = sorted(
            {
                _festival_region(row)
                for row in festivals
                if _festival_region(row) != "미분류"
            }
        )

        selected_region = st.selectbox(
            "지역",
            ["전체"] + regions,
            key="map_region",
        )

        selected_month = st.selectbox(
            "기간",
            ["전체"] + [f"{month}월" for month in range(1, 13)],
            key="map_month",
        )

        filtered = festivals

        if selected_region != "전체":
            filtered = [
                row
                for row in filtered
                if _festival_region(row) == selected_region
            ]

        if selected_month != "전체":
            month_number = int(
                selected_month.replace("월", "")
            )

            filtered = [
                row
                for row in filtered
                if month_number in _event_months(row)
            ]

        st.divider()

        st.metric(
            "검색 결과",
            f"{len(filtered)}개",
        )

        if filtered:
            for row in filtered[:3]:
                name = festival_name(row)
                region = _festival_region(row)

                st.markdown(
                    f"""
                    **{name}**  
                    📍 {region}
                    """
                )

            if len(filtered) > 3:
                st.caption(
                    f"외 {len(filtered) - 3}개"
                )

        else:
            st.info(
                "조건에 맞는 축제가 없습니다."
            )

    # ---------------------------------------------------------
    # 오른쪽 지도
    # ---------------------------------------------------------
    with map_col:
        coordinates = []

        for index, row in enumerate(filtered):
            lat = (
                _value(row, "latitude")
                or _value(row, "lat")
            )

            lon = (
                _value(row, "longitude")
                or _value(row, "lon")
            )

            try:
                lat = float(lat)
                lon = float(lon)
            except (TypeError, ValueError):
                continue

            coordinates.append(
                {
                    "index": index,
                    "row": row,
                    "lat": lat,
                    "lon": lon,
                    "name": festival_name(row),
                    "region": _festival_region(row),
                }
            )

        if not coordinates:
            st.info(
                "현재 조건에서 지도에 표시할 좌표가 없습니다."
            )
            return

        # -----------------------------------------------------
        # 대한민국 지도 범위
        # -----------------------------------------------------
        min_lon = 124.5
        max_lon = 131.0
        min_lat = 33.0
        max_lat = 38.8

        def lon_to_x(lon: float) -> float:
            return (
                (lon - min_lon)
                / (max_lon - min_lon)
            )

        def lat_to_y(lat: float) -> float:
            return (
                (lat - min_lat)
                / (max_lat - min_lat)
            )

        x_values = [
            lon_to_x(item["lon"])
            for item in coordinates
        ]

        y_values = [
            lat_to_y(item["lat"])
            for item in coordinates
        ]

        custom_data = [
            [
                item["index"],
                item["region"],
                _format_date(
                    _value(
                        item["row"],
                        "event_start",
                    )
                ),
                _format_date(
                    _value(
                        item["row"],
                        "event_end",
                    )
                ),
            ]
            for item in coordinates
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scattergeo(
                lat=[item["lat"] for item in coordinates],
                lon=[item["lon"] for item in coordinates],
                mode="markers",
                text=[
                    item["name"]
                    for item in coordinates
                ],
                customdata=custom_data,
                marker=dict(
                    symbol="circle",
                    size=9,
                    line=dict(
                        width=2,
                        color="#ffffff",
                    ),
                    color="#ff5b7f",
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "지역: %{customdata[1]}<br>"
                    "기간: "
                    "%{customdata[2]} "
                    "~ %{customdata[3]}"
                    "<extra></extra>"
                ),
            )
        )
        region_labels = {
            "서울": (37.57, 126.98), "인천": (37.46, 126.70), "경기": (37.30, 127.20),
            "강원": (37.75, 128.30), "충북": (36.80, 127.70), "충남": (36.55, 126.80),
            "전북": (35.75, 127.15), "전남": (34.85, 127.00), "경북": (36.35, 128.90),
            "경남": (35.35, 128.25), "제주": (33.40, 126.55),
        }
        fig.add_trace(
            go.Scattergeo(
                lat=[value[0] for value in region_labels.values()],
                lon=[value[1] for value in region_labels.values()],
                text=list(region_labels),
                mode="text",
                textfont=dict(size=11, color="#557080"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        fig.update_layout(
            height=720,
            margin=dict(
                l=0,
                r=0,
                t=10,
                b=0,
            ),
            showlegend=False,
            paper_bgcolor="#f4fbff",
            geo=dict(
                scope="asia",
                resolution=50,
                projection=dict(type="mercator", scale=5.2),
                center=dict(lat=36.1, lon=127.8),
                showland=True,
                landcolor="#fff4d6",
                showocean=True,
                oceancolor="#c9eff7",
                showlakes=True,
                lakecolor="#b7e7f2",
                showcountries=True,
                countrycolor="#f2a6b8",
                coastlinecolor="#78bdd0",
                showframe=False,
            ),
        )

        # -----------------------------------------------------
        # 클릭 가능한 Plotly 지도
        # -----------------------------------------------------
        event = st.plotly_chart(
            fig,
            use_container_width=True,
            key="festival_illustration_map",
            on_select="rerun",
            selection_mode="points",
        )

        selected_index = None

        try:
            points = event.selection.points

            if points:
                selected_index = int(
                    points[0]["customdata"][0]
                )

        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ):
            pass

        # 클릭 전에는 첫 번째 축제를 기본 선택
        if (
            selected_index is None
            and filtered
        ):
            selected_index = 0

        # -----------------------------------------------------
        # 선택 축제 카드
        # -----------------------------------------------------
        if (
            selected_index is not None
            and selected_index < len(filtered)
        ):
            selected = filtered[
                selected_index
            ]

            st.divider()

            card_left, card_right = (
                st.columns([1, 2])
            )

            image_url = _festival_image(
                selected
            )

            with card_left:
                if image_url:
                    st.image(
                        image_url,
                        use_container_width=True,
                    )

                else:
                    st.markdown(
                        """
                        <div style="
                            height:180px;
                            border-radius:14px;
                            background:#f1f3f5;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:46px;">
                            🎪
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with card_right:
                st.subheader(
                    festival_name(selected)
                )

                region = _festival_region(
                    selected
                )

                start = _format_date(
                    _value(
                        selected,
                        "event_start",
                    )
                )

                end = _format_date(
                    _value(
                        selected,
                        "event_end",
                    )
                )

                place = (
                    _value(
                        selected,
                        "eventplace",
                    )
                    or _value(
                        selected,
                        "address",
                    )
                    or "-"
                )

                fee = (
                    _value(
                        selected,
                        "usetimefestival",
                    )
                    or "-"
                )

                st.write(
                    f"📍 **지역** · {region}"
                )

                st.write(
                    f"📅 **기간** · "
                    f"{start} ~ {end}"
                )

                st.write(
                    f"🏛️ **장소** · {place}"
                )

                st.write(
                    f"💰 **요금** · {fee}"
                )

                homepage = _value(
                    selected,
                    "homepage",
                )

                if homepage:
                    st.link_button(
                        "공식 홈페이지",
                        str(homepage),
                        use_container_width=True,
                    )

                if st.button(
                    "상세보기 →",
                    use_container_width=True,
                    key=(
                        f"map-detail-"
                        f"{selected_index}"
                    ),
                ):
                    st.session_state[
                        "selected_festival"
                    ] = selected

                    st.session_state[
                        "page"
                    ] = "detail"

                    st.rerun()

        # -----------------------------------------------------
        # 아래 미리보기 카드
        # -----------------------------------------------------
        st.subheader(
            "지역별 축제 미리보기"
        )

        for i, row in enumerate(
            filtered[:3]
        ):
            festival_card(
                st,
                row,
                f"map-{i}",
                lambda selected: festival_detail_callback(st, selected),
            )


def _kakao_api_key(st: Any) -> str:
    load_dotenv()
    secrets = getattr(st, "secrets", {})
    names = ("KAKAO_MAP_API_KEY", "KAKAO_API_KEY", "KAKAO_JAVASCRIPT_KEY", "KAKAO_MAP_KEY")
    for name in names:
        value = os.getenv(name)
        if not value and hasattr(secrets, "get"):
            value = secrets.get(name)
        if value:
            return str(value).strip()
    return ""


def _render_kakao_map(st: Any, points: list[dict[str, Any]], api_key: str) -> None:
    payload = json.dumps(points, ensure_ascii=False).replace("</", "<\\/")
    key_json = json.dumps(api_key)
    html = f"""
    <div id="festival-map" style="width:100%;height:650px;border-radius:18px;overflow:hidden;"></div>
    <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={api_key}&autoload=false"></script>
    <script>
      const points = {payload};
      kakao.maps.load(function() {{
        const map = new kakao.maps.Map(document.getElementById('festival-map'), {{
          center: new kakao.maps.LatLng(36.35, 127.8), level: 13
        }});
        const bounds = new kakao.maps.LatLngBounds();
        points.forEach(function(point) {{
          const position = new kakao.maps.LatLng(point.lat, point.lon);
          const marker = new kakao.maps.Marker({{ map: map, position: position }});
          const info = new kakao.maps.InfoWindow({{
            content: '<div style="padding:8px 12px;font-size:13px;white-space:nowrap;"><b>' + point.name + '</b><br>' + point.region + '</div>'
          }});
          kakao.maps.event.addListener(marker, 'click', function() {{ info.open(map, marker); }});
          bounds.extend(position);
        }});
        if (points.length > 0) map.setBounds(bounds);
      }});
    </script>
    """
    components.html(html, height=670, scrolling=False)


def render_map(st: Any, data: dict[str, Any]) -> None:
    """Render the map with Streamlit's native geographic map component."""
    st.title("🗺️ 놀러갈지도")
    st.caption("\uc9c0\uc5ed\uacfc \uae30\uac04\uc744 \uc120\ud0dd\ud558\uba74 \ud574\ub2f9 \ucd95\uc81c\ub9cc \uc9c0\ub3c4\uc5d0 \ud45c\uc2dc\ub429\ub2c8\ub2e4.")

    festivals = data.get("festivals", [])
    if not festivals:
        return empty_state(st)

    regions = sorted({_festival_region(row) for row in festivals})
    filter_panel, map_panel = st.columns([1, 3], gap="large")
    with filter_panel:
        st.subheader("\uac80\uc0c9 \ud544\ud130")
        selected_region = st.selectbox(
            "\uc9c0\uc5ed", ["\uc804\uccb4", *regions], key="native_map_region"
        )
        selected_month = st.selectbox(
            "\uae30\uac04",
            ["\uc804\uccb4", *[f"{month}\uc6d4" for month in range(1, 13)]],
            key="native_map_month",
        )

    filtered = festivals
    if selected_region != "\uc804\uccb4":
        filtered = [row for row in filtered if _festival_region(row) == selected_region]
    if selected_month != "\uc804\uccb4":
        month_number = int(selected_month.removesuffix("\uc6d4"))
        filtered = [row for row in filtered if month_number in _event_months(row)]

    points = []
    for filtered_index, row in enumerate(filtered):
        try:
            latitude = float(_value(row, "latitude"))
            longitude = float(_value(row, "longitude"))
        except (TypeError, ValueError):
            continue
        # Ignore malformed source coordinates that would make st.map zoom
        # out to a world view instead of the Korean peninsula.
        if not (32.0 <= latitude <= 39.5 and 123.0 <= longitude <= 132.0):
            continue
        points.append({
            "lat": latitude,
            "lon": longitude,
            "name": festival_name(row),
            "region": _festival_region(row),
            "filtered_index": filtered_index,
        })

    with filter_panel:
        st.metric("\ud45c\uc2dc \ucd95\uc81c", f"{len(filtered)}\uac1c")

    if points:
        kakao_key = _kakao_api_key(st)
        if kakao_key:
            _render_kakao_map(st, points, kakao_key)
            return
        deck = pdk.Deck(
            # 밝은 Voyager 지도를 사용해 회색 기본 배경을 피합니다.
            map_style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
            initial_view_state=pdk.ViewState(
                latitude=36.35,
                longitude=127.8,
                zoom=6.7,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    id="festival-points",
                    data=points,
                    get_position="[lon, lat]",
                    get_radius=1000,
                    get_fill_color=[235, 84, 102, 220],
                    get_line_color=[255, 255, 255, 255],
                    line_width_min_pixels=2,
                    pickable=True,
                    auto_highlight=True,
                )
            ],
            tooltip={
                "html": "<b>{name}</b><br/>지역: {region}",
                "style": {
                    "backgroundColor": "#182942",
                    "color": "white",
                    "fontSize": "14px",
                },
            },
        )
        selection = map_panel.pydeck_chart(
            deck,
            height=650,
            width="stretch",
            on_select="rerun",
            selection_mode="single-object",
            key="festival_native_map",
        )
        selected = None
        try:
            selection_data = selection.selection
            selected_objects_by_layer = getattr(selection_data, "objects", {}) or {}
            selected_objects = selected_objects_by_layer.get("festival-points", [])
            if selected_objects:
                selected_index = int(selected_objects[0]["filtered_index"])
                selected = filtered[selected_index]
            else:
                selected_indices_by_layer = getattr(selection_data, "indices", {}) or {}
                selected_indices = selected_indices_by_layer.get("festival-points", [])
                if selected_indices:
                    selected = filtered[points[selected_indices[0]]["filtered_index"]]
        except (AttributeError, KeyError, IndexError, TypeError, ValueError):
            selected = None
        if selected is not None:
            st.session_state["selected_festival"] = selected
            st.session_state["page"] = "\ucd95\uc81c \uc0c1\uc138"
            st.rerun()
    else:
        map_panel.info("\uc120\ud0dd\ud55c \uc870\uac74\uc5d0 \ub9de\ub294 \uc88c\ud45c \ub370\uc774\ud130\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.")

    st.subheader("\ucd95\uc81c \ubbf8\ub9ac\ubcf4\uae30")
    preview_cols = st.columns(min(3, len(filtered))) if filtered else []
    for column, (index, row) in zip(preview_cols, enumerate(filtered[:3])):
        with column:
            festival_card(
                st,
                row,
                f"native-map-{index}",
                lambda selected: festival_detail_callback(st, selected),
            )


def render_detail(
    st: Any,
    row: dict[str, Any],
    triples: list[dict[str, Any]],
) -> None:
    """축제 상세 페이지."""

    st.markdown(
        """
        <style>
        :root {
            --festival-navy: #17324d;
            --festival-blue: #2f6f9f;
            --festival-mint: #e8f4f1;
            --festival-peach: #fff1e6;
            --festival-line: #dbe5ec;
            --festival-muted: #64748b;
        }
        .detail-section-title {
            color: var(--festival-navy);
            font-size: 1.4rem;
            font-weight: 750;
            margin: 1.5rem 0 .75rem;
            letter-spacing: -.02em;
        }
        .festival-hero {
            padding: 1.35rem 1.6rem;
            border-radius: 18px;
            min-height: 104px;
            display: flex;
            align-items: center;
            border: 1px solid #d7e4ed;
            border-left: 8px solid #2f6f9f;
            color: var(--festival-navy);
            background: linear-gradient(105deg, #ffffff 0%, #f2f8fb 100%);
            box-shadow: 0 10px 24px rgba(23, 50, 77, .08);
        }
        .festival-image {
            width: 100%;
            height: 430px;
            object-fit: cover;
            border-radius: 18px;
            margin-bottom: 0;
            box-shadow: 0 12px 30px rgba(18, 59, 99, .16);
        }
        .image-panel { height: 430px; border-radius: 18px; overflow: hidden; }
        .festival-hero h1 { margin: 0; font-size: 1.9rem; line-height: 1.35; letter-spacing: -.035em; }
        .festival-hero-content { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
        .festival-hero-kicker { color: #2f6f9f; font-size: .78rem; font-weight: 800; letter-spacing: .14em; margin-bottom: .35rem; }
        .festival-hero-title { min-width: 0; }
        .hero-link { display: inline-block; padding: .65rem .85rem; border: 1px solid #b9d2e2; border-radius: 10px; color: var(--festival-blue); background: white; font-size: .9rem; font-weight: 700; text-decoration: none; }
        .detail-card {
            padding: 1rem 1.1rem;
            border: 1px solid var(--festival-line);
            border-radius: 16px;
            height: 7.2rem;
            box-sizing: border-box;
            margin-bottom: .75rem;
            background: white;
            box-shadow: 0 4px 14px rgba(23, 50, 77, .05);
        }
        .detail-label { color: var(--festival-muted); font-size: 1.15rem !important; font-weight: 700; line-height: 1.5; margin-bottom: .4rem; }
        .detail-value { color: var(--festival-navy); font-size: 1.15rem !important; font-weight: 700; line-height: 1.5; }
        .detail-value.scrollable { max-height: 4.1rem; overflow-y: auto; padding-right: .35rem; }
        .detail-value ul, .program-card ul { margin: 0; padding-left: 1.25rem; }
        .detail-value li, .program-card li { margin: .25rem 0; color: var(--festival-navy); font-size: 1.15rem !important; font-weight: 700 !important; line-height: 1.5; }
        .program-heading { color: #4a3426; font-size: 1.15rem; font-weight: 750; line-height: 1.6; margin-top: .55rem; }
        .program-subitem { color: #4a3426; font-size: 1.1rem; font-weight: 400; line-height: 1.6; padding-left: 1.25rem; }
        .description-card {
            padding: 1.25rem 1.4rem;
            border: 1px solid #cce4df;
            border-radius: 16px;
            color: #334155;
            font-size: 1.05rem;
            line-height: 1.8;
            background: var(--festival-mint);
            box-shadow: 0 4px 14px rgba(32, 100, 90, .05);
        }
        .program-card {
            padding: 1.1rem 1.3rem;
            border: 1px solid #f3d4bd;
            border-radius: 16px;
            color: #4a3426;
            font-size: 1.05rem;
            line-height: 1.75;
            background: var(--festival-peach);
            max-height: 38rem;
            overflow-y: auto;
        }
        .program-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; align-items: start; }
        .program-item-card { align-self: start; padding: 1.1rem 1.2rem; border: 1px solid #f1c9a8; border-radius: 13px; background: rgba(255,255,255,.42); }
        .program-heading { color: #4a3426; font-size: 1.05rem; font-weight: 750; line-height: 1.5; margin: 0; }
        .program-subitem { color: #4a3426; font-size: 1rem; font-weight: 400; line-height: 1.55; padding-left: 1rem; margin-top: .55rem; }
        @media (max-width: 760px) { .program-grid { grid-template-columns: 1fr; } }
        .nearby-image {
            width: 132px; height: 132px; object-fit: cover;
            border-radius: 12px; display: block; flex: 0 0 132px;
        }
        .nearby-card {
            border: 1px solid var(--festival-line);
            border-radius: 16px;
            padding: .8rem; margin-bottom: 1rem;
            background: white; min-height: 148px;
            box-shadow: 0 4px 14px rgba(23, 50, 77, .05);
            display: flex; align-items: stretch; gap: .9rem;
        }
        .nearby-placeholder { width: 132px; height: 132px; flex: 0 0 132px; display: flex; align-items: center; justify-content: center; border-radius: 12px; background: linear-gradient(135deg, #e8f4f1, #fff1e6); font-size: 2.2rem; }
        .nearby-copy { display: flex; flex-direction: column; justify-content: center; min-width: 0; }
        .nearby-title { font-size: 1.1rem; font-weight: 750; margin-bottom: .4rem; color: var(--festival-navy); }
        .nearby-distance { color: #e56b32; font-size: .95rem; font-weight: 700; }
        .nearby-address { color: var(--festival-muted); font-size: .95rem; margin-top: .45rem; line-height: 1.45; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("축제 상세정보")

    image_url = _festival_image(row)
    fallback_uri = _fallback_image_uri()
    image_src = escape(image_url or fallback_uri, quote=True)
    image_fallback = escape(fallback_uri, quote=True)
    image_alt = escape(festival_name(row), quote=True)
    homepage = _value(row, "homepage")
    homepage_link = (
        f'<a class="hero-link" href="{escape(str(homepage), quote=True)}" target="_blank">🔗 공식 홈페이지</a>'
        if homepage else ""
    )

    st.markdown(
        f'<div class="festival-hero"><div class="festival-hero-content"><div class="festival-hero-title"><div class="festival-hero-kicker">FESTIVAL DETAIL</div><h1>{image_alt}</h1></div>{homepage_link}</div></div>',
        unsafe_allow_html=True,
    )

    metadata = _meta(row)

    st.divider()

    # ---------------------------------------------------------
    # 기본 정보
    # ---------------------------------------------------------
    info_col, image_col = st.columns([1, 1], gap="large")

    event_start = _format_date(
        _value(
            row,
            "event_start",
        )
    )

    event_end = _format_date(
        _value(
            row,
            "event_end",
        )
    )

    eventplace = (
        _value(
            row,
            "eventplace",
        )
        or "-"
    )

    address = (
        _value(
            row,
            "address",
        )
        or "-"
    )

    playtime = (
        _value(
            row,
            "playtime",
        )
        or "-"
    )

    fee = (
        _value(
            row,
            "usetimefestival",
        )
        or "-"
    )

    sponsor1 = (
        _value(
            row,
            "sponsor1",
        )
        or "-"
    )

    with info_col:
        st.markdown('<div class="detail-section-title">📌 기본 정보</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="medium")

        with c1:
            st.markdown(f'<div class="detail-card"><div class="detail-label">📅 행사 기간</div><div class="detail-value">{event_start} ~ {event_end}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-card"><div class="detail-label">📍 행사 장소</div><div class="detail-value scrollable">{escape(eventplace)}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-card"><div class="detail-label">🏠 주소</div><div class="detail-value scrollable">{escape(address)}</div></div>', unsafe_allow_html=True)

        with c2:
            st.markdown(f'<div class="detail-card"><div class="detail-label">🕐 운영시간</div><div class="detail-value">{playtime}</div></div>', unsafe_allow_html=True)
            fee_content = _list_markup(fee) if fee != "-" else "-"
            st.markdown(f'<div class="detail-card"><div class="detail-label">💰 이용요금</div><div class="detail-value scrollable">{fee_content}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-card"><div class="detail-label">🏢 주최</div><div class="detail-value">{sponsor1}</div></div>', unsafe_allow_html=True)

    with image_col:
        st.markdown(
            f'<div class="image-panel"><img class="festival-image" src="{image_src}" '
            f'onerror="this.onerror=null;this.src=\'{image_fallback}\';" '
            f'alt="{image_alt} 대표 이미지"></div>',
            unsafe_allow_html=True,
        )

    description = _festival_description(row)
    if description:
        st.markdown('<div class="detail-section-title">📝 축제 소개</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="description-card">{escape(description).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown('<div class="detail-section-title">🎪 주요 프로그램</div>', unsafe_allow_html=True)

    programs = _festival_programs(row, metadata)

    if programs:
        st.markdown(
            f'<div class="program-card">{_program_markup(str(programs))}</div>',
            unsafe_allow_html=True,
        )

    else:
        st.markdown('<div class="program-card">프로그램 정보 준비 중</div>', unsafe_allow_html=True)

    st.markdown('<div class="detail-section-title">📍 근처 장소 추천</div>', unsafe_allow_html=True)

    nearby = load_json(
        "data/extra/festival_nearby_5km.json",
        [],
    )

    if isinstance(nearby, dict):
        nearby = nearby.get(
            "items",
            nearby.get(
                "data",
                [],
            ),
        )

    festival_id = str(row.get("doc_id") or _value(row, "contentid"))
    nearby_groups = [
        group for group in nearby if isinstance(group, dict)
        and str(group.get("festival_contentid")) == festival_id
    ] if isinstance(nearby, list) else []
    nearby_items = nearby_groups[0].get("nearby", []) if nearby_groups else []

    if nearby_items:
        cards = nearby_items[:6]
        columns = st.columns(2, gap="medium")
        for index, item in enumerate(cards):
            with columns[index % 2]:
                title = str(item.get("title") or "이름 없는 장소")
                address = str(item.get("addr1") or "주소 정보 없음")
                distance = item.get("dist")
                distance_text = f"약 {float(distance):.0f}m" if distance else "주변 장소"
                nearby_image = item.get("firstimage") or item.get("firstimage2")
                media = (
                    f'<img class="nearby-image" src="{escape(str(nearby_image), quote=True)}" alt="{escape(title, quote=True)}">'
                    if nearby_image else '<div class="nearby-placeholder">📍</div>'
                )
                st.markdown(
                    f'<div class="nearby-card">{media}<div class="nearby-copy">'
                    f'<div class="nearby-title">{escape(title)}</div>'
                    f'<div class="nearby-distance">{escape(distance_text)}</div>'
                    f'<div class="nearby-address">{escape(address)}</div></div></div>',
                    unsafe_allow_html=True,
                )

    else:
        st.info("연결된 주변 관광지 정보가 없습니다.")
