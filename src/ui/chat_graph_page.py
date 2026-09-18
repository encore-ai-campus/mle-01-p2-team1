"""Local chatbot/evidence and knowledge-graph Streamlit pages."""
from __future__ import annotations

import re
import math
from collections.abc import Iterable, Sequence
from typing import Any

from .components import empty_state
from .data_loader import festival_name, festival_text
from .aura_service import choose_festival_name, fetch_festival_names, fetch_graph_edges, retrieve_aura_festivals


_QUESTION_STOP_WORDS = {
    "관련",
    "무엇",
    "어디",
    "어떤",
    "있는",
    "열리는",
    "축제",
    "축제를",
    "행사",
    "알려줘",
    "추천",
    "해주세요",
}
_KOREAN_PARTICLE_SUFFIXES = (
    "에서",
    "에게",
    "으로",
    "부터",
    "까지",
    "처럼",
    "보다",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "와",
    "과",
    "도",
    "에",
)
_URL_PATTERN = re.compile(r"https?://[^\s<>\]\[()\"']+", re.IGNORECASE)
_ENTITY_COLORS = {
    "Festival": "#FFB703",
    "Location": "#4CC9F0",
    "Organization": "#90BE6D",
    "Program": "#F9844A",
    "Theme": "#B892FF",
    "Audience": "#F28482",
    "Artist": "#F72585",
    "Product": "#43AA8B",
    "Accommodation": "#577590",
    "Experience": "#277DA1",
}


def filter_experience_edges(triples: Sequence[dict[str, Any]], show_experience: bool = False) -> list[dict[str, Any]]:
    """Hide noisy Experience neighbors by default while keeping an opt-in toggle."""
    if show_experience:
        return list(triples)
    return [
        triple for triple in triples
        if triple.get("subject_type") != "Experience"
        and triple.get("object_type") != "Experience"
    ]


def _question_terms(question: str) -> list[str]:
    terms: list[str] = []
    for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", question.lower()):
        if token in _QUESTION_STOP_WORDS:
            continue
        normalized = token
        for suffix in _KOREAN_PARTICLE_SUFFIXES:
            if normalized.endswith(suffix) and len(normalized) - len(suffix) >= 2:
                normalized = normalized[: -len(suffix)]
                break
        if normalized not in _QUESTION_STOP_WORDS and normalized not in terms:
            terms.append(normalized)
    return terms


def _first_url(value: Any) -> str | None:
    match = _URL_PATTERN.search(str(value or ""))
    return match.group(0).rstrip(".,;:!?") if match else None


def _evidence_excerpt(text: str, matched_terms: Iterable[str], limit: int = 360) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    terms = [term.lower() for term in matched_terms]
    evidence = next(
        (sentence for sentence in sentences if any(term in sentence.lower() for term in terms)),
        sentences[0] if sentences else "원문 정보가 없습니다.",
    )
    return evidence if len(evidence) <= limit else evidence[: limit - 1].rstrip() + "…"


def build_source_card(
    festival: dict[str, Any],
    matched_terms: Iterable[str] = (),
) -> dict[str, str | None]:
    """Normalize one festival document into a source card for the chat UI."""
    metadata = festival.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    text = festival_text(festival)
    return {
        "title": festival_name(festival),
        "source_doc_id": str(
            festival.get("source_doc_id")
            or festival.get("doc_id")
            or metadata.get("source_doc_id")
            or metadata.get("doc_id")
            or "문서 ID 없음"
        ),
        "evidence": _evidence_excerpt(text, matched_terms),
        "source_url": _first_url(
            festival.get("source_url")
            or festival.get("url")
            or festival.get("homepage")
            or metadata.get("homepage")
            or metadata.get("source_url")
        ),
    }


def _rank_festivals(
    question: str,
    festivals: Sequence[dict[str, Any]],
    limit: int = 3,
) -> list[tuple[dict[str, Any], list[str]]]:
    terms = _question_terms(question)
    if not terms:
        return []

    ranked: list[tuple[int, int, dict[str, Any], list[str]]] = []
    for index, festival in enumerate(festivals):
        metadata = festival.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        name = festival_name(festival).lower()
        text = festival_text(festival).lower()
        metadata_text = " ".join(str(value) for value in metadata.values()).lower()
        matched_terms = [
            term for term in terms if term in name or term in text or term in metadata_text
        ]
        if not matched_terms:
            continue
        score = sum(
            3 if term in name else 2 if term in metadata_text else 1
            for term in matched_terms
        )
        ranked.append((score, index, festival, matched_terms))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [(festival, matched) for _, _, festival, matched in ranked[:limit]]


