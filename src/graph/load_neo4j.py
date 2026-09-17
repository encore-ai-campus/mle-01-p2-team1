"""Neo4j 적재용 Node/Relationship 파일을 DB에 넣는 실행 골격."""

from datetime import date, datetime, time, timedelta
from typing import Any, Sequence


# 입력: neo4j_nodes.json, neo4j_relationships.json, NEO4J_URI/USER/PASSWORD
# 출력: Neo4j DB, load_report.json
# TODO 1. 환경변수에서 접속 정보를 읽고 비밀번호를 로그에 남기지 않는다.
# TODO 2. EntityType별 unique constraint 또는 index를 생성한다.
# TODO 3. Node를 entity_type과 name 기준 MERGE한다.
# TODO 4. ontology 방향과 같은 방향으로 Relationship을 MATCH/MERGE한다.
# TODO 5. source_doc_id와 evidence를 Relationship property로 저장한다.
# TODO 6. 일정 건수씩 batch transaction으로 적재하고 실패 batch를 기록한다.
# TODO 7. 적재 후 Node/Relationship 수와 type별 통계를 조회한다.


def create_constraints(driver: Any) -> None:
    """Neo4j unique constraint/index를 생성한다."""
    with driver.session() as session:
        session.run(
            """
            CREATE CONSTRAINT entity_identity IF NOT EXISTS
            FOR (n:Entity)
            REQUIRE (n.entity_type, n.canonical_name) IS UNIQUE
            """
        ).consume()


def load_nodes(driver: Any, nodes: Sequence[dict[str, Any]], batch_size: int = 500) -> int:
    """Node 목록을 batch 단위로 적재한다."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    query = """
    UNWIND $rows AS item
    MERGE (n:Entity {
        entity_type: item.entity_type,
        canonical_name: item.canonical_name
    })
    SET n += item
    """
    written = 0
    with driver.session() as session:
        for start in range(0, len(nodes), batch_size):
            rows = list(nodes[start:start + batch_size])
            session.run(query, rows=rows).consume()
            written += len(rows)
    return written


def load_relationships(driver: Any, relationships: Sequence[dict[str, Any]], batch_size: int = 500) -> int:
    """Relationship 목록을 batch 단위로 적재한다."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    query = """
    UNWIND $rows AS item
    MATCH (s:Entity {
        entity_type: item.subject.entity_type,
        canonical_name: item.subject.canonical_name
    })
    MATCH (o:Entity {
        entity_type: item.object.entity_type,
        canonical_name: item.object.canonical_name
    })
    MERGE (s)-[r:$(item.relation)]->(o)
    SET r += item.properties
    """
    written = 0
    with driver.session() as session:
        for start in range(0, len(relationships), batch_size):
            rows = [
                {
                    "subject": row["subject"],
                    "relation": row["relation"],
                    "object": row["object"],
                    "properties": {
                        key: _normalize_relationship_property(key, value)
                        for key, value in row.items()
                        if key not in {"subject", "relation", "object"}
                    },
                }
                for row in relationships[start:start + batch_size]
            ]
            result = session.run(query, rows=rows)
            summary = result.consume()
            written += summary.counters.relationships_created
    return written


def _normalize_relationship_property(field_name: str, value: Any) -> Any:
    """Neo4j가 저장 가능한 관계 속성만 통과시키고 tuple은 list로 바꾼다."""
    scalar_types = (str, bool, int, float, bytes, date, datetime, time, timedelta)
    if value is None or isinstance(value, scalar_types):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, (list, tuple)):
        normalized = []
        for item in value:
            if item is None or isinstance(item, (list, tuple, dict, set)):
                break
            if isinstance(item, bytearray):
                item = bytes(item)
            if not isinstance(item, scalar_types):
                break
            normalized.append(item)
        else:
            if not normalized or len({type(item) for item in normalized}) == 1:
                return normalized

    raise ValueError(
        f"{field_name} is not a valid Neo4j relationship property value"
    )


def build_load_report(driver: Any) -> dict[str, Any]:
    """적재 후 개수와 오류 통계를 만든다."""
    with driver.session() as session:
        result = session.run(
            """
            MATCH (n:Entity)
            WITH count(n) AS node_count
            OPTIONAL MATCH ()-[r]->()
            RETURN node_count, count(r) AS relationship_count
            """
        ).single()
    return {
        "node_count": result["node_count"],
        "relationship_count": result["relationship_count"],
    }


# 최소 예시: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD는 .env로 관리한다.
# 완료 조건: 재실행해도 중복 Node/Relationship이 생기지 않고 load_report가 저장된다.
# Freeze point: MERGE key와 관계 property 이름은 승인 없이 변경하지 않는다.
