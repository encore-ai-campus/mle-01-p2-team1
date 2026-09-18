"""Small presentational helpers shared by Streamlit page modules."""
from __future__ import annotations

from typing import Any


def metric_row(st: Any, values: dict[str, Any]) -> None:
    cols = st.columns(len(values))
    for col, (label, value) in zip(cols, values.items()):
        col.metric(label, value)


def empty_state(st: Any, message: str = "표시할 데이터가 없습니다.") -> None:
    st.info(message)


def festival_card(st: Any, row: dict[str, Any], key: str) -> bool:
    from .data_loader import festival_name, festival_text
    with st.container(border=True):
        st.subheader(festival_name(row))
        st.caption(festival_text(row)[:180] or "상세 설명 준비 중")
        # TODO(공통 UI 담당): 타입이 지정된 상세 페이지 이동 콜백으로 교체합니다.
        # 현재는 선택 축제를 세션에 저장하는 공통 라우팅 구현을 사용합니다.
        clicked = st.button("상세 보기", key=key)
        if clicked:
            st.session_state["selected_festival"] = row
            st.session_state["page"] = "축제 상세"
            st.rerun()
        return clicked
