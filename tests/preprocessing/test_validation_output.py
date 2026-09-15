from src.preprocessing.validation_output import (
    build_preprocessing_report,
    preprocess_documents,
    validate_document,
)


def make_document(doc_id="1", text="x" * 60):
    return {
        "doc_id": doc_id,
        "title": "title",
        "text": text,
        "metadata": {
            "event_start": "20260101",
            "event_end": "20260102",
            "longitude": 126.9,
            "latitude": 37.5,
        },
    }


def test_validate_document_reports_missing_text_and_invalid_metadata():
    document = make_document(text="")
    document["metadata"].update({"event_start": "2026-01-01", "latitude": 99})

    assert validate_document(document) == [
        "missing_text",
        "short_text",
        "invalid_event_start",
        "invalid_latitude",
    ]


def test_preprocess_documents_rejects_duplicate_ids_and_keeps_first():
    processed, rejects, duplicate_count = preprocess_documents(
        [make_document(), make_document()]
    )

    assert len(processed) == 1
    assert rejects[0]["reject_reason"] == ["duplicate_doc_id"]
    assert duplicate_count == 1


def test_report_counts_reject_categories():
    processed = [make_document()]
    rejects = [
        {"reject_reason": ["duplicate_doc_id"]},
        {"reject_reason": ["short_text"]},
        {"reject_reason": ["missing_text"]},
        {"reject_reason": ["invalid_latitude"]},
    ]

    report = build_preprocessing_report(processed, rejects, 5, 1)

    assert report["duplicate_removed_count"] == 1
    assert report["short_text_removed_count"] == 1
    assert report["missing_text_count"] == 1
    assert report["other_removed_count"] == 1
    assert report["reject_count"] == 4