def build_local_chat_response(
    question: str,
    festivals: Sequence[dict[str, Any]],
    limit: int = 3,
) -> dict[str, Any]:
    """Answer with only local festival documents and attach visible evidence."""
    matches = _rank_festivals(question, festivals, limit=limit)
    if not matches:
        return {
            "answer": "관련 축제 정보를 찾지 못했습니다. 다른 지역, 테마 또는 축제명으로 질문해 주세요.",
            "sources": [],
            "retrieval_method": "local",
        }

    sources = [build_source_card(row, terms) for row, terms in matches]
    names = [source["title"] for source in sources]
    answer = "관련 축제로 " + ", ".join(f"**{name}**" for name in names) + "을(를) 찾았습니다."
    return {"answer": answer, "sources": sources, "retrieval_method": "local"}


def select_graph_edges(
    triples: Sequence[dict[str, Any]],
    limit: int,
    query: str = "",
    entity_types: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Filter triples for the graph while enforcing the 5..200 edge contract."""
    if not 5 <= limit <= 200:
        raise ValueError("limit must be between 5 and 200")

    needle = query.strip().lower()
    selected: list[dict[str, Any]] = []
    for triple in triples:
        edge_types = {
            str(triple.get("subject_type") or "Unknown"),
            str(triple.get("object_type") or "Unknown"),
        }
        if entity_types is not None and not edge_types.issubset(entity_types):
            continue
        searchable = " ".join(
            str(value)
            for value in (
                triple.get("subject"),
                triple.get("relation"),
                triple.get("object"),
                triple.get("evidence"),
                triple.get("evidences"),
            )
        ).lower()
        if needle and needle not in searchable:
            continue
        selected.append(triple)
        if len(selected) == limit:
            break
    return selected


def _dot_escape(value: Any) -> str:
    return str(value or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _list_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value or "")


def build_graph_dot(triples: Sequence[dict[str, Any]]) -> str:
    """Build a deterministic Graphviz DOT graph from selected triples."""
    node_ids: dict[tuple[str, str], str] = {}
    node_lines: list[str] = []
    edge_lines: list[str] = []

    def node_id(label: Any, entity_type: Any) -> str:
        key = (str(entity_type or "Unknown"), str(label or "이름 없음"))
        if key not in node_ids:
            identifier = f"n{len(node_ids)}"
            node_ids[key] = identifier
            color = _ENTITY_COLORS.get(key[0], "#ADB5BD")
            label = key[1] if len(key[1]) <= 18 else key[1][:17] + "…"
            node_lines.append(
                f'  {identifier} [label="{_dot_escape(label)}", '
                f'tooltip="{_dot_escape(key[0] + " · " + key[1])}", fillcolor="{color}"];'
            )
        return node_ids[key]

    for triple in triples:
        subject_id = node_id(triple.get("subject"), triple.get("subject_type"))
        object_id = node_id(triple.get("object"), triple.get("object_type"))
        evidence = triple.get("evidences", triple.get("evidence", ""))
        edge_lines.append(
            f'  {subject_id} -> {object_id} [label="{_dot_escape(triple.get("relation"))}", '
            f'tooltip="{_dot_escape(_list_text(evidence))}"];'
        )

    lines = [
        "digraph FestivalKnowledgeGraph {",
        '  graph [rankdir="LR", bgcolor="transparent", pad="0.15", size="12,6!", ratio="fill", nodesep="0.35", ranksep="0.7", splines="spline", overlap="false"];',
        '  node [shape="box", style="rounded,filled", fontname="Malgun Gothic", fontsize="10", margin="0.12,0.08", color="#495057"];',
        '  edge [fontname="Malgun Gothic", fontsize="8", color="#6C757D", fontcolor="#343A40"];',
        *node_lines,
        *edge_lines,
        "}",
    ]
    return "\n".join(lines)


def build_graph_figure_data(triples: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[tuple[str, str, str]]]:
    """Build deduplicated node and edge data for the interactive graph view."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[tuple[str, str, str]] = []
    for triple in triples:
        subject = str(triple.get("subject") or "이름 없음")
        object_ = str(triple.get("object") or "이름 없음")
        subject_type = str(triple.get("subject_type") or "Unknown")
        object_type = str(triple.get("object_type") or "Unknown")
        nodes.setdefault(subject, {"id": subject, "type": subject_type})
        nodes.setdefault(object_, {"id": object_, "type": object_type})
        edge = (subject, object_, str(triple.get("relation") or "RELATED"))
        if edge not in edges:
            edges.append(edge)
    return list(nodes.values()), edges


def build_interactive_graph(st: Any, triples: Sequence[dict[str, Any]]) -> None:
    """Render a compact Neo4j-like interactive network with Plotly."""
    import plotly.graph_objects as go

    nodes, edges = build_graph_figure_data(triples)
    if not nodes:
        return
    degree = {node["id"]: 0 for node in nodes}
    for source, target, _ in edges:
        degree[source] += 1
        degree[target] += 1
    center = max(degree, key=degree.get)
    ordered = [center] + [node["id"] for node in nodes if node["id"] != center]
    positions = {center: (0.0, 0.0)}
    radius = 1.0
    for index, node_id in enumerate(ordered[1:]):
        angle = 2 * math.pi * index / max(1, len(ordered) - 1)
        positions[node_id] = (radius * math.cos(angle), radius * math.sin(angle))
    colors = {name: color for name, color in _ENTITY_COLORS.items()}
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for source, target, _ in edges:
        edge_x += [positions[source][0], positions[target][0], None]
        edge_y += [positions[source][1], positions[target][1], None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line={"width": 1.5, "color": "#9aa8b8"}, hoverinfo="none")
    node_trace = go.Scatter(
        x=[positions[node["id"]][0] for node in nodes],
        y=[positions[node["id"]][1] for node in nodes],
        mode="markers+text",
        text=[node["id"] for node in nodes],
        textposition="top center",
        hovertext=[f"{node['type']} · {node['id']}" for node in nodes],
        hoverinfo="text",
        marker={"size": [34 if node["id"] == center else 24 for node in nodes], "color": [colors.get(node["type"], "#adb5bd") for node in nodes], "line": {"width": 1.5, "color": "#536273"}},
    )
    labels = []
    for source, target, relation in edges:
        x = (positions[source][0] + positions[target][0]) / 2
        y = (positions[source][1] + positions[target][1]) / 2
        labels.append(dict(x=x, y=y, text=relation, showarrow=False, font={"size": 10, "color": "#536273"}))
    fig = go.Figure([edge_trace, node_trace])
    fig.update_layout(height=600, margin={"l": 10, "r": 10, "t": 10, "b": 10}, showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis={"visible": False}, yaxis={"visible": False, "scaleanchor": "x"}, annotations=labels)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})


