"""Neo4j 적재 후 Graph 구조와 Ontology 일치 여부를 검사한다."""

from math import isfinite
from typing import Any

from src.extraction.ontology import RELATION_SIGNATURES


_RELATIONSHIP_QUERY = """
// graph_validate:all_relationships
MATCH (s)-[r]->(o)
RETURN elementId(s) AS subject_id,
       labels(s) AS subject_labels,
       s.entity_type AS subject_type,
       s.canonical_name AS subject,
       type(r) AS relation,
       elementId(o) AS object_id,
       labels(o) AS object_labels,
       o.entity_type AS object_type,
       o.canonical_name AS object,
       properties(r) AS properties
ORDER BY subject_type, subject, relation, object_type, object
"""

_EXTRA_SIGNATURES = {
    ("Festival", "NEARBY", "Accommodation"),
    ("Festival", "NEARBY", "Experience"),
}


def _value(value: Any) -> Any:
    """Enum은 문자열 값으로, 일반 값은 그대로 반환한다."""
    return getattr(value, "value", value)


_ONTOLOGY_SIGNATURES = {
    tuple(_value(part) for part in signature)
    for signature in RELATION_SIGNATURES
}
_ALLOWED_SIGNATURES = _ONTOLOGY_SIGNATURES | _EXTRA_SIGNATURES
_ALLOWED_ENTITY_TYPES = {
    entity_type
    for subject_type, _, object_type in _ALLOWED_SIGNATURES
    for entity_type in (subject_type, object_type)
}
_ALLOWED_RELATIONS = {relation for _, relation, _ in _ALLOWED_SIGNATURES}


def _rows(driver: Any, query: str, **parameters: Any) -> list[dict[str, Any]]:
    """Neo4j 결과 Record를 직렬화 가능한 dict 목록으로 바꾼다."""
    with driver.session() as session:
        result = session.run(query, **parameters)
        return [
            record.data() if hasattr(record, "data") else dict(record)
            for record in result
        ]


def find_schema_violations(driver: Any) -> list[dict[str, Any]]:
    """Ontology Signature와 다른 Graph relationship을 찾는다."""
    violations = []

    for row in _rows(driver, _RELATIONSHIP_QUERY):
        if (
            "Entity" not in (row.get("subject_labels") or [])
            or "Entity" not in (row.get("object_labels") or [])
        ):
            violations.append({**row, "error_code": "INVALID_ENDPOINT_LABEL"})
            continue

        signature = (
            row.get("subject_type"),
            row.get("relation"),
            row.get("object_type"),
        )
        if signature in _ALLOWED_SIGNATURES:
            continue

        subject_type, relation, object_type = signature
        if (
            subject_type not in _ALLOWED_ENTITY_TYPES
            or object_type not in _ALLOWED_ENTITY_TYPES
        ):
            error_code = "UNKNOWN_ENTITY_TYPE"
        elif relation not in _ALLOWED_RELATIONS:
            error_code = "UNKNOWN_RELATION"
        elif (object_type, relation, subject_type) in _ALLOWED_SIGNATURES:
            error_code = "REVERSED_DIRECTION"
        else:
            error_code = "SIGNATURE_INVALID"

        violations.append({**row, "error_code": error_code})

    return violations


def find_duplicate_nodes(driver: Any) -> list[dict[str, Any]]:
    """Node unique key인 (entity_type, canonical_name) 중복을 찾는다."""
    query = """
    // graph_validate:duplicate_nodes
    MATCH (n)
    WITH n.entity_type AS entity_type,
         n.canonical_name AS canonical_name,
         collect(elementId(n)) AS node_ids,
         count(*) AS duplicate_count
    WHERE duplicate_count > 1
    RETURN entity_type, canonical_name, duplicate_count, node_ids
    ORDER BY duplicate_count DESC, entity_type, canonical_name
    """
    return _rows(driver, query)


def find_orphan_nodes(driver: Any) -> list[dict[str, Any]]:
    """어떤 Relationship에도 연결되지 않은 Node를 찾는다."""
    query = """
    // graph_validate:orphan_nodes
    MATCH (n)
    WHERE NOT (n)--()
    RETURN elementId(n) AS node_id,
           n.entity_type AS entity_type,
           n.canonical_name AS canonical_name
    ORDER BY entity_type, canonical_name
    """
    return _rows(driver, query)


