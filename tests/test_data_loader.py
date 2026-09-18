from src.ui.data_loader import Festival, load_app_data


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
