"""Full-text Search와 Vector Search의 공통 Retriever 골격."""

from typing import Any, Sequence


# 입력: query, Neo4j driver, top_k
# 출력: name, entity_type, score, source를 갖는 동일 형식의 결과 목록
# TODO 1. Full-text index에 query를 보내고 score를 포함한 결과를 받는다.
# TODO 2. query embedding을 만든 뒤 Vector index를 조회한다.
# TODO 3. 두 검색 결과를 공통 schema로 변환한다.
# TODO 4. top_k 기본값과 tie 처리 규칙을 고정한다.


def full_text_search(driver: Any, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Full-text 검색 결과를 반환한다."""
    raise NotImplementedError


def vector_search(driver: Any, query: str, embedding_model: Any, top_k: int = 5) -> list[dict[str, Any]]:
    """Vector 검색 결과를 반환한다."""
    raise NotImplementedError


def normalize_search_results(rows: Sequence[dict[str, Any]], source: str) -> list[dict[str, Any]]:
    """검색 결과를 name/entity_type/score/source 형식으로 통일한다."""
    raise NotImplementedError


# 최소 예시: {"name": "유플페", "entity_type": "Festival", "score": 0.89, "source": "vector"}
# 완료 조건: 두 검색 방식이 같은 결과 계약과 top_k를 사용한다.
# Freeze point: 검색 결과 key와 score 의미는 QA 데이터 작성 전 고정한다.
