"""Small presentational helpers shared by Streamlit page modules."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


FestivalDetailCallback = Callable[[dict[str, Any]], None]


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
    with st.container(border=True):
        st.subheader(festival_name(row))
        st.caption(festival_text(row)[:180] or "상세 설명 준비 중")
        clicked = st.button("상세 보기", key=key)
        if clicked:
            on_detail(row)
        return clicked
