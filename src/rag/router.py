"""질문 유형에 따라 Text2Cypher, Vector, Full-text를 선택하는 골격."""

import re
from typing import Any


# 입력: 사용자 question
# 출력: query, selected_tool, routing_reason
# TODO 1. 관계·조건·집계 질문은 text2cypher로 보내는 rule을 작성한다.
# TODO 2. 유사도·추천·자연어 설명 질문은 vector search로 보내는 rule을 작성한다.
# TODO 3. 축제명·프로그램명 exact 검색은 full-text search로 보내는 rule을 작성한다.
# TODO 4. 여러 규칙이 맞을 때 우선순위와 fallback을 결정한다.
# TODO 5. 선택 결과와 근거를 report에 남긴다.


_TEXT2CYPHER_PATTERNS = (
    r"몇\s*(?:개|명|곳|가지|시)",
    r"(?:개수|평균|합계|총합)",
    r"(?:가장|얼마나)\s*(?:많|적|가까|먼|오래|인기)",
    r"어디(?:에서|에|인지|인가|예요|야)?",
    r"(?:언제|누가|주최|대상)",
    r"(?:근처|주변|숙소)",
    r"체험(?:할|이\s*있는|은\s*어디)",
    r"(?:입장료|가격|무료|유료|이상|이하|초과|미만)",
    r"\d[\d,]*\s*(?:만원|원)(?![가-힣A-Za-z0-9])",
    r"\d{1,2}\s*월",
    r"(?:열리|개최)",
    r"(?:프로그램이\s*있는|포함하)",
    r"(?:어떤\s*관계|관계가\s*있|연결)",
)
_VECTOR_PATTERNS = (
    r"(?:비슷|유사)(?:한|하게)",
    r"추천(?:해|하여|받)",
    r"어울리(?:는|게)",
    r"관련된",
    r"(?:설명|소개|특징)",
    r"어떤\s*(?:축제|행사|프로그램)",
    r"알려\s*(?:줘|주세요)",
)


def route_question(question: str) -> dict[str, str]:
    """규칙 기반으로 질문 처리 도구를 선택한다."""
    if not isinstance(question, str):
        raise TypeError("question must be a string")

    query = question.strip()
    if not query:
        raise ValueError("question must not be empty")

    if any(re.search(pattern, query) for pattern in _TEXT2CYPHER_PATTERNS):
        selected_tool = "text2cypher"
        routing_reason = "관계·조건·집계 질문"
    elif any(re.search(pattern, query) for pattern in _VECTOR_PATTERNS):
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
