"""질문 유형에 따라 Text2Cypher, Vector, Full-text를 선택하는 골격."""

from typing import Any


# 입력: 사용자 question
# 출력: query, selected_tool, routing_reason
# TODO 1. 관계·조건·집계 질문은 text2cypher로 보내는 rule을 작성한다.
# TODO 2. 유사도·추천·자연어 설명 질문은 vector search로 보내는 rule을 작성한다.
# TODO 3. 축제명·프로그램명 exact 검색은 full-text search로 보내는 rule을 작성한다.
# TODO 4. 여러 규칙이 맞을 때 우선순위와 fallback을 결정한다.
# TODO 5. 선택 결과와 근거를 report에 남긴다.


_TEXT2CYPHER_KEYWORDS = (
    "몇 개",
    "몇개",
    "개수",
    "얼마나",
    "가장 많은",
    "가장 적은",
    "에서 열리는",
    "어디에서",
    "어디에",
    "언제",
    "누가",
    "주최",
    "대상",
    "프로그램이 있는",
    "포함하는",
    "관계",
)
_VECTOR_KEYWORDS = (
    "비슷",
    "유사",
    "추천",
    "설명",
    "어울리",
    "관련된",
)


def route_question(question: str) -> dict[str, str]:
    """규칙 기반으로 질문 처리 도구를 선택한다."""
    if not isinstance(question, str):
        raise TypeError("question must be a string")

    query = question.strip()
    if not query:
        raise ValueError("question must not be empty")

    if any(keyword in query for keyword in _TEXT2CYPHER_KEYWORDS):
        selected_tool = "text2cypher"
        routing_reason = "관계·조건·집계 질문"
    elif any(keyword in query for keyword in _VECTOR_KEYWORDS):
        selected_tool = "vector"
        routing_reason = "유사도·추천·자연어 설명 질문"
    else:
        selected_tool = "full_text"
        routing_reason = "축제명·프로그램명 정확 검색 또는 기본 검색"

    return {
        "query": query,
        "selected_tool": selected_tool,
        "routing_reason": routing_reason,
    }


def dispatch_question(question: str, services: dict[str, Any]) -> Any:
    """Router 결과에 따라 검색 또는 Text2Cypher를 호출한다."""
    route = route_question(question)
    selected_tool = route["selected_tool"]
    if selected_tool not in services:
        raise KeyError(f"{selected_tool} service is required")

    service = services[selected_tool]
    if not callable(service):
        raise TypeError(f"{selected_tool} service must be callable")

    return service(route["query"])


# 최소 예시: {"query": "부산 축제", "selected_tool": "full_text", "routing_reason": "정확한 이름 검색"}
# 완료 조건: 같은 질문은 같은 rule 우선순위로 같은 tool을 선택한다.
# Freeze point: Router tool 이름은 answer/QA 모듈과 합의 후 변경하지 않는다.
