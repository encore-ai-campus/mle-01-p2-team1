"""Neo4j 적재용 Node/Relationship 파일을 DB에 넣는 실행 골격."""

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
    raise NotImplementedError


def load_nodes(driver: Any, nodes: Sequence[dict[str, Any]], batch_size: int = 500) -> int:
    """Node 목록을 batch 단위로 적재한다."""
    raise NotImplementedError


def load_relationships(driver: Any, relationships: Sequence[dict[str, Any]], batch_size: int = 500) -> int:
    """Relationship 목록을 batch 단위로 적재한다."""
    raise NotImplementedError


def build_load_report(driver: Any) -> dict[str, Any]:
    """적재 후 개수와 오류 통계를 만든다."""
    raise NotImplementedError


# 최소 예시: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD는 .env로 관리한다.
# 완료 조건: 재실행해도 중복 Node/Relationship이 생기지 않고 load_report가 저장된다.
# Freeze point: MERGE key와 관계 property 이름은 승인 없이 변경하지 않는다.
