import importlib
import json

import pytest


MODULE_NAME = "src.preprocessing.load_data_user"


def load_module():
    return importlib.import_module(MODULE_NAME)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_load_json_reads_a_json_array_without_changing_values(tmp_path):
    path = tmp_path / "rows.json"
    expected = [{"contentid": 123, "title": "테스트 축제"}]
    path.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")

    result = load_module().load_json(path)

    assert result == expected
    assert result is not expected


def test_load_json_returns_an_empty_array(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("[]", encoding="utf-8")

    assert load_module().load_json(path) == []


def test_load_json_keeps_file_not_found_error_distinguishable(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_module().load_json(missing_path)


def test_load_json_keeps_json_decode_error_distinguishable(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("[{", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_module().load_json(path)


def test_normalize_festival_converts_id_and_supplies_missing_fields():
    row = {
        "contentid": 123,
        "title": "테스트 축제",
        "eventstartdate": "20260101",
        "eventenddate": "20260102",
        "addr1": "서울",
        "mapx": "126.9",
        "mapy": "37.5",
        "homepage": "https://example.com",
        "modifiedtime": "20251231235959",
    }

    result = load_module().normalize_festival(row)

    assert result == {
        "contentid": "123",
        "title": "테스트 축제",
        "eventstartdate": "20260101",
        "eventenddate": "20260102",
        "addr1": "서울",
        "mapx": "126.9",
        "mapy": "37.5",
        "homepage": "https://example.com",
        "modifiedtime": "20251231235959",
        "overview": "",
    }


def test_normalize_festival_does_not_modify_the_input_row():
    row = {"contentid": 7, "title": "원본"}
    original = row.copy()

    load_module().normalize_festival(row)

    assert row == original


def test_build_lookup_skips_missing_ids_and_records_duplicate_ids():
    rows = [
        {"contentid": "1", "value": "first"},
        {"title": "ID 없음"},
        {"contentid": " ", "title": "빈 ID"},
        {"contentid": 1, "value": "duplicate"},
    ]
    missing_rows = []
    duplicate_ids = []

    result = load_module().build_lookup(
        rows,
        missing_rows=missing_rows,
        duplicate_ids=duplicate_ids,
    )

    assert result == {"1": rows[0]}
    assert missing_rows == [
        {"row_index": 1, "row": rows[1]},
        {"row_index": 2, "row": rows[2]},
    ]
    assert duplicate_ids == ["1"]


def test_build_lookup_groups_multiple_rows_for_the_same_id():
    rows = [
        {"contentid": "1", "value": "first"},
        {"contentid": "1", "value": "second"},
        {"contentid": "2", "value": "third"},
    ]

    result = load_module().build_lookup(rows, multiple=True)

    assert dict(result) == {
        "1": [rows[0], rows[1]],
        "2": [rows[2]],
    }


def test_build_intro_lookup_unwraps_the_first_detail_record():
    detail = {"contentid": "10", "program": "체험 프로그램"}
    rows = [
        {
            "contentid": 10,
            "title": "테스트 축제",
            "intro": [detail, {"contentid": "10", "program": "두 번째"}],
            "error": None,
        }
    ]

    result = load_module().build_intro_lookup(rows)

    assert result == {"10": detail}


def test_build_intro_lookup_records_api_errors_and_empty_wrappers():
    rows = [
        {"contentid": "10", "intro": [], "error": None},
        {"contentid": "11", "intro": [], "error": "API timeout"},
    ]
    skipped_rows = []

    result = load_module().build_intro_lookup(rows, skipped_rows=skipped_rows)

    assert result == {}
    assert skipped_rows == [
        {"row_index": 0, "contentid": "10", "reason": "empty_intro"},
        {
            "row_index": 1,
            "contentid": "11",
            "reason": "api_error",
            "error": "API timeout",
        },
    ]


def test_build_info_lookup_unwraps_and_groups_all_detail_records():
    first = {
        "contentid": "10",
        "infoname": "행사소개",
        "infotext": "축제 설명",
    }
    second = {
        "contentid": "10",
        "infoname": "행사내용",
        "infotext": "프로그램 설명",
    }
    rows = [
        {
            "contentid": "10",
            "title": "테스트 축제",
            "info": [first, second],
            "error": None,
        }
    ]

    result = load_module().build_info_lookup(rows)

    assert dict(result) == {"10": [first, second]}


def test_build_info_lookup_records_api_errors_and_empty_wrappers():
    rows = [
        {"contentid": "10", "info": [], "error": None},
        {"contentid": "11", "info": [], "error": "API timeout"},
    ]
    skipped_rows = []

    result = load_module().build_info_lookup(rows, skipped_rows=skipped_rows)

    assert dict(result) == {}
    assert skipped_rows == [
        {"row_index": 0, "contentid": "10", "reason": "empty_info"},
        {
            "row_index": 1,
            "contentid": "11",
            "reason": "api_error",
            "error": "API timeout",
        },
    ]


def test_select_info_texts_keeps_only_nonempty_description_items_in_order():
    items = [
        {"infoname": "행사소개", "infotext": "축제 설명"},
        {"infoname": "전화번호", "infotext": "02-1234-5678"},
        {"infoname": "행사내용", "infotext": "  "},
        {"infoname": "출연", "infotext": "가수 A"},
        {"infoname": "홈페이지", "infotext": "https://example.com"},
        {"infoname": "이용요금", "infotext": "10,000원"},
    ]

    result = load_module().select_info_texts(items)

    assert result == ["축제 설명", "가수 A"]


def test_load_festival_sources_returns_named_data_and_diagnostics(tmp_path):
    festival_rows = [
        {"contentid": 10, "title": "정상 축제", "overview": "설명"},
        {"title": "ID 없는 축제"},
        {"contentid": "10", "title": "중복 축제"},
    ]
    intro_detail = {"contentid": "10", "program": "프로그램"}
    intro_rows = [
        {"contentid": "10", "intro": [intro_detail], "error": None},
        {"contentid": "20", "intro": [], "error": "API 오류"},
    ]
    info_detail = {
        "contentid": "10",
        "infoname": "행사소개",
        "infotext": "축제 상세 설명",
    }
    info_rows = [
        {"contentid": "10", "info": [info_detail], "error": None},
        {"contentid": "20", "info": [], "error": None},
    ]
    write_json(tmp_path / "data/raw/festival_raw.json", festival_rows)
    write_json(tmp_path / "data/extra/festival_intro_2026.json", intro_rows)
    write_json(tmp_path / "data/extra/festival_info_2026.json", info_rows)

    result = load_module().load_festival_sources(tmp_path)

    assert [row["contentid"] for row in result.festival_rows] == ["10", "", "10"]
    assert result.intro_lookup == {"10": intro_detail}
    assert dict(result.info_lookup) == {"10": [info_detail]}
    assert result.diagnostics.festival_missing_rows == [
        {"row_index": 1, "row": festival_rows[1]}
    ]
    assert result.diagnostics.festival_duplicate_ids == ["10"]
    assert result.diagnostics.intro_skipped_rows == [
        {
            "row_index": 1,
            "contentid": "20",
            "reason": "api_error",
            "error": "API 오류",
        }
    ]
    assert result.diagnostics.info_skipped_rows == [
        {"row_index": 1, "contentid": "20", "reason": "empty_info"}
    ]


@pytest.mark.parametrize(
    ("relative_path", "value", "path_fragment"),
    [
        ("data/raw/festival_raw.json", {"contentid": "10"}, "festival_raw.json"),
        ("data/extra/festival_intro_2026.json", {}, "festival_intro_2026.json"),
        ("data/extra/festival_info_2026.json", {}, "festival_info_2026.json"),
    ],
)
def test_load_festival_sources_rejects_non_list_top_level(
    tmp_path, relative_path, value, path_fragment
):
    write_json(tmp_path / "data/raw/festival_raw.json", [])
    write_json(tmp_path / "data/extra/festival_intro_2026.json", [])
    write_json(tmp_path / "data/extra/festival_info_2026.json", [])
    write_json(tmp_path / relative_path, value)

    with pytest.raises(TypeError, match=path_fragment) as exc_info:
        load_module().load_festival_sources(tmp_path)

    assert "list" in str(exc_info.value)


def test_load_festival_sources_reports_path_and_row_for_non_dict_row(tmp_path):
    write_json(tmp_path / "data/raw/festival_raw.json", [{"contentid": "10"}, 99])
    write_json(tmp_path / "data/extra/festival_intro_2026.json", [])
    write_json(tmp_path / "data/extra/festival_info_2026.json", [])

    with pytest.raises(TypeError) as exc_info:
        load_module().load_festival_sources(tmp_path)

    message = str(exc_info.value)
    assert "festival_raw.json" in message
    assert "row 1" in message
    assert "dict" in message


@pytest.mark.parametrize(
    ("filename", "row", "missing_field"),
    [
        ("festival_intro_2026.json", {"contentid": "10", "error": None}, "intro"),
        ("festival_info_2026.json", {"contentid": "10", "error": None}, "info"),
        ("festival_intro_2026.json", {"intro": [], "error": None}, "contentid"),
        ("festival_info_2026.json", {"info": [], "error": None}, "contentid"),
    ],
)
def test_load_festival_sources_reports_required_wrapper_field(
    tmp_path, filename, row, missing_field
):
    write_json(tmp_path / "data/raw/festival_raw.json", [])
    write_json(tmp_path / "data/extra/festival_intro_2026.json", [])
    write_json(tmp_path / "data/extra/festival_info_2026.json", [])
    write_json(tmp_path / "data/extra" / filename, [row])

    with pytest.raises(ValueError) as exc_info:
        load_module().load_festival_sources(tmp_path)

    message = str(exc_info.value)
    assert filename in message
    assert "row 0" in message
    assert missing_field in message


def test_load_festival_sources_reports_nested_non_dict_detail(tmp_path):
    write_json(tmp_path / "data/raw/festival_raw.json", [])
    write_json(
        tmp_path / "data/extra/festival_intro_2026.json",
        [{"contentid": "10", "intro": ["잘못된 상세값"], "error": None}],
    )
    write_json(tmp_path / "data/extra/festival_info_2026.json", [])

    with pytest.raises(TypeError) as exc_info:
        load_module().load_festival_sources(tmp_path)

    message = str(exc_info.value)
    assert "festival_intro_2026.json" in message
    assert "row 0" in message
    assert "intro[0]" in message
