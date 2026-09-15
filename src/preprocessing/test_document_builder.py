import document_builder


def test_build_metadata_with_all_fields():
    festival = {
        "contentid": 12345,
        "title": "서울빛축제",
        "eventstartdate": "20261001",
        "eventenddate": "20261010",
        "addr1": "서울특별시 종로구",
        "mapx": "126.9784",
        "mapy": "37.5667",
        "homepage": "https://example.com",
        "modifiedtime": "20260910120000",
    }

    intro = {
        "sponsor1": "서울특별시",
        "sponsor2": "서울관광재단",
        "eventplace": "청계천",
        "playtime": "18:00~22:00",
        "agelimit": "전 연령",
        "usetimefestival": "무료",
    }

    metadata = document_builder.build_metadata(
        festival,
        intro,
    )

    assert metadata["doc_id"] == "12345"
    assert metadata["title"] == "서울빛축제"

    assert metadata["event_start"] == "20261001"
    assert metadata["event_end"] == "20261010"

    assert metadata["address"] == "서울특별시 종로구"

    assert metadata["longitude"] == 126.9784
    assert metadata["latitude"] == 37.5667

    assert metadata["homepage"] == "https://example.com"
    assert metadata["modified_at"] == "20260910120000"

    assert metadata["sponsor1"] == "서울특별시"
    assert metadata["sponsor2"] == "서울관광재단"
    assert metadata["eventplace"] == "청계천"
    assert metadata["playtime"] == "18:00~22:00"
    assert metadata["agelimit"] == "전 연령"
    assert metadata["usetimefestival"] == "무료"


def test_build_metadata_without_intro():
    festival = {
        "contentid": "12345",
        "title": "서울빛축제",
    }

    metadata = document_builder.build_metadata(
        festival,
        None,
    )

    # intro가 없어도 metadata key는 존재해야 한다.
    assert metadata["sponsor1"] == ""
    assert metadata["sponsor2"] == ""
    assert metadata["eventplace"] == ""
    assert metadata["playtime"] == ""
    assert metadata["agelimit"] == ""
    assert metadata["usetimefestival"] == ""


def test_build_metadata_with_invalid_coordinates():
    festival = {
        "contentid": "12345",
        "title": "좌표 테스트 축제",
        "mapx": "",
        "mapy": "잘못된좌표",
    }

    metadata = document_builder.build_metadata(
        festival,
        None,
    )

    # 빈 좌표는 빈 값 그대로 보존
    assert metadata["longitude"] == ""

    # 잘못된 좌표도 builder에서 버리지 않는다.
    # validation 단계가 나중에 판단한다.
    assert metadata["latitude"] == "잘못된좌표"


def test_build_document_with_empty_text(monkeypatch):
    festival = {
        "contentid": "777",
        "title": "본문 없는 축제",
    }

    # 담당 3의 text_processing 결과가 없다고 가정
    monkeypatch.setattr(
        document_builder,
        "collect_text_parts",
        lambda festival, intro, info_rows: [],
    )

    monkeypatch.setattr(
        document_builder,
        "build_document_text",
        lambda parts: "",
    )

    document = document_builder.build_festival_document(
        festival=festival,
        intro=None,
        info_rows=[],
    )

    # builder는 reject하지 않는다.
    assert document["text"] == ""

    # Document 자체는 정상적으로 생성
    assert document["doc_id"] == "777"


def test_document_and_metadata_use_same_doc_id(monkeypatch):
    festival = {
        "contentid": 99999,
        "title": "ID 테스트 축제",
    }

    monkeypatch.setattr(
        document_builder,
        "collect_text_parts",
        lambda festival, intro, info_rows: ["테스트 본문"],
    )

    monkeypatch.setattr(
        document_builder,
        "build_document_text",
        lambda parts: "테스트 본문",
    )

    document = document_builder.build_festival_document(
        festival=festival,
        intro=None,
        info_rows=[],
    )

    assert document["doc_id"] == "99999"
    assert document["metadata"]["doc_id"] == "99999"
    assert document["doc_id"] == document["metadata"]["doc_id"]