def build_agraph(st: Any, triples: Sequence[dict[str, Any]]) -> Any:
    """Render a Neo4j-like draggable graph using streamlit-agraph."""
    from streamlit_agraph import Config, Edge, Node, agraph

    nodes, edges = build_graph_figure_data(triples)
    degree: dict[str, int] = {node["id"]: 0 for node in nodes}
    for source, target, _ in edges:
        degree[source] += 1
        degree[target] += 1
    color_map = {name: color for name, color in _ENTITY_COLORS.items()}
    graph_nodes = [
        Node(
            id=node["id"],
            label=node["id"],
            title=f"{node['type']} · 연결 {degree[node['id']]}개",
            size=30 if degree[node["id"]] >= 3 else 22,
            color=color_map.get(node["type"], "#ADB5BD"),
        )
        for node in nodes
    ]
    graph_edges = [
        Edge(source=source, target=target, label=relation, type="arrow")
        for source, target, relation in edges
    ]
    config = Config(
        width="100%",
        height=620,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F45B73",
        collapsible=False,
    )
    return agraph(nodes=graph_nodes, edges=graph_edges, config=config)


def _render_sources(st: Any, sources: Sequence[dict[str, Any]]) -> None:
    if not sources:
        return
    with st.expander(f"근거 원문 및 링크 ({len(sources)}건)", expanded=True):
        for index, source in enumerate(sources, start=1):
            st.markdown(f"**{index}. {source['title']}**")
            st.caption(f"문서 ID: {source['source_doc_id']}")
            st.write(source["evidence"])
            if source.get("source_url"):
                st.link_button("공식 페이지 열기", source["source_url"])
            else:
                st.caption("공식 페이지 링크 정보 없음")


def _render_chat_entry(st: Any, entry: dict[str, Any]) -> None:
    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])
        if entry["role"] == "assistant":
            _render_sources(st, entry.get("sources", []))


