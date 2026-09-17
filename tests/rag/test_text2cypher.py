import logging
from types import SimpleNamespace

import pytest

from src.rag.text2cypher import (
    TEXT2CYPHER_PROMPT,
    build_graph_schema_block,
    build_text2cypher_prompt,
    execute_text2cypher,
    validate_read_only_cypher,
)


class _FakeSession:
    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def run(self, cypher):
        self.driver.executed_queries.append(cypher)
        return [{"festival": "Seoul Lantern Festival"}]


class _FakeDriver:
    def __init__(self):
        self.session_calls = 0
        self.executed_queries = []

    def session(self):
        self.session_calls += 1
        return _FakeSession(self)


class _FakeLLM:
    def __init__(self, cypher):
        self.cypher = cypher

    def invoke(self, prompt):
        return SimpleNamespace(content=self.cypher)


@pytest.mark.parametrize("keyword", ["CREATE", "MERGE", "DELETE", "SET", "REMOVE"])
def test_validate_read_only_cypher_rejects_write_keywords(keyword: str):
    with pytest.raises(ValueError):
        validate_read_only_cypher(f"MATCH (n) {keyword} n.flag = true RETURN n")


def test_validate_read_only_cypher_rejects_write_keywords_case_insensitively():
    with pytest.raises(ValueError):
        validate_read_only_cypher("match (n) delete n")


def test_validate_read_only_cypher_allows_read_only_query_and_keyword_substrings():
    validate_read_only_cypher("MATCH (n {canonical_name: 'Sunset'}) RETURN n")


def test_validate_read_only_cypher_rejects_unbalanced_syntax():
    with pytest.raises(ValueError, match="Invalid Cypher syntax"):
        validate_read_only_cypher("MATCH (n:Entity RETURN n")


@pytest.mark.parametrize(
    "cypher",
    [
        "MATCH (n:Place) RETURN n",
        "MATCH (n:Entity)-[:LOCATED_AT]->(m:Entity) RETURN n",
        "MATCH (n:Entity) WHERE n.name = 'festival' RETURN n",
        "MATCH (n:Entity {entity_type: 'Place'}) RETURN n",
    ],
)
def test_validate_read_only_cypher_rejects_schema_outside_ontology(cypher: str):
    with pytest.raises(ValueError, match="not allowed by the graph schema"):
        validate_read_only_cypher(cypher)


def test_validate_read_only_cypher_accepts_allowed_schema():
    validate_read_only_cypher(
        "MATCH (f:Entity {entity_type: 'Festival'})-[:HELD_IN]->"
        "(l:Entity {entity_type: 'Location'}) "
        "WHERE l.canonical_name = 'Seoul' RETURN f"
    )


def test_build_graph_schema_block_describes_entity_nodes_and_directed_relationships():
    block = build_graph_schema_block()

    assert "Node label: Entity" in block
    assert "entity_type" in block
    assert "canonical_name" in block
    assert "(:Entity {entity_type: 'Festival'})-[:HELD_IN]->(:Entity {entity_type: 'Location'})" in block
    assert "(:Entity {entity_type: 'Organization'})-[:ORGANIZES]->(:Entity {entity_type: 'Festival'})" in block
    assert "(:Entity {entity_type: 'Location'})-[:HELD_IN]->(:Entity {entity_type: 'Festival'})" not in block


def test_build_graph_schema_block_describes_nearby_accommodations_and_experiences():
    block = build_graph_schema_block()

    assert "(:Entity {entity_type: 'Accommodation'})" in block
    assert "(:Entity {entity_type: 'Experience'})" in block
    assert (
        "(:Entity {entity_type: 'Festival'})-[:NEARBY]->"
        "(:Entity {entity_type: 'Accommodation'})"
    ) in block
    assert (
        "(:Entity {entity_type: 'Festival'})-[:NEARBY]->"
        "(:Entity {entity_type: 'Experience'})"
    ) in block


def test_build_graph_schema_block_describes_queryable_metadata():
    block = build_graph_schema_block()

    assert "Node properties:" in block
    assert "extra_id: string" in block
    assert "latitude: number" in block
    assert "longitude: number" in block
    assert "Relationship properties:" in block
    assert "source_doc_id: list[string]" in block
    assert "evidence: list[string]" in block
    assert "distance_meters: number" in block


def test_validate_read_only_cypher_accepts_queryable_metadata():
    validate_read_only_cypher(
        "MATCH (f:Entity {entity_type: 'Festival'})-[r:NEARBY]->"
        "(a:Entity {entity_type: 'Accommodation'}) "
        "WHERE r.distance_meters <= 1000 "
        "RETURN a.name, a.address, a.latitude, a.longitude, a.text, "
        "a.source_file, r.distance_meters, r.source_file"
    )
    validate_read_only_cypher(
        "MATCH (f:Entity {entity_type: 'Festival'})-[r:HELD_IN]->"
        "(l:Entity {entity_type: 'Location'}) "
        "RETURN r.source_doc_id, r.evidence"
    )


def test_text2cypher_prompt_constrains_generated_query_to_graph_schema():
    prompt = build_text2cypher_prompt("어떤 축제가 열리나요?")

    assert prompt == TEXT2CYPHER_PROMPT.format(
        schema=build_graph_schema_block(), question="어떤 축제가 열리나요?"
    )
    assert "스키마에 없는 label이나 relation을 만들거나 사용하지 마세요" in prompt
    assert "Entity 라벨만 사용하세요" in prompt
    assert "읽기 전용 Cypher" in prompt
    assert "어떤 축제가 열리나요?" in prompt


def test_execute_text2cypher_runs_validated_query_and_logs_audit_fields(caplog):
    question = "서울에서 열리는 축제는?"
    cypher = (
        "MATCH (f:Entity {entity_type: 'Festival'})-[:HELD_IN]->"
        "(l:Entity {entity_type: 'Location'}) RETURN f"
    )
    driver = _FakeDriver()
    caplog.set_level(logging.INFO, logger="src.rag.text2cypher")

    result = execute_text2cypher(driver, question, _FakeLLM(cypher))

    assert result == [{"festival": "Seoul Lantern Festival"}]
    assert driver.executed_queries == [cypher]
    audit_record = caplog.records[-1]
    assert audit_record.question == question
    assert audit_record.cypher == cypher
    assert audit_record.error is None


def test_execute_text2cypher_does_not_run_unsafe_query_and_logs_error(caplog):
    question = "모든 노드를 삭제해 줘"
    cypher = "MATCH (n) DELETE n RETURN n"
    driver = _FakeDriver()
    caplog.set_level(logging.ERROR, logger="src.rag.text2cypher")

    with pytest.raises(ValueError, match="Write operations are not allowed"):
        execute_text2cypher(driver, question, _FakeLLM(cypher))

    assert driver.session_calls == 0
    audit_record = caplog.records[-1]
    assert audit_record.question == question
    assert audit_record.cypher == cypher
    assert "Write operations are not allowed" in audit_record.error
