"""Owner 3: chatbot/evidence and knowledge graph pages."""
from __future__ import annotations

from typing import Any
from .components import empty_state
from .data_loader import festival_name, festival_text


def render_chat(st: Any, data: dict[str, Any]) -> None:
    st.title("💬 축제 챗봇")
    question = st.chat_input("축제에 대해 질문해보세요")
    if not question: return
    matches = [r for r in data["festivals"] if any(token in str(r).lower() for token in question.split())][:3]
    if not matches: matches = data["festivals"][:3]
    st.write("현재는 로컬 키워드 검색 기반 답변입니다.")
    for row in matches:
        st.markdown(f"**{festival_name(row)}**")
        st.write(festival_text(row)[:500] or "관련 설명을 찾았습니다.")
        st.caption("근거 원문")
        st.code(festival_text(row)[:1000] or "원문 없음")
        # TODO(챗봇 담당): src/rag/retrieval.py를 연결하고 출처 URL을 첨부합니다.
        source_url = row.get("url") or row.get("source_url")
        if source_url: st.markdown(f"[출처 원문 열기]({source_url})")


def render_graph(st: Any, data: dict[str, Any]) -> None:
    st.title("🕸️ 지식그래프")
    limit = st.slider("표시할 간선 관계 수", min_value=5, max_value=200, value=30)
    triples = data["triples"][:limit]
    if not triples: return empty_state(st, "지식그래프 관계가 없습니다.")
    st.metric("표시 관계 수", len(triples))
    st.dataframe(triples, use_container_width=True)
    # TODO(그래프 담당): streamlit-agraph 또는 PyVis로 노드·간선을 시각화합니다.
    # 외부 시각화 패키지 없이도 현재는 관계 표를 제공해 검증 가능하게 합니다.
