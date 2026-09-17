import pytest

from src.graph.graph_validate import (
    build_graph_validation_report,
    find_duplicate_nodes,
    find_orphan_nodes,
    find_schema_violations,
)


class FakeRecord(dict):
    def data(self):
        return dict(self)


class FakeResult:
    def __init__(self, rows):
        self._rows = [FakeRecord(row) for row in rows]

    def __iter__(self):
        return iter(self._rows)


class FakeSession:
    def __init__(self, responses, queries):
        self._responses = responses
        self._queries = queries
        self.last_query = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def run(self, query, **parameters):
        self.last_query = query
        self._queries.append(query)
        for marker, rows in self._responses.items():
            if marker in query:
                if marker == "graph_validate:high_degree_nodes":
                    assert parameters == {"threshold": 10}
                return FakeResult(rows)
        raise AssertionError(f"Unexpected query: {query}")


class FakeDriver:
    def __init__(self, responses):
        self._responses = responses
        self.last_session = None
        self.queries = []

    def session(self):
        self.last_session = FakeSession(self._responses, self.queries)
        return self.last_session


def relationship_row(subject_type, relation, object_type, **overrides):
    row = {
        "subject_id": "s-1",
        "subject_labels": ["Entity"],
        "subject_type": subject_type,
        "subject": "subject",
        "relation": relation,
        "object_id": "o-1",
        "object_labels": ["Entity"],
        "object_type": object_type,
        "object": "object",
        "properties": {
            "source_doc_id": ["doc-1"],
            "evidence": ["source evidence"],
        },
    }
    row.update(overrides)
    return row


def test_find_schema_violations_accepts_ontology_and_nearby_signatures():
    rows = [
        relationship_row("Festival", "HELD_IN", "Location"),
        relationship_row("Festival", "NEARBY", "Accommodation"),
        relationship_row("Festival", "NEARBY", "Experience"),
    ]
    driver = FakeDriver({"graph_validate:all_relationships": rows})

    assert find_schema_violations(driver) == []


def test_find_schema_violations_classifies_direction_relation_and_signature_errors():
    rows = [
        relationship_row("Location", "HELD_IN", "Festival"),
        relationship_row("Festival", "MADE_UP", "Location"),
        relationship_row("Artist", "ORGANIZES", "Festival"),
    ]
    driver = FakeDriver({"graph_validate:all_relationships": rows})

    violations = find_schema_violations(driver)

    assert [row["error_code"] for row in violations] == [
        "REVERSED_DIRECTION",
        "UNKNOWN_RELATION",
        "SIGNATURE_INVALID",
    ]
    assert violations[0]["subject_type"] == "Location"
    assert violations[0]["object_type"] == "Festival"


def test_find_schema_violations_reports_unknown_entity_types():
    rows = [
        relationship_row("UnknownType", "HELD_IN", "Location"),
    ]
    driver = FakeDriver({"graph_validate:all_relationships": rows})

    violations = find_schema_violations(driver)

    assert violations[0]["error_code"] == "UNKNOWN_ENTITY_TYPE"


def test_find_schema_violations_scans_relationships_without_label_filter():
    driver = FakeDriver({"graph_validate:all_relationships": []})

    find_schema_violations(driver)

    query = driver.last_session.last_query
    assert "MATCH (s)-[r]->(o)" in query
    assert "labels(s) AS subject_labels" in query
    assert "labels(o) AS object_labels" in query


def test_find_schema_violations_reports_invalid_endpoint_labels():
    row = relationship_row(
        "Festival",
        "HELD_IN",
        "Location",
        subject_labels=["Festival"],
    )
    driver = FakeDriver({"graph_validate:all_relationships": [row]})

    violations = find_schema_violations(driver)

    assert violations[0]["error_code"] == "INVALID_ENDPOINT_LABEL"


def test_find_duplicate_nodes_returns_duplicate_identity_and_node_ids():
    rows = [
        {
            "entity_type": "Festival",
            "canonical_name": "축제",
            "duplicate_count": 2,
            "node_ids": ["n-1", "n-2"],
        }
    ]
    driver = FakeDriver({"graph_validate:duplicate_nodes": rows})

    assert find_duplicate_nodes(driver) == rows

    query = driver.last_session.last_query
    before_grouping, after_grouping = query.split("WITH", maxsplit=1)
    assert "trim(n.entity_type) <> ''" in before_grouping
    assert "trim(n.canonical_name) <> ''" in before_grouping
    assert "collect(elementId(n)) AS node_ids" in after_grouping
    assert "count(*) AS duplicate_count" in after_grouping
    assert "WHERE duplicate_count > 1" in after_grouping


def test_find_orphan_nodes_returns_unconnected_nodes():
    rows = [
        {
            "node_id": "n-3",
            "entity_type": "Program",
            "canonical_name": "체험 프로그램",
        }
    ]
    driver = FakeDriver({"graph_validate:orphan_nodes": rows})

    assert find_orphan_nodes(driver) == rows
    assert "WHERE NOT (n)--()" in driver.last_session.last_query


def test_graph_report_high_degree_query_counts_relationships_and_uses_threshold():
    responses = {
        "graph_validate:all_relationships": [],
        "graph_validate:duplicate_nodes": [],
        "graph_validate:orphan_nodes": [],
        "graph_validate:high_degree_nodes": [],
        "graph_validate:all_nodes": [],
    }
    driver = FakeDriver(responses)

    build_graph_validation_report(driver, high_degree_threshold=10)

    query = next(
        query
        for query in driver.queries
        if "graph_validate:high_degree_nodes" in query
    )
    assert "OPTIONAL MATCH (n)-[r]-()" in query
    assert "count(r) AS degree" in query
    assert "WHERE degree > $threshold" in query


