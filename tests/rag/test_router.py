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


@pytest.mark.parametrize(
    "question",
    [
        "축제는 어디에서 열리나요?",
        "이 축제의 대상은 누구인가요?",
        "이 축제 근처에서 머물 수 있는 숙소는 어디인가요?",
        "이 축제 근처에서 체험할 수 있는 곳은 어디인가요?",
        "10월에 열리는 무료 축제",
        "입장료가 1만원 이하인 축제",
    ],
)
def test_route_question_sends_relationship_and_condition_questions_to_text2cypher(
    question,
):
    assert route_question(question)["selected_tool"] == "text2cypher"


@pytest.mark.parametrize("question", ["이천원 나오는 축제 알려줘", "장윤정 출연 축제"]) 
def test_route_question_sends_performer_questions_to_text2cypher(question):
    assert route_question(question)["selected_tool"] == "text2cypher"


def test_route_question_sends_product_questions_to_text2cypher():
    assert route_question("이순신 축제에서 주는 기념품 알려줘")["selected_tool"] == "text2cypher"


@pytest.mark.parametrize(
    "question",
    [
        "부산 불꽃축제는 어떤 축제야?",
        "이 축제 특징을 알려줘",
        "얼마나 재미있는 축제인지 설명해줘",
        "관계없는 축제를 추천해줘",
        "부산 축제 추천",
        "서울 추천 축제",
    ],
)
def test_route_question_sends_explanations_without_keyword_collisions_to_vector(
    question,
):
    assert route_question(question)["selected_tool"] == "vector"


@pytest.mark.parametrize(
    "festival_title",
    [
        "「인각사」와 함께하는 제5회 군위 삼국유사 전국 가족걷기대회",
        "2026 원주 독서대전 〈거리에서 만난 책〉",
        "2026 원주옥상영화제",
        "거문도백도 은빛바다체험행사",
        "하전바지락 오감체험 페스티벌",
    ],
)
def test_route_question_keeps_real_bare_festival_titles_on_full_text(
    festival_title,
):
    assert route_question(festival_title)["selected_tool"] == "full_text"


def test_route_question_uses_full_text_as_deterministic_fallback():
    first = route_question("  불꽃축제  ")
    second = route_question("  불꽃축제  ")

    assert first == second
    assert first["query"] == "불꽃축제"
    assert first["selected_tool"] == "full_text"


def test_route_question_does_not_send_bare_information_request_to_vector():
    assert route_question("축제 알려줘")["selected_tool"] == "full_text"


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
