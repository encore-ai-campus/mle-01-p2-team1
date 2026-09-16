"""질문 유형에 따라 Text2Cypher, Vector, Full-text를 선택하는 골격."""

from typing import Any


# 입력: 사용자 question
# 출력: query, selected_tool, routing_reason
# TODO 1. 관계·조건·집계 질문은 text2cypher로 보내는 rule을 작성한다.
# TODO 2. 유사도·추천·자연어 설명 질문은 vector search로 보내는 rule을 작성한다.
# TODO 3. 축제명·프로그램명 exact 검색은 full-text search로 보내는 rule을 작성한다.
# TODO 4. 여러 규칙이 맞을 때 우선순위와 fallback을 결정한다.
# TODO 5. 선택 결과와 근거를 report에 남긴다.


def route_question(question: str) -> dict[str, str]:
    """규칙 기반으로 질문 처리 도구를 선택한다."""
    raise NotImplementedError


def dispatch_question(question: str, services: dict[str, Any]) -> Any:
    """Router 결과에 따라 검색 또는 Text2Cypher를 호출한다."""
    raise NotImplementedError


# 최소 예시: {"query": "부산 축제", "selected_tool": "full_text", "routing_reason": "정확한 이름 검색"}
# 완료 조건: 같은 질문은 같은 rule 우선순위로 같은 tool을 선택한다.
# Freeze point: Router tool 이름은 answer/QA 모듈과 합의 후 변경하지 않는다.
