from src.preprocessing.text_processing import (
    build_document_text,
    collect_text_parts,
)


def test_collect_text_parts_keeps_only_supported_string_fields_in_order():
    result = collect_text_parts(
        {"overview": " overview ", "title": "ignored"},
        {"program": "program", "subevent": None, "placeinfo": 123},
        [{"infotext": "info"}, {"infotext": {"bad": "value"}}],
    )

    assert result == [" overview ", "info", "program"]


def test_build_document_text_cleans_entities_and_removes_duplicates():
    assert build_document_text(["<b>A</b> &amp; B", " A & B ", " "]) == "A & B"
