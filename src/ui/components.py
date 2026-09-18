"""Small presentational helpers shared by Streamlit page modules."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


FestivalDetailCallback = Callable[[dict[str, Any]], None]


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    return value if isinstance(value, dict) else {}


def festival_image(row: dict[str, Any]) -> str | None:
    """Return the first usable festival image from top-level or metadata fields."""
    keys = ("firstimage", "firstimage2", "image_url", "image", "thumbnail", "thumbnail_url")
    for source in (row, _metadata(row)):
        for key in keys:
            value = source.get(key)
            if value:
                return str(value)
    return None


def format_festival_date(value: Any) -> str:
    """Format TourAPI's YYYYMMDD values for compact cards."""
    normalized = str(value or "").replace("-", "")
    if len(normalized) >= 8 and normalized[:8].isdigit():
        return f"{normalized[:4]}.{normalized[4:6]}.{normalized[6:8]}"
    return normalized or "일정 미정"


def region_label(row: dict[str, Any]) -> str:
    """Extract a short Korean province/city label from a row."""
    address = str(row.get("address") or row.get("region") or row.get("location") or _metadata(row).get("address") or "")
    mapping = {
        "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천",
        "광주광역시": "광주", "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종",
        "경기도": "경기", "강원특별자치도": "강원", "강원도": "강원", "충청북도": "충북",
        "충청남도": "충남", "전북특별자치도": "전북", "전라북도": "전북", "전라남도": "전남",
        "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주",
    }
    for full, short in mapping.items():
        if full in address:
            return short
    return address.split()[0] if address else "전국"


def metric_row(st: Any, values: dict[str, Any]) -> None:
    cols = st.columns(len(values))
    for col, (label, value) in zip(cols, values.items()):
        col.metric(label, value)


def empty_state(st: Any, message: str = "표시할 데이터가 없습니다.") -> None:
    st.info(message)


def festival_detail_callback(st: Any, row: dict[str, Any]) -> None:
    st.session_state["selected_festival"] = row
    st.session_state["page"] = "축제 상세"
    st.rerun()


def festival_card(
    st: Any,
    row: dict[str, Any],
    key: str,
    on_detail: FestivalDetailCallback,
) -> bool:
    from .data_loader import festival_name, festival_text
    image = festival_image(row)
    with st.container(border=True):
        if key.startswith("home-recommend-"):
            st.markdown('<span class="home-recommend-card-marker"></span>', unsafe_allow_html=True)
        if image:
            st.image(image, use_container_width=True)
        st.markdown(f'<div class="festival-card-region">{region_label(row)}</div>', unsafe_allow_html=True)
        st.subheader(festival_name(row))
        st.caption(festival_text(row)[:150] or "상세 설명 준비 중")
        clicked = st.button("상세 보기  →", key=key, use_container_width=True)
        if clicked:
            on_detail(row)
        return clicked
