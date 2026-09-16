"""Neo4j 적재 후 실제 Graph 구조와 Ontology 일치 여부를 검사하는 골격."""

from typing import Any


# 입력: Neo4j driver/session, ontology.py의 허용 Signature
# 출력: graph_validation_report.json
# TODO 1. 존재하지 않는 label/relation과 반대 방향 relationship을 조회한다.
# TODO 2. 같은 entity_type과 canonical_name을 가진 duplicate Node를 조회한다.
# TODO 3. 어떤 Relationship에도 연결되지 않은 orphan Node를 조회한다.
# TODO 4. degree 0 또는 비정상적으로 높은 degree Node를 별도 후보로 기록한다.
# TODO 5. 오류를 적재 오류와 ER/데이터 품질 의심으로 구분한다.


def find_schema_violations(driver: Any) -> list[dict[str, Any]]:
    """Ontology Signature와 다른 Graph relationship을 찾는다."""
    raise NotImplementedError


def find_duplicate_nodes(driver: Any) -> list[dict[str, Any]]:
    """Node unique key 중복을 찾는다."""
    raise NotImplementedError


def find_orphan_nodes(driver: Any) -> list[dict[str, Any]]:
    """관계가 없는 Node를 찾는다."""
    raise NotImplementedError


def build_graph_validation_report(driver: Any, high_degree_threshold: int = 100) -> dict[str, Any]:
    """Graph 품질 검사 결과를 하나의 report로 묶는다."""
    raise NotImplementedError


# 완료 조건: schema violation, duplicate, orphan, suspicious high-degree 수와 상세 목록이 남는다.
# Freeze point: 검사 기준과 report key는 후속 QA가 시작되면 고정한다.
