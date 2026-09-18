import pytest

from src.ui.chat_graph_page import (
    build_graph_dot,
    build_local_chat_response,
    build_source_card,
    select_graph_edges,
)


FESTIVALS = [
    {
        "doc_id": "festival-001",
        "title": "부산바다축제",
        "text": "부산 해운대에서 음악 공연과 체험 프로그램을 운영한다.",
        "metadata": {
            "homepage": "공식 홈페이지 https://festival.example/busan 자세히 보기",
            "address": "부산광역시 해운대구",
        },
    },
    {
        "doc_id": "festival-002",
        "title": "서울장미축제",
        "text": "서울에서 장미 전시와 산책 프로그램을 운영한다.",
        "metadata": {"homepage": "https://festival.example/seoul"},
    },
]


TRIPLES = [
    {
        "subject": "부산바다축제",
        "subject_type": "Festival",
        "relation": "HELD_IN",
        "object": "해운대",
        "object_type": "Location",
        "source_doc_ids": ["festival-001"],
        "evidences": ["부산 해운대에서 열린다."],
    },
    {
        "subject": "서울장미축제",
        "subject_type": "Festival",
        "relation": "HAS_THEME",
        "object": "장미",
        "object_type": "Theme",
        "source_doc_ids": ["festival-002"],
        "evidences": ["장미를 주제로 한다."],
    },
]


def test_build_source_card_extracts_nested_official_url_and_evidence():
    card = build_source_card(FESTIVALS[0], matched_terms=["음악"])

    assert card == {
        "title": "부산바다축제",
        "source_doc_id": "festival-001",
        "evidence": "부산 해운대에서 음악 공연과 체험 프로그램을 운영한다.",
        "source_url": "https://festival.example/busan",
    }


def test_build_source_card_extracts_normalized_top_level_homepage():
    festival = {
        "doc_id": "festival-003",
        "name": "정규화 축제",
        "text": "정규화된 축제 원문이다.",
        "homepage": "https://festival.example/normalized",
    }

    card = build_source_card(festival, matched_terms=["정규화"])

    assert card["source_url"] == "https://festival.example/normalized"


def test_local_chat_response_returns_only_relevant_festival_with_source():
    response = build_local_chat_response("부산 음악 축제를 알려줘", FESTIVALS)

    assert response["retrieval_method"] == "local"
    assert response["sources"] == [
        {
            "title": "부산바다축제",
            "source_doc_id": "festival-001",
            "evidence": "부산 해운대에서 음악 공연과 체험 프로그램을 운영한다.",
            "source_url": "https://festival.example/busan",
        }
    ]
    assert "부산바다축제" in response["answer"]
    assert "서울장미축제" not in response["answer"]


def test_local_chat_response_matches_korean_location_with_particle():
    response = build_local_chat_response("부산에서 열리는 축제를 알려줘", FESTIVALS)

    assert [source["title"] for source in response["sources"]] == ["부산바다축제"]


def test_local_chat_response_does_not_invent_an_unmatched_answer():
    response = build_local_chat_response("우주 로봇 행사를 알려줘", FESTIVALS)

    assert response["sources"] == []
    assert response["answer"] == "관련 축제 정보를 찾지 못했습니다. 다른 지역, 테마 또는 축제명으로 질문해 주세요."


def test_select_graph_edges_applies_search_entity_filter_and_limit():
    selected = select_graph_edges(
        TRIPLES,
        limit=5,
        query="부산",
        entity_types={"Festival", "Location"},
    )

    assert selected == [TRIPLES[0]]


def test_select_graph_edges_returns_empty_when_no_entity_type_is_selected():
    assert select_graph_edges(TRIPLES, limit=5, entity_types=set()) == []


@pytest.mark.parametrize("limit", [4, 201])
def test_select_graph_edges_rejects_limit_outside_slider_contract(limit):
    with pytest.raises(ValueError, match="between 5 and 200"):
        select_graph_edges(TRIPLES, limit=limit)


def test_build_graph_dot_renders_typed_nodes_and_relationship_evidence():
    dot = build_graph_dot([TRIPLES[0]])

    assert dot.startswith("digraph FestivalKnowledgeGraph")
    assert 'label="부산바다축제"' in dot
    assert 'label="해운대"' in dot
    assert 'label="HELD_IN"' in dot
    assert 'tooltip="부산 해운대에서 열린다."' in dot
