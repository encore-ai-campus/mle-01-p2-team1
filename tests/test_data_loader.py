from src.ui.data_loader import (
    Festival,
    classify_fee,
    enrich_festivals,
    load_app_data,
    normalize_audiences,
    normalize_region,
    normalize_theme_categories,
)


def test_festival_model_flattens_document_metadata():
    festival = Festival.from_document(
        {
            "doc_id": "123",
            "title": "봄 축제",
            "text": "꽃과 음악",
            "metadata": {
                "event_start": "20260401",
                "event_end": "20260403",
                "address": "서울",
                "longitude": 126.9,
                "latitude": 37.5,
                "eventplace": "공원",
            },
        }
    )

    assert festival.name == "봄 축제"
    assert festival.start_date == "20260401"
    assert festival.latitude == 37.5


def test_load_app_data_returns_serializable_festival_records():
    data = load_app_data()

    assert data["festivals"]
    assert isinstance(data["festivals"][0], dict)
    assert {"name", "text"} <= data["festivals"][0].keys()


def test_normalize_region_uses_province_from_address():
    assert normalize_region("경기도 고양시 일산동구 중앙로 1") == "경기"
    assert normalize_region("서울특별시 종로구 세종대로 1") == "서울"
    assert normalize_region("") == ""


def test_classify_fee_keeps_partial_payment_out_of_free_filter():
    assert classify_fee("무료") == "무료"
    assert classify_fee("무료 (일부 프로그램 유료)") == "유료"
    assert classify_fee("입장권 10,000원") == "유료"
    assert classify_fee("") == ""


def test_normalize_audiences_maps_graph_text_to_stable_categories():
    assert normalize_audiences(["어린이를 동반한 가족", "전 연령"]) == [
        "전 연령",
        "어린이",
        "가족",
    ]


def test_normalize_theme_categories_maps_free_text_to_stable_categories():
    assert normalize_theme_categories(["벚꽃"]) == ["자연생태", "계절축제"]
    assert normalize_theme_categories(["야간 콘서트"]) == ["음악공연", "야간관광"]
    assert normalize_theme_categories(["정체를 알 수 없는 행사"]) == ["기타"]


def test_enrich_festivals_joins_theme_audience_and_relation_count_by_doc_id():
    festivals = [
        {
            "doc_id": "123",
            "name": "봄 축제",
            "address": "서울특별시 종로구",
            "age_limit": "전 연령",
            "usage_fee": "무료",
        }
    ]
    triples = [
        {
            "relation": "HAS_THEME",
            "object": "벚꽃",
            "source_doc_ids": ["123"],
        },
        {
            "relation": "TARGETS",
            "object": "어린이 동반 가족",
            "source_doc_ids": ["123"],
        },
        {
            "relation": "HAS_PROGRAM",
            "object": "봄 음악회",
            "source_doc_ids": ["123"],
        },
    ]

    enriched = enrich_festivals(festivals, triples)[0]

    assert enriched["region"] == "서울"
    assert enriched["themes"] == ["벚꽃"]
    assert enriched["theme_categories"] == ["자연생태", "계절축제"]
    assert enriched["audiences"] == ["전 연령", "어린이", "가족"]
    assert enriched["fee_category"] == "무료"
    assert enriched["relation_count"] == 3
