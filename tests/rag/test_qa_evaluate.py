from src.rag.qa_evaluate import evaluate_qa


def test_evaluate_qa_accepts_any_expected_entity_from_list():
    report = evaluate_qa(
        [{"qa_id": "q1", "expected_entity": ["정답A", "정답B"], "expected_answer": "정답A"}],
        [{"qa_id": "q1", "vector_results": ["정답B"], "fulltext_results": ["정답B"], "answer": "정답A입니다."}],
    )

    assert report["vector_hit@5"] == 1.0
    assert report["fulltext_hit@5"] == 1.0
    assert report["answer_contains_rate"] == 1.0


def test_evaluate_qa_accepts_entity_aliases():
    report = evaluate_qa(
        [{"qa_id": "q1", "expected_entity": "정식명", "acceptable_aliases": ["별칭"], "expected_answer": "정답"}],
        [{"qa_id": "q1", "vector_results": ["별칭"], "fulltext_results": ["별칭"], "answer": "정답"}],
    )

    assert report["vector_hit@5"] == 1.0
    assert report["fulltext_hit@5"] == 1.0


def test_evaluate_qa_keeps_search_results_separate_by_index():
    report = evaluate_qa(
        [{"qa_id": "q1", "expected_entity": "정답", "expected_answer": "정답"}],
        [{
            "qa_id": "q1",
            "vector_results_by_index": {"festival_vec": ["오답"], "program_vec": ["정답"]},
            "fulltext_results_by_index": {"festival_fulltext": ["오답"], "program_fulltext": ["정답"]},
            "answer": "정답",
        }],
    )

    assert report["vector_hit@5"] == 1.0
    assert report["fulltext_hit@5"] == 1.0


def test_hit_and_mrr_use_any_index_without_truncating_other_indexes():
    report = evaluate_qa(
        [{"qa_id": "q1", "expected_entity": "정답", "expected_answer": "정답"}],
        [{
            "qa_id": "q1",
            "vector_results_by_index": {
                "festival_vec": ["오답1", "오답2", "오답3", "오답4", "오답5"],
                "program_vec": ["오답1", "정답"],
            },
            "fulltext_results_by_index": {},
            "answer": "정답",
        }],
    )

    assert report["vector_hit@5"] == 1.0
    assert report["vector_mrr"] == 0.5


def test_evaluate_qa_filters_indexes_by_expected_entity_type():
    report = evaluate_qa(
        [{"qa_id": "q1", "expected_entity": "정답", "expected_entity_type": "Program", "expected_answer": "정답"}],
        [{
            "qa_id": "q1",
            "vector_results_by_index": {"festival_vec": ["정답"], "program_vec": ["오답"]},
            "fulltext_results_by_index": {},
            "answer": "정답",
        }],
    )

    assert report["vector_hit@5"] == 0.0
