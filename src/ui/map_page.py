"""Owner 2: map, preview carousel, and festival detail page."""

from __future__ import annotations

import base64
import math
from pathlib import Path
from typing import Any
from html import escape

import plotly.graph_objects as go
from PIL import Image

try:
    from .components import empty_state, festival_card
    from .data_loader import festival_name, festival_text, load_json
except ImportError:
    from src.ui.components import empty_state, festival_card
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
    }

    for full_name, short_name in region_map.items():
        if full_name in address:
            return short_name

    return "미분류"


def _event_months(row: dict[str, Any]) -> set[int]:
    """
    행사 시작일~종료일 사이에 포함되는 월을 반환합니다.

    예:
    20260425 ~ 20260510
    -> {4, 5}
    """

    start = str(
        _value(row, "event_start")
        or _value(row, "eventstartdate")
        or ""
    ).replace("-", "")

    end = str(
        _value(row, "event_end")
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
    return ""


def render_map(st: Any, data: dict[str, Any]) -> None:
    """전국 축제 탐색 지도 페이지."""

    st.title("🗺️ 전국 축제 탐색 — 지도로 찾기")
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
            for row in filtered[:6]:
                name = festival_name(row)
                region = _festival_region(row)

                st.markdown(
                    f"""
                    **{name}**  
                    📍 {region}
                    """
                )

            if len(filtered) > 6:
                st.caption(
                    f"외 {len(filtered) - 6}개"
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

        # -----------------------------------------------------
        # 일러스트 지도 이미지
        #
        # 프로젝트 루트 기준:
        # assets/korea_map.png
        # -----------------------------------------------------
        map_image_path = Path(
            "assets/korea_map.png"
        )

        if map_image_path.exists():
            background = Image.open(
                map_image_path
            )

            fig.add_layout_image(
                dict(
                    source=background,
                    xref="x",
                    yref="y",
                    x=0,
                    y=1,
                    sizex=1,
                    sizey=1,
                    sizing="stretch",
                    opacity=1.0,
                    layer="below",
                )
            )
        else:
            st.warning(
                "assets/korea_map.png가 없습니다. "
                "일러스트 지도를 사용하려면 해당 경로에 이미지를 넣어주세요."
            )

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="markers",
                text=[
                    item["name"]
                    for item in coordinates
                ],
                customdata=custom_data,
                marker=dict(
                    size=16,
                    line=dict(
                        width=2,
                        color="white",
                    ),
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

        fig.update_layout(
            height=720,
            margin=dict(
                l=0,
                r=0,
                t=10,
                b=0,
            ),
            showlegend=False,
            xaxis=dict(
                range=[0, 1],
                visible=False,
                fixedrange=True,
            ),
            yaxis=dict(
                range=[0, 1],
                visible=False,
                fixedrange=True,
                scaleanchor="x",
                scaleratio=1,
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
            font-size: 1.25rem;
            font-weight: 750;
            margin: 1.5rem 0 .75rem;
            letter-spacing: -.02em;
        }
        .festival-hero {
            padding: 1.15rem 1.5rem;
            border-radius: 22px;
            min-height: 88px;
            display: flex;
            align-items: center;
            border: 1px solid #cfe0eb;
            color: var(--festival-navy);
            background: #f5f9fc;
            box-shadow: 0 8px 22px rgba(23, 50, 77, .07);
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
        .festival-hero h1 { margin: 0; font-size: 1.65rem; line-height: 1.35; }
        .festival-hero-content { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
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
        .detail-label { color: var(--festival-muted); font-size: .9rem; font-weight: 650; margin-bottom: .4rem; }
        .detail-value { color: var(--festival-navy); font-size: 1.05rem; font-weight: 650; line-height: 1.5; }
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
        }
        .nearby-image {
            width: 100%; height: 108px; object-fit: cover;
            border-radius: 14px 14px 0 0; display: block;
        }
        .nearby-card {
            border: 1px solid var(--festival-line);
            border-radius: 0 0 14px 14px;
            padding: 1rem; margin-bottom: 1rem;
            background: white; min-height: 108px;
            box-shadow: 0 4px 14px rgba(23, 50, 77, .05);
        }
        .nearby-title { font-size: 1rem; font-weight: 700; margin-bottom: .35rem; }
        .nearby-distance { color: #f97316; font-size: .9rem; font-weight: 650; }
        .nearby-address { color: var(--festival-muted); font-size: .9rem; margin-top: .4rem; line-height: 1.4; }
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
        f'<div class="festival-hero"><div class="festival-hero-content"><h1>{image_alt}</h1>{homepage_link}</div></div>',
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
            st.markdown(f'<div class="detail-card"><div class="detail-label">📍 행사 장소</div><div class="detail-value">{eventplace}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-card"><div class="detail-label">🏠 주소</div><div class="detail-value">{address}</div></div>', unsafe_allow_html=True)

        with c2:
            st.markdown(f'<div class="detail-card"><div class="detail-label">🕐 운영시간</div><div class="detail-value">{playtime}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-card"><div class="detail-label">💰 이용요금</div><div class="detail-value">{fee}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-card"><div class="detail-label">🏢 주최</div><div class="detail-value">{sponsor1}</div></div>', unsafe_allow_html=True)

    with image_col:
        st.markdown(
            f'<div class="image-panel"><img class="festival-image" src="{image_src}" '
            f'onerror="this.onerror=null;this.src=\'{image_fallback}\';" '
            f'alt="{image_alt} 대표 이미지"></div>',
            unsafe_allow_html=True,
        )

    description = festival_text(row)
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
            f'<div class="program-card">{escape(str(programs)).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

    else:
        st.markdown('<div class="program-card">프로그램 정보 준비 중</div>', unsafe_allow_html=True)

    st.markdown('<div class="detail-section-title">🕸️ 지식그래프</div>', unsafe_allow_html=True)
    _render_knowledge_graph(st, triples, festival_name(row))

    st.markdown('<div class="detail-section-title">📍 근처 볼거리</div>', unsafe_allow_html=True)

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
        columns = st.columns(3)
        for index, item in enumerate(cards):
            with columns[index % 3]:
                title = str(item.get("title") or "이름 없는 장소")
                address = str(item.get("addr1") or "주소 정보 없음")
                distance = item.get("dist")
                distance_text = f"약 {float(distance):.0f}m" if distance else "주변 장소"
                nearby_image = item.get("firstimage") or item.get("firstimage2")
                if nearby_image:
                    st.markdown(
                        f'<img class="nearby-image" src="{escape(str(nearby_image), quote=True)}" '
                        f'alt="{escape(title, quote=True)}">',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div class="nearby-card"><div class="nearby-title">{escape(title)}</div>'
                    f'<div class="nearby-distance">{escape(distance_text)}</div>'
                    f'<div class="nearby-address">{escape(address)}</div></div>',
                    unsafe_allow_html=True,
                )

    else:
        st.info("연결된 주변 관광지 정보가 없습니다.")
