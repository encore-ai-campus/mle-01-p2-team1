"""Neo4j Full-text/Vector 검색을 위한 index 생성 골격."""

from typing import Any, Sequence


# 입력: Neo4j driver, Node text 구성 규칙, embedding model
# 출력: Full-text index, Vector index, index_report.json
# TODO 1. EntityType별 검색 대상 property와 index 이름을 결정한다.
# TODO 2. Festival description/overview, Program name+description, Theme name의 임베딩 text를 만든다.
# TODO 3. 임베딩 모델과 차원·거리(metric)를 고정하고 Node에 vector property를 저장한다.
# TODO 4. Neo4j vector index와 Full-text index를 생성한다.
# TODO 5. index 상태가 ONLINE인지 확인하고 차원·대상 label을 report에 저장한다.


# TODO 6. Accommodation/Experience의 name, text, address를 Full-text 검색 대상에 포함한다.
# TODO 7. Festival/Accommodation/Experience metadata를 검색·embedding용 text로 매핑한다.

def build_search_text(node: dict[str, Any]) -> str:
    """Node에서 검색과 임베딩에 사용할 text를 만든다."""
    raise NotImplementedError


def create_fulltext_index(driver: Any, index_name: str, labels: Sequence[str], properties: Sequence[str]) -> None:
    """Full-text index를 생성한다."""
    raise NotImplementedError


def create_vector_index(driver: Any, index_name: str, dimensions: int, similarity_function: str = "cosine") -> None:
    """Vector index를 생성한다."""
    raise NotImplementedError


def build_index_report(driver: Any) -> dict[str, Any]:
    """Index 이름과 ONLINE 상태를 기록한다."""
    raise NotImplementedError


# 완료 조건: Full-text와 Vector 검색이 각각 한 건 이상 반환되고 index 상태가 ONLINE이다.
# Freeze point: embedding model, vector dimension, index 이름은 승인 없이 변경하지 않는다.