def test_graph_report_scans_all_nodes_and_reports_invalid_labels():
    responses = {
        "graph_validate:all_relationships": [],
        "graph_validate:duplicate_nodes": [],
        "graph_validate:orphan_nodes": [],
        "graph_validate:high_degree_nodes": [],
        "graph_validate:all_nodes": [
            {
                "node_id": "n-1",
                "labels": ["Festival"],
                "entity_type": "Festival",
                "canonical_name": "축제",
                "properties": {
                    "entity_type": "Festival",
                    "canonical_name": "축제",
                },
            }
        ],
    }
    driver = FakeDriver(responses)

    report = build_graph_validation_report(driver, high_degree_threshold=10)

    node_queries = [
        query
        for query in driver.queries
        if "graph_validate:duplicate_nodes" in query
        or "graph_validate:orphan_nodes" in query
        or "graph_validate:high_degree_nodes" in query
        or "graph_validate:all_nodes" in query
    ]
    assert all("MATCH (n)" in query for query in node_queries)
    assert report["node_metadata_violations"][0]["invalid_fields"] == ["labels"]


def test_build_graph_validation_report_collects_counts_and_details():
    invalid_relationship = relationship_row(
        "Location",
        "HELD_IN",
        "Festival",
        properties={},
    )
    responses = {
        "graph_validate:all_relationships": [invalid_relationship],
        "graph_validate:duplicate_nodes": [
            {
                "entity_type": "Festival",
                "canonical_name": "축제",
                "duplicate_count": 2,
                "node_ids": ["n-1", "n-2"],
            }
        ],
        "graph_validate:orphan_nodes": [
            {
                "node_id": "n-3",
                "entity_type": "Program",
                "canonical_name": "고립 프로그램",
            }
        ],
        "graph_validate:high_degree_nodes": [
            {
                "node_id": "n-4",
                "entity_type": "Audience",
                "canonical_name": "관광객",
                "degree": 11,
            }
        ],
        "graph_validate:all_nodes": [
            {
                "node_id": "n-5",
                "labels": ["Entity"],
                "entity_type": None,
                "canonical_name": "이름만 있음",
                "properties": {"canonical_name": "이름만 있음"},
            }
        ],
    }
    driver = FakeDriver(responses)

    report = build_graph_validation_report(driver, high_degree_threshold=10)

    assert report["schema_violation_count"] == 1
    assert report["duplicate_node_count"] == 1
    assert report["orphan_node_count"] == 1
    assert report["high_degree_node_count"] == 1
    assert report["node_metadata_violation_count"] == 1
    assert report["relationship_metadata_violation_count"] == 1
    assert report["total_issue_count"] == 6
    assert report["schema_violations"][0]["error_code"] == "REVERSED_DIRECTION"
    assert report["node_metadata_violations"][0]["missing_fields"] == ["entity_type"]
    assert report["relationship_metadata_violations"][0]["missing_fields"] == [
        "source_doc_id",
        "evidence",
    ]


def test_build_graph_validation_report_validates_high_degree_threshold():
    driver = FakeDriver({})

    with pytest.raises(ValueError, match="high_degree_threshold must be positive"):
        build_graph_validation_report(driver, high_degree_threshold=0)


def test_build_graph_validation_report_checks_extra_and_nearby_metadata():
    nearby_relationship = relationship_row(
        "Festival",
        "NEARBY",
        "Accommodation",
        properties={"distance_meters": -1, "source_file": ""},
    )
    responses = {
        "graph_validate:all_relationships": [nearby_relationship],
        "graph_validate:duplicate_nodes": [],
        "graph_validate:orphan_nodes": [],
        "graph_validate:high_degree_nodes": [],
        "graph_validate:all_nodes": [
            {
                "node_id": "stay-1",
                "labels": ["Entity"],
                "entity_type": "Accommodation",
                "canonical_name": "숙소",
                "properties": {
                    "entity_type": "Accommodation",
                    "canonical_name": "숙소",
                },
            }
        ],
    }
    driver = FakeDriver(responses)

    report = build_graph_validation_report(driver, high_degree_threshold=10)

    assert report["node_metadata_violations"][0]["missing_fields"] == [
        "extra_id",
        "name",
        "source_file",
    ]
    assert report["relationship_metadata_violations"][0]["missing_fields"] == [
        "source_file",
    ]
    assert report["relationship_metadata_violations"][0]["invalid_fields"] == [
        "distance_meters",
    ]


def test_build_graph_validation_report_rejects_non_finite_nearby_distance():
    nearby_relationship = relationship_row(
        "Festival",
        "NEARBY",
        "Experience",
        properties={"distance_meters": float("nan"), "source_file": "nearby.jsonl"},
    )
    responses = {
        "graph_validate:all_relationships": [nearby_relationship],
        "graph_validate:duplicate_nodes": [],
        "graph_validate:orphan_nodes": [],
        "graph_validate:high_degree_nodes": [],
        "graph_validate:all_nodes": [],
    }
    driver = FakeDriver(responses)

    report = build_graph_validation_report(driver, high_degree_threshold=10)

    assert report["relationship_metadata_violations"][0]["invalid_fields"] == [
        "distance_meters",
    ]
