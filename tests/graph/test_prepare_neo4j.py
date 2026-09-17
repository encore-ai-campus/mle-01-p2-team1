from src.graph.prepare_neo4j import build_nodes, build_relationships, link_accommodations_to_festivals, enrich_accommodations_file


def test_build_nodes_deduplicates_by_type_and_name():
    triples = [{"subject": {"entity_type": "Festival", "canonical_name": "fest"}, "object": {"entity_type": "City", "canonical_name": "seoul"}}, {"subject": {"entity_type": "Festival", "canonical_name": "fest"}, "object": {"entity_type": "City", "canonical_name": "busan"}}]
    assert build_nodes(triples) == [{"entity_type": "Festival", "canonical_name": "fest"}, {"entity_type": "City", "canonical_name": "seoul"}, {"entity_type": "City", "canonical_name": "busan"}]


def test_build_relationships_merges_evidence():
    triples = [{"subject": "fest", "subject_type": "Festival", "relation": "HELD_IN", "object": "seoul", "object_type": "Location", "source_doc_id": "doc-1", "evidence": "one"}, {"subject": "fest", "subject_type": "Festival", "relation": "HELD_IN", "object": "seoul", "object_type": "Location", "source_doc_id": "doc-2", "evidence": "two"}]
    assert build_relationships(triples)[0]["source_doc_id"] == ["doc-1", "doc-2"]
    assert build_relationships(triples)[0]["object"]["canonical_name"] == "seoul"


def test_link_accommodations_to_festivals_keeps_nearest_within_radius():
    accommodations = [{"extra_id": "a1", "source_type": "accommodation", "title": "stay", "latitude": 37.5665, "longitude": 126.9780}]
    festivals = [{"doc_id": "f1", "title": "near", "metadata": {"latitude": 37.5665, "longitude": 126.9780}}, {"doc_id": "f2", "title": "far", "metadata": {"latitude": 37.70, "longitude": 127.10}}]
    linked = link_accommodations_to_festivals(accommodations, festivals, radius_km=3)
    assert linked[0]["related_festival_id"] == "f1"
    assert linked[0]["distance_meters"] == 0


def test_enrich_accommodations_file_writes_linked_jsonl(tmp_path):
    accommodation_path = tmp_path / "accommodations.jsonl"
    festival_path = tmp_path / "festivals.jsonl"
    output_path = tmp_path / "linked.jsonl"
    accommodation_path.write_text('{"extra_id":"a1","title":"stay","latitude":37.5665,"longitude":126.978}\n', encoding="utf-8")
    festival_path.write_text('{"doc_id":"f1","title":"near","metadata":{"latitude":37.5665,"longitude":126.978}}\n', encoding="utf-8")

    enrich_accommodations_file(accommodation_path, festival_path, output_path)

    assert '"related_festival_id": "f1"' in output_path.read_text(encoding="utf-8")


def test_enrich_accommodations_file_excludes_unlinked_records(tmp_path):
    accommodation_path = tmp_path / "accommodations.jsonl"
    festival_path = tmp_path / "festivals.jsonl"
    output_path = tmp_path / "linked.jsonl"
    accommodation_path.write_text(
        '{"extra_id":"near","title":"near","latitude":37.5665,"longitude":126.978}\n'
        '{"extra_id":"far","title":"far","latitude":35.0,"longitude":129.0}\n', encoding="utf-8"
    )
    festival_path.write_text('{"doc_id":"f1","title":"near","metadata":{"latitude":37.5665,"longitude":126.978}}\n', encoding="utf-8")

    enrich_accommodations_file(accommodation_path, festival_path, output_path)

    assert output_path.read_text(encoding="utf-8").count("\n") == 1
