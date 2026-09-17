"""ER 완료 Triple을 Neo4j 적재용 Node/Relationship JSON으로 변환하는 골격."""

from typing import Any, Sequence


# 입력: resolved_triples.json
# 출력: neo4j_nodes.json, neo4j_relationships.json
# TODO 1. subject/object에서 (entity_type, canonical_name) 기준 unique Node를 만든다.
# TODO 2. 같은 이름이라도 EntityType이 다르면 별도 Node로 유지한다.
# TODO 3. Triple을 relationship row로 변환하고 source_doc_id/evidence를 보존한다.
# TODO 4. 같은 subject-relation-object 관계의 evidence/source_doc_id 병합 규칙을 결정한다.
# TODO 5. 실제 ontology signature와 다른 row는 적재 전에 Reject한다.
# TODO 6. 적재용 JSON을 저장하고 다시 읽어 구조를 확인한다.


# TODO 7. resolved_triples.json 기반 Node/Relationship 입력 형식을 확정한다.
# TODO 8. extra_accommodations.jsonl을 Accommodation Node로 변환하고 ID, 이름, 주소,
#           좌표, 설명, source_file을 Node metadata로 보존한다.
# TODO 9. extra_nearby.jsonl을 Experience/nearby Node로 변환하고 extra_id 중복을 방지한다.
# TODO 10. Festival과 Accommodation/Experience 사이의 NEARBY 관계를 생성한다.
# TODO 11. Relationship metadata에 distance_meters, source_file, source_doc_id를 보존한다.
# TODO 12. Node metadata와 Relationship metadata의 최종 field mapping을 확정한다.

def build_nodes(resolved_triples: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolved Triple에서 Neo4j Node 목록을 만든다."""
    raise NotImplementedError


def build_relationships(resolved_triples: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolved Triple을 Neo4j Relationship row로 변환한다."""
    raise NotImplementedError


def prepare_neo4j_data(resolved_triples: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Node와 Relationship을 함께 생성한다."""
    raise NotImplementedError


# 최소 예시: {"name": "유플페", "entity_type": "Festival"}
# 완료 조건: 모든 Relationship의 양 끝 Node가 Node 목록에 존재한다.
# Freeze point: Node key와 Relationship property 이름은 적재 전 승인 없이 변경하지 않는다.