def _find_high_degree_nodes(
    driver: Any,
    high_degree_threshold: int,
) -> list[dict[str, Any]]:
    query = """
    // graph_validate:high_degree_nodes
    MATCH (n)
    OPTIONAL MATCH (n)-[r]-()
    WITH n, count(r) AS degree
    WHERE degree > $threshold
    RETURN elementId(n) AS node_id,
           n.entity_type AS entity_type,
           n.canonical_name AS canonical_name,
           degree
    ORDER BY degree DESC, entity_type, canonical_name
    """
    return _rows(driver, query, threshold=high_degree_threshold)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return not value
    return False


def _find_node_metadata_violations(driver: Any) -> list[dict[str, Any]]:
    query = """
    // graph_validate:all_nodes
    MATCH (n)
    RETURN elementId(n) AS node_id,
           labels(n) AS labels,
           n.entity_type AS entity_type,
           n.canonical_name AS canonical_name,
           properties(n) AS properties
    ORDER BY entity_type, canonical_name
    """
    violations = []

    for row in _rows(driver, query):
        properties = row.get("properties") or {}
        required_fields = ["entity_type", "canonical_name"]
        if row.get("entity_type") in {"Accommodation", "Experience"}:
            required_fields.extend(["extra_id", "name", "source_file"])

        missing_fields = [
            field
            for field in required_fields
            if _is_missing(properties.get(field, row.get(field)))
        ]
        invalid_fields = []
        if "Entity" not in (row.get("labels") or []):
            invalid_fields.append("labels")

        if missing_fields or invalid_fields:
            violation = dict(row)
            if missing_fields:
                violation["missing_fields"] = missing_fields
            if invalid_fields:
                violation["invalid_fields"] = invalid_fields
            violations.append(violation)

    return violations


def _find_relationship_metadata_violations(
    driver: Any,
) -> list[dict[str, Any]]:
    violations = []

    for row in _rows(driver, _RELATIONSHIP_QUERY):
        properties = row.get("properties") or {}
        relation = row.get("relation")
        required_fields = (
            ["distance_meters", "source_file"]
            if relation == "NEARBY"
            else ["source_doc_id", "evidence"]
        )
        missing_fields = [
            field for field in required_fields if _is_missing(properties.get(field))
        ]
        invalid_fields = []
        if relation == "NEARBY" and "distance_meters" not in missing_fields:
            distance = properties.get("distance_meters")
            if (
                not isinstance(distance, (int, float))
                or isinstance(distance, bool)
                or distance < 0
                or not isfinite(distance)
            ):
                invalid_fields.append("distance_meters")

        if missing_fields or invalid_fields:
            violation = {
                key: value
                for key, value in row.items()
                if key != "properties"
            }
            if missing_fields:
                violation["missing_fields"] = missing_fields
            if invalid_fields:
                violation["invalid_fields"] = invalid_fields
            violations.append(violation)

    return violations


def build_graph_validation_report(
    driver: Any,
    high_degree_threshold: int = 100,
) -> dict[str, Any]:
    """Graph 품질 검사 결과와 항목별 건수를 하나의 report로 묶는다."""
    if high_degree_threshold < 1:
        raise ValueError("high_degree_threshold must be positive")

    schema_violations = find_schema_violations(driver)
    duplicate_nodes = find_duplicate_nodes(driver)
    orphan_nodes = find_orphan_nodes(driver)
    high_degree_nodes = _find_high_degree_nodes(driver, high_degree_threshold)
    node_metadata_violations = _find_node_metadata_violations(driver)
    relationship_metadata_violations = _find_relationship_metadata_violations(driver)

    issue_groups = {
        "schema_violation": schema_violations,
        "duplicate_node": duplicate_nodes,
        "orphan_node": orphan_nodes,
        "high_degree_node": high_degree_nodes,
        "node_metadata_violation": node_metadata_violations,
        "relationship_metadata_violation": relationship_metadata_violations,
    }
    report: dict[str, Any] = {
        "high_degree_threshold": high_degree_threshold,
        "total_issue_count": sum(len(rows) for rows in issue_groups.values()),
    }
    for name, rows in issue_groups.items():
        report[f"{name}_count"] = len(rows)
        report[f"{name}s"] = rows

    return report


# 완료 조건: schema violation, duplicate, orphan, suspicious high-degree 수와 상세 목록이 남는다.
# Freeze point: 검사 기준과 report key는 후속 QA가 시작되면 고정한다.
