"""Local chatbot/evidence and knowledge-graph Streamlit pages."""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

from .components import empty_state
from .data_loader import festival_name, festival_text


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
            node_lines.append(
                f'  {identifier} [label="{_dot_escape(key[1])}", '
                f'tooltip="{_dot_escape(key[0])}", fillcolor="{color}"];'
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
        '  graph [rankdir="LR", bgcolor="transparent", pad="0.2"];',
        '  node [shape="box", style="rounded,filled", fontname="Malgun Gothic", color="#495057"];',
        '  edge [fontname="Malgun Gothic", color="#6C757D", fontcolor="#343A40"];',
        *node_lines,
        *edge_lines,
        "}",
    ]
    return "\n".join(lines)


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
    st.caption(
        f"현재는 프로젝트의 축제 원문 {len(festivals):,}건을 검색합니다. "
        "별도의 API 키가 필요하지 않습니다."
    )

    history = st.session_state.setdefault("festival_chat_history", [])
    for entry in history:
        _render_chat_entry(st, entry)

    question = st.chat_input("예: 부산에서 음악 공연을 볼 수 있는 축제를 알려줘")
    if not question:
        return

    user_entry = {"role": "user", "content": question}
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
    triples = data.get("triples", [])
    if not triples:
        return empty_state(st, "지식그래프 관계가 없습니다.")

    entity_types = sorted(
        {
            str(entity_type)
            for triple in triples
            for entity_type in (triple.get("subject_type"), triple.get("object_type"))
            if entity_type
        }
    )
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
    limit = st.slider("표시할 간선 관계 수", min_value=5, max_value=200, value=30)
    selected = select_graph_edges(
        triples,
        limit=limit,
        query=query,
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
