from src.ui.components import festival_image, format_festival_date, region_label


def test_festival_image_prefers_nested_metadata_image():
    row = {"metadata": {"firstimage": "https://example.com/festival.jpg"}}
    assert festival_image(row) == "https://example.com/festival.jpg"


def test_format_festival_date_formats_tour_api_dates():
    assert format_festival_date("20260501") == "2026.05.01"


def test_region_label_extracts_short_province_name():
    assert region_label({"address": "경기도 고양시 일산서구"}) == "경기"