def render_chat(st: Any, data: dict[str, Any]) -> None:
    st.title("💬 축제 챗봇")
    festivals = data.get("festivals", [])
    aura_driver = data.get("aura_driver")
    st.caption(
        "Neo4j Aura Full-text 검색" if aura_driver else
        f"로컬 축제 원문 {len(festivals):,}건 검색( Aura 연결 없음 )"
    )

    history = st.session_state.setdefault("festival_chat_history", [])
    for entry in history:
        _render_chat_entry(st, entry)

    question = st.chat_input("예: 부산에서 음악 공연을 볼 수 있는 축제를 알려줘")
    if not question:
        return

    user_entry = {"role": "user", "content": question}
    aura_rows = retrieve_aura_festivals(aura_driver, question) if aura_driver else []
    if aura_rows:
        response = {
            "answer": "Aura에서 관련 축제로 " + ", ".join(f"**{row['name']}**" for row in aura_rows) + "을(를) 찾았습니다.",
            "sources": [
                {"title": row.get("name", ""), "source_doc_id": str(row.get("source_doc_id") or "문서 ID 없음"),
                 "evidence": str(row.get("text") or "Neo4j Aura 검색 결과"), "source_url": None}
                for row in aura_rows
            ],
            "retrieval_method": "aura_fulltext",
        }
    else:
        response = build_local_chat_response(question, festivals)
    assistant_entry = {
        "role": "assistant",
        "content": response["answer"],
        "sources": response["sources"],
        "retrieval_method": response["retrieval_method"],
    }
    history.extend([user_entry, assistant_entry])
    _render_chat_entry(st, user_entry)
    _render_chat_entry(st, assistant_entry)


def _graph_detail_rows(triples: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "주어": str(triple.get("subject") or ""),
            "관계": str(triple.get("relation") or ""),
            "목적어": str(triple.get("object") or ""),
            "문서 ID": _list_text(
                triple.get("source_doc_ids", triple.get("source_doc_id", ""))
            ),
            "근거 원문": _list_text(triple.get("evidences", triple.get("evidence", ""))),
        }
        for triple in triples
    ]


def render_graph(st: Any, data: dict[str, Any]) -> None:
    st.title("🕸️ 지식그래프")
    st.caption("축제와 장소·프로그램·테마 등의 연결 관계를 탐색할 수 있습니다.")
    aura_driver = data.get("aura_driver")
    if aura_driver:
        festival_names = fetch_festival_names(aura_driver)
        current = st.session_state.get("selected_graph_festival")
        selected_festival = st.selectbox(
            "축제 선택",
            festival_names,
            index=festival_names.index(current) if current in festival_names else 0,
            key="graph_festival_selector",
            help="선택한 축제를 중심으로 Neo4j Aura의 연결 관계를 표시합니다.",
        ) if festival_names else ""
        if not selected_festival:
            return empty_state(st, "Aura에서 축제 목록을 불러오지 못했습니다.")
        st.session_state["selected_graph_festival"] = choose_festival_name(festival_names, selected_festival)
        triples = fetch_graph_edges(aura_driver, limit=100, query=selected_festival)
        st.caption(f"선택한 축제 중심의 Neo4j Aura 관계 {len(triples)}건입니다.")
        if not triples:
            return empty_state(st, "Aura에서 해당 엔티티와 연결된 관계를 찾지 못했습니다.")
    else:
        triples = data.get("triples", [])
    if not triples:
        return empty_state(st, "지식그래프 관계가 없습니다.")

    show_experience = st.toggle("체험(Experience) 표시", value=False)
    triples = filter_experience_edges(triples, show_experience=show_experience)
    if not triples:
        return empty_state(st, "체험 관계를 제외하면 표시할 그래프가 없습니다.")

    entity_types = sorted(
        {
            str(entity_type)
            for triple in triples
            for entity_type in (triple.get("subject_type"), triple.get("object_type"))
            if entity_type
        }
    )
    if aura_driver:
        selected_types = st.multiselect(
            "엔티티 유형",
            entity_types,
            default=entity_types,
        )
    else:
        search_col, type_col = st.columns([2, 3])
        query = search_col.text_input(
            "그래프 검색",
            placeholder="축제명, 장소, 프로그램 또는 관계를 입력하세요",
        )
        selected_types = type_col.multiselect(
            "엔티티 유형",
            entity_types,
            default=entity_types,
        )
    limit = st.slider("표시할 간선 관계 수", min_value=5, max_value=100, value=12)
    selected = select_graph_edges(
        triples,
        limit=limit,
        query="" if aura_driver else query,
        entity_types=set(selected_types),
    )
    if not selected:
        return empty_state(st, "선택한 조건에 맞는 지식그래프 관계가 없습니다.")

    node_count = len(
        {
            (str(triple.get("subject_type")), str(triple.get("subject")))
            for triple in selected
        }
        | {
            (str(triple.get("object_type")), str(triple.get("object")))
            for triple in selected
        }
    )
    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("표시 관계 수", len(selected))
    metric_col2.metric("표시 노드 수", node_count)
    st.graphviz_chart(build_graph_dot(selected), width="stretch")

    with st.expander("관계별 근거 원문 보기"):
        st.dataframe(_graph_detail_rows(selected), width="stretch", hide_index=True)
