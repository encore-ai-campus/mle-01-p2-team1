from src.rag.text2cypher import generate_cypher, validate_read_only_cypher


class FakeLLM:
    def __init__(self, content: str):
        self.content = content

    def invoke(self, _prompt: str):
        return type("Response", (), {"content": self.content})()


def test_generate_cypher_removes_trailing_invalid_unicode_after_order_by():
    llm = FakeLLM(
        "MATCH (f:Festival) RETURN f.canonical_name AS festival_name "
        "ORDER BY festival_name \U000fffff"
    )

    assert generate_cypher("축제 목록", llm) == (
        "MATCH (f:Festival) RETURN f.canonical_name AS festival_name "
        "ORDER BY festival_name"
    )


def test_validator_allows_accommodation_properties_when_label_identifies_type():
    validate_read_only_cypher(
        "MATCH (f:Festival)-[r:NEARBY]->(a:Accommodation) "
        "WHERE f.canonical_name CONTAINS '달밤에체조 부산 챌린지' "
        "RETURN a.canonical_name, a.name, a.address, r.distance_meters "
        "ORDER BY r.distance_meters ASC"
    )


def test_validator_allows_untyped_read_only_relationship_for_evidence_search():
    validate_read_only_cypher(
        "MATCH (f:Festival)-[r:HELD_IN]->(l:Location) "
        "WHERE EXISTS { MATCH (f)-[s]->(x) "
        "WHERE x.canonical_name CONTAINS '봄' "
        "OR any(e IN coalesce(s.evidence, []) WHERE e CONTAINS '봄') } "
        "RETURN f.canonical_name"
    )
