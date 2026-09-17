"""자연어 질문을 읽기 전용 Cypher로 변환하는 골격."""

from typing import Any


# 입력: question, 고정 Graph schema, LLM
# 출력: read-only Cypher와 실행 결과 또는 오류 로그
# TODO 1. 현재 확정된 Node label과 Relationship 방향으로 Graph schema block을 만든다.
# TODO 2. schema 밖의 label/relation을 만들지 않는 Text2Cypher prompt를 작성한다.
# TODO 3. CREATE/MERGE/DELETE/SET/REMOVE가 포함된 query를 차단한다.
# TODO 4. 생성 Cypher의 문법과 허용 schema를 실행 전에 검사한다.
# TODO 5. 안전한 query만 Neo4j에서 실행하고 question/Cypher/error를 기록한다.


# TODO 6. Accommodation/Experience Node와 NEARBY 관계를 Graph schema block에 반영한다.
# TODO 7. Node metadata와 distance_meters 등 Relationship metadata를 질의 가능한 schema로 설명한다.

def build_graph_schema_block() -> str:
    """Ontology와 일치하는 Graph schema 설명을 만든다."""
    raise NotImplementedError


def generate_cypher(question: str, llm: Any) -> str:
    """자연어 질문에서 읽기 전용 Cypher를 생성한다."""
    raise NotImplementedError


def validate_read_only_cypher(cypher: str) -> None:
    """쓰기·삭제 query와 허용되지 않은 구문을 차단한다."""
    raise NotImplementedError


def execute_text2cypher(driver: Any, question: str, llm: Any) -> list[dict[str, Any]]:
    """Cypher 생성·검사·실행을 연결한다."""
    raise NotImplementedError


# 완료 조건: 임의 쓰기 query가 실행되지 않고, 허용 schema 범위의 질문 결과만 반환된다.
# Freeze point: Text2Cypher에 제공하는 schema는 Graph 적재 구조와 함께 고정한다.
