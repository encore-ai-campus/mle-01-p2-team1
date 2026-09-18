"""Owner 2: map, preview carousel, and festival detail page."""
from __future__ import annotations

from typing import Any
from .components import empty_state, festival_card, festival_detail_callback
from .data_loader import festival_name, festival_text


def render_map(st: Any, data: dict[str, Any]) -> None:
    st.title("🗺️ 축제 지도")
    regions = ["전체"] + sorted({str(r.get("region") or r.get("location") or "미분류") for r in data["festivals"]})
    c1, c2 = st.columns(2)
    region = c1.selectbox("지역", regions)
    month = c2.selectbox("기간(월)", ["전체"] + [str(i) for i in range(1, 13)])
    rows = data["festivals"]
    if region != "전체": rows = [r for r in rows if region in str(r)]
    if month != "전체": rows = [r for r in rows if month in str(r.get("date") or r.get("period") or "")]
    # TODO(지도 담당): 위도·경도 필드명을 확정하고 st.map 사용으로 전환합니다.
    coordinates = []
    for r in rows:
        lat, lon = r.get("lat", r.get("latitude")), r.get("lon", r.get("longitude"))
        try:
            if lat is not None and lon is not None:
                coordinates.append({"lat": float(lat), "lon": float(lon)})
        except (TypeError, ValueError):
            continue
    coordinates = [r for r in coordinates if r["lat"] is not None and r["lon"] is not None]
    if coordinates: st.map(coordinates, latitude="lat", longitude="lon")
    else: st.info("좌표가 있는 축제 데이터가 아직 없습니다. 아래 목록에서 확인하세요.")
    if not rows: return empty_state(st)
    st.subheader("지역별 축제 미리보기")
    for i, row in enumerate(rows[:3]):
        festival_card(st, row, f"map-{i}", lambda selected: festival_detail_callback(st, selected))


def render_detail(st: Any, row: dict[str, Any], triples: list[dict[str, Any]]) -> None:
    st.title(festival_name(row))
    st.write(festival_text(row) or "상세 설명 준비 중")
    st.subheader("메타데이터")
    st.json(row)
    st.subheader("주요 프로그램")
    st.info(str(row.get("programs") or row.get("program") or "프로그램 정보 준비 중"))
    st.subheader("지식그래프")
    st.dataframe(triples[:20], use_container_width=True)
    st.subheader("근처 볼 거리")
    # TODO(상세 담당): 대표 축제 ID를 기준으로 주변 관광지 데이터를 연결합니다.
    from .data_loader import load_json
    nearby = load_json("data/extra/festival_nearby_5km.json", [])
    if isinstance(nearby, dict): nearby = nearby.get("items", nearby.get("data", []))
    if nearby: st.dataframe(nearby[:10], use_container_width=True)
    else: st.info("주변 관광지 정보가 없습니다.")
