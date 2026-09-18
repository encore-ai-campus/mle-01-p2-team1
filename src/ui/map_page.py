"""Owner 2: map, preview carousel, and festival detail page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    value = row.get(key)

    if value not in (None, ""):
        return value

    return _meta(row).get(key, default)


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


def _format_date(value: Any) -> str:
    """20260515 -> 2026.05.15"""

    value = str(value or "").replace("-", "")

    if len(value) >= 8 and value[:8].isdigit():
        return f"{value[:4]}.{value[4:6]}.{value[6:8]}"

    return value or "-"


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

    st.title(
        festival_name(row)
    )

    description = festival_text(row)

    st.write(
        description
        or "상세 설명 준비 중"
    )

    metadata = _meta(row)

    st.divider()

    # ---------------------------------------------------------
    # 대표 이미지
    # ---------------------------------------------------------
    image_url = _festival_image(row)

    if image_url:
        st.image(
            image_url,
            use_container_width=True,
        )

    # ---------------------------------------------------------
    # 기본 정보
    # ---------------------------------------------------------
    st.subheader("📌 기본 정보")

    c1, c2 = st.columns(2)

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

    with c1:
        st.write(
            f"📅 **기간**: "
            f"{event_start} ~ {event_end}"
        )

        st.write(
            f"📍 **장소**: {eventplace}"
        )

        st.write(
            f"🏠 **주소**: {address}"
        )

    with c2:
        st.write(
            f"🕐 **운영시간**: "
            f"{playtime}"
        )

        st.write(
            f"💰 **이용요금**: {fee}"
        )

        st.write(
            f"🏢 **주최**: {sponsor1}"
        )

        homepage = _value(
            row,
            "homepage",
        )

        if homepage:
            st.link_button(
                "🔗 공식 홈페이지",
                str(homepage),
            )

    st.divider()

    # ---------------------------------------------------------
    # 주요 프로그램
    # ---------------------------------------------------------
    st.subheader("🎪 주요 프로그램")

    programs = (
        row.get("programs")
        or row.get("program")
        or metadata.get("programs")
        or metadata.get("program")
    )

    if programs:
        st.info(
            str(programs)
        )

    else:
        st.info(
            "프로그램 정보 준비 중"
        )

    # ---------------------------------------------------------
    # 지식그래프
    # ---------------------------------------------------------
    st.subheader("🕸️ 지식그래프")

    if triples:
        st.dataframe(
            triples[:20],
            use_container_width=True,
        )

    else:
        st.info(
            "연결된 지식그래프 정보가 없습니다."
        )

    # ---------------------------------------------------------
    # 근처 볼거리
    # ---------------------------------------------------------
    st.subheader("📍 근처 볼거리")

    nearby = load_json(
        "data/extra/festival_nearby_5km.json",
        [],
    )

    if isinstance(
        nearby,
        dict,
    ):
        nearby = nearby.get(
            "items",
            nearby.get(
                "data",
                [],
            ),
        )

    if nearby:
        st.dataframe(
            nearby[:10],
            use_container_width=True,
        )

    else:
        st.info(
            "주변 관광지 정보가 없습니다."
        )