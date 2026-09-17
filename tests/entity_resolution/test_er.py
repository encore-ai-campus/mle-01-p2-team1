from src.entity_resolution.er import (
    _as_triple_dict,
    normalize_comparison_name,
    replace_with_canonical_names,
    resolve_entities,
    build_er_report,
)


def test_normalization_preserves_korean_and_removes_formatting():
    assert normalize_comparison_name("  부산  축제(2024) [공식] ") == "부산 축제"


def test_plain_model_dump_with_flat_triple_fields_is_supported():
    class TripleModel:
        def model_dump(self):
            return {"subject": "축제", "subject_type": "Festival"}

    assert _as_triple_dict(TripleModel())["subject"] == "축제"


def test_fuzzy_matches_require_review_and_do_not_auto_merge():
    mentions = [
        {"mention_id": "1:subject", "name": "도아세", "entity_type": "Festival"},
        {"mention_id": "2:subject", "name": "도아세이", "entity_type": "Festival"},
    ]
    result = resolve_entities(mentions)
    assert len(result["entities"]) == 2
    assert result["candidates"][0]["decision"] == "review"


def test_replacement_uses_normalized_name():
    triples = [{"subject": " 부산 축제 ", "subject_type": "Festival", "object": "장소", "object_type": "Location"}]
    resolution = {"name_mapping": [{"entity_type": "Festival", "original_name": "부산 축제", "canonical_name": "부산국제축제"}]}
    assert replace_with_canonical_names(triples, resolution)[0]["subject"] == "부산국제축제"


def test_er_report_contains_rates_decision_counts_and_consistency():
    mentions = [
        {"mention_id": "1", "name": "A", "entity_type": "Festival"},
        {"mention_id": "2", "name": "B", "entity_type": "Festival"},
    ]
    resolution = {
        "entities": [{"entity_id": "entity_0", "canonical_name": "A", "entity_type": "Festival", "mention_ids": ["1"]}],
        "mention_to_entity": {"1": "entity_0"},
        "candidates": [
            {"decision": "exact_merge"},
            {"decision": "review", "candidate_type": "fuzzy", "human_decision": "approved_merge"},
            {"decision": "review", "candidate_type": "embedding", "human_decision": "rejected_merge"},
        ],
    }
    report = build_er_report(mentions, resolution)
    assert report["entity_count_before"] == 2
    assert report["entity_reduction_rate"] == 0.5
    assert report["exact_merge_count"] == 1
    assert report["fuzzy_review_count"] == 1
    assert report["embedding_review_count"] == 1
    assert report["approved_merge_count"] == 1
    assert report["rejected_merge_count"] == 1
    assert report["merge_precision"] == 0.5
    assert report["er_consistency"] == 0.5
