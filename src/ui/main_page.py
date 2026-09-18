"""Owner 1: home dashboard and recommendation page."""
from __future__ import annotations

from typing import Any
from .components import empty_state, festival_card, festival_detail_callback, metric_row
from .data_loader import festival_name


def render_home(st: Any, data: dict[str, Any]) -> None:
    st.title("🎪 우리 동네 축제 탐색")
    query = st.text_input("축제 검색", placeholder="축제명, 지역, 테마를 검색해보세요")
    metric_row(st, {"총 축제 개수": len(data["festivals"]), "지식그래프 관계 수": len(data["triples"])})
    if query:
        matches = [r for r in data["festivals"] if query.lower() in str(r).lower()]
        st.subheader("검색 결과")
        for i, row in enumerate(matches[:10]):
            festival_card(st, row, f"home-{i}", lambda selected: festival_detail_callback(st, selected))
    st.caption("왼쪽 메뉴에서 추천, 지도, 챗봇, 지식그래프 페이지로 이동하세요.")


def render_recommendations(st: Any, data: dict[str, Any]) -> None:
    st.title("✨ 축제 추천")
    regions = ["전체"] + sorted({str(r.get("region") or r.get("location") or "미분류") for r in data["festivals"]})
    themes = ["전체"] + sorted({str(r.get("theme") or "미분류") for r in data["festivals"]})
    months = ["전체"] + [str(i) for i in range(1, 13)]
    ages = ["전체", "어린이", "청소년", "성인", "가족", "시니어"]
    region, theme, month, age = st.columns(4)
    selected_region = region.selectbox("지역", regions)
    selected_theme = theme.selectbox("테마", themes)
    selected_month = month.selectbox("기간(월)", months)
    selected_age = age.selectbox("연령대", ages)
    # TODO(추천 담당): 최종 스키마 기준으로 날짜·테마·연령대 배열을 정규화합니다.
    # 현재 데이터에 배열 또는 문자열이 섞여 있어 문자열 기준으로 안전하게 필터링합니다.
    rows = data["festivals"]
    if selected_region != "전체": rows = [r for r in rows if selected_region in str(r)]
    if selected_theme != "전체": rows = [r for r in rows if selected_theme in str(r)]
    if selected_month != "전체": rows = [r for r in rows if selected_month in str(r.get("date") or r.get("period") or "")]
    if selected_age != "전체": rows = [r for r in rows if selected_age in str(r)]
    if not rows: return empty_state(st)
    for i, row in enumerate(rows[:30]):
        festival_card(st, row, f"recommend-{i}", lambda selected: festival_detail_callback(st, selected))
