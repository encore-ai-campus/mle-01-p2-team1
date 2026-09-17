from copy import deepcopy

import pytest

from src.graph.load_neo4j import load_nodes, load_relationships


class FakeCounters:
    relationships_created = 1


class FakeSummary:
    counters = FakeCounters()


class FakeResult:
    def consume(self):
        return FakeSummary()


class FakeSession:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def run(self, query, **parameters):
        self.calls.append((query, parameters))
        return FakeResult()


class FakeDriver:
    def __init__(self):
        self.fake_session = FakeSession()

    def session(self):
        return self.fake_session


class FailingResult:
    def consume(self):
        raise RuntimeError("boom")


class FailingSession(FakeSession):
    def run(self, query, **parameters):
        return FailingResult()


class FailingDriver:
    def session(self):
        return FailingSession()


def test_load_nodes_records_failed_batch_before_reraising():
    failures = []
    with pytest.raises(RuntimeError, match="boom"):
        load_nodes(FailingDriver(), [{"entity_type": "Festival", "canonical_name": "A"}], failure_log=failures)
    assert failures == [{"operation": "nodes", "batch_index": 0, "start": 0, "end": 1, "error": "boom"}]


def test_load_relationships_sends_only_flat_metadata_as_properties():
    relationships = [
        {
            "subject": {
                "entity_type": "Festival",
                "canonical_name": "축제",
            },
            "relation": "HELD_IN",
            "object": {
                "entity_type": "Location",
                "canonical_name": "서울",
            },
            "source_doc_id": ["doc-1"],
            "evidence": ["서울에서 열린다."],
        }
    ]
    original = deepcopy(relationships)
    driver = FakeDriver()

    written = load_relationships(driver, relationships)

    query, parameters = driver.fake_session.calls[0]
    assert written == 1
    assert "SET r += item.properties" in query
    assert parameters["rows"] == [
        {
            "subject": relationships[0]["subject"],
            "relation": "HELD_IN",
            "object": relationships[0]["object"],
            "properties": {
                "source_doc_id": ["doc-1"],
                "evidence": ["서울에서 열린다."],
            },
        }
    ]
    assert relationships == original


@pytest.mark.parametrize(
    "invalid_value",
    [
        {"nested": "value"},
        [["nested"]],
        ["doc-1", 2],
    ],
)
def test_load_relationships_rejects_illegal_neo4j_property_values(invalid_value):
    relationships = [
        {
            "subject": {
                "entity_type": "Festival",
                "canonical_name": "축제",
            },
            "relation": "HELD_IN",
            "object": {
                "entity_type": "Location",
                "canonical_name": "서울",
            },
            "bad_metadata": invalid_value,
        }
    ]
    driver = FakeDriver()

    with pytest.raises(
        ValueError,
        match="bad_metadata.*Neo4j relationship property",
    ):
        load_relationships(driver, relationships)

    assert driver.fake_session.calls == []
