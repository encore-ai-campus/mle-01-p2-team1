import pytest

from src.rag.router import dispatch_question, route_question


@pytest.mark.parametrize(
    ("question", "expected_tool"),
    [
        ("서울에서 열리는 축제는 몇 개야?", "text2cypher"),
        ("부산 축제와 비슷한 축제를 추천해줘", "vector"),
        ("부산 축제", "full_text"),
    ],
)
def test_route_question_selects_tool_by_question_type(question, expected_tool):
    route = route_question(question)

    assert route["query"] == question
    assert route["selected_tool"] == expected_tool
    assert route["routing_reason"].strip()


def test_route_question_prioritizes_text2cypher_when_multiple_rules_match():
    route = route_question("서울에서 열리는 축제 중 비슷한 축제는 몇 개야?")

    assert route["selected_tool"] == "text2cypher"


def test_route_question_uses_full_text_as_deterministic_fallback():
    first = route_question("  불꽃축제  ")
    second = route_question("  불꽃축제  ")

    assert first == second
    assert first["query"] == "불꽃축제"
    assert first["selected_tool"] == "full_text"


@pytest.mark.parametrize("question", ["", "   "])
def test_route_question_rejects_empty_question(question):
    with pytest.raises(ValueError, match="question must not be empty"):
        route_question(question)


def test_dispatch_question_calls_selected_service_with_normalized_query():
    services = {
        "text2cypher": lambda query: {"tool": "text2cypher", "query": query},
        "vector": lambda query: {"tool": "vector", "query": query},
        "full_text": lambda query: {"tool": "full_text", "query": query},
    }

    result = dispatch_question("  비슷한 축제 추천해줘  ", services)

    assert result == {"tool": "vector", "query": "비슷한 축제 추천해줘"}


def test_dispatch_question_reports_missing_selected_service():
    with pytest.raises(KeyError, match="full_text service is required"):
        dispatch_question("부산 축제", {})


def test_dispatch_question_rejects_non_callable_service():
    with pytest.raises(TypeError, match="full_text service must be callable"):
        dispatch_question("부산 축제", {"full_text": "not-callable"})
