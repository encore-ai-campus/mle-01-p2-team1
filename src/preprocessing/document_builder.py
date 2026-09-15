"""
담당 4. Festival Document 및 metadata 생성 가이드

festival_raw의 flat 필드, intro/info lookup, 담당 3의 text를 결합한다.
축제 한 건을 입력받으면 Document 한 건만 반환하는 것이 핵심 계약이다.

이 파일은:
- 파일을 저장하지 않는다.
- reject 여부를 판단하지 않는다.
- validation을 수행하지 않는다.
"""

from text_processing import (
    collect_text_parts,
    build_document_text,
)


# =========================================================
# 공통 보조 함수
# =========================================================

def _empty_if_none(value):
    """
    None 값을 빈 문자열로 바꾼다.

    담당 4에서는 누락값을 제거하거나 reject하지 않고
    담당 5가 판단할 수 있도록 빈 값으로 보존한다.
    """
    if value is None:
        return ""

    return value


def _convert_coordinate(value):
    """
    mapx/mapy 좌표를 가능하면 float으로 변환한다.

    예:
    "126.9784" -> 126.9784
    "" -> ""
    "잘못된좌표" -> "잘못된좌표"

    변환할 수 없는 값은 그대로 두고
    validation 단계에서 판단하도록 한다.
    """
    value = _empty_if_none(value)

    if value == "":
        return ""

    try:
        return float(value)

    except ValueError:
        return value


# =========================================================
# TODO 1.
# build_metadata(festival, intro) -> dict
# =========================================================

def build_metadata(
    festival: dict,
    intro: dict | None,
) -> dict:

    # contentid -> doc_id
    raw_contentid = festival.get("contentid", "")

    if raw_contentid is None:
        doc_id = ""
    else:
        doc_id = str(raw_contentid)

    # mapx -> longitude
    longitude = _convert_coordinate(
        festival.get("mapx", "")
    )

    # mapy -> latitude
    latitude = _convert_coordinate(
        festival.get("mapy", "")
    )

    # -----------------------------------------------------
    # TODO 5도 함께 반영
    #
    # 모든 Document가 동일한 metadata key를 가지도록
    # intro 관련 key까지 먼저 빈 값으로 생성한다.
    # -----------------------------------------------------

    metadata: dict = {
        "doc_id": doc_id,

        "title": _empty_if_none(
            festival.get("title", "")
        ),

        "event_start": _empty_if_none(
            festival.get("eventstartdate", "")
        ),

        "event_end": _empty_if_none(
            festival.get("eventenddate", "")
        ),

        "address": _empty_if_none(
            festival.get("addr1", "")
        ),

        "longitude": longitude,

        "latitude": latitude,

        "homepage": _empty_if_none(
            festival.get("homepage", "")
        ),

        "modified_at": _empty_if_none(
            festival.get("modifiedtime", "")
        ),

        # intro가 없어도 key는 유지
        "sponsor1": "",
        "sponsor2": "",
        "eventplace": "",
        "playtime": "",
        "agelimit": "",
        "usetimefestival": "",
    }

    # intro가 존재하면 빈 값을 실제 값으로 갱신
    if intro:
        metadata.update({
            "sponsor1": _empty_if_none(
                intro.get("sponsor1", "")
            ),

            "sponsor2": _empty_if_none(
                intro.get("sponsor2", "")
            ),

            "eventplace": _empty_if_none(
                intro.get("eventplace", "")
            ),

            "playtime": _empty_if_none(
                intro.get("playtime", "")
            ),

            "agelimit": _empty_if_none(
                intro.get("agelimit", "")
            ),

            "usetimefestival": _empty_if_none(
                intro.get("usetimefestival", "")
            ),
        })

    return metadata


# =========================================================
# TODO 2.
# build_festival_document(
#     festival,
#     intro,
#     info_rows
# ) -> dict
# =========================================================

def build_festival_document(
    festival: dict,
    intro: dict | None,
    info_rows: list[dict],
) -> dict:

    # 1.
    # contentid -> doc_id
    raw_contentid = festival.get("contentid", "")

    if raw_contentid is None:
        contentid = ""
    else:
        contentid = str(raw_contentid)

    # 2.
    # 담당 3의 함수로 text 조각 수집
    parts: list[str] = collect_text_parts(
        festival,
        intro,
        info_rows,
    )

    # 3.
    # text 조각을 최종 문자열 하나로 결합
    text: str = build_document_text(parts)

    # 4.
    # metadata 생성
    metadata: dict = build_metadata(
        festival,
        intro,
    )

    # 5.
    # 축제 한 건 -> Document 한 건
    document: dict = {
        "doc_id": contentid,

        "title": _empty_if_none(
            festival.get("title", "")
        ),

        "text": text,

        "metadata": metadata,
    }

    return document


# """담당 4. Festival Document 및 metadata 생성 가이드

# festival_raw의 flat 필드, intro/info lookup, 담당 3의 text를 결합한다.
# 축제 한 건을 입력받으면 Document 한 건만 반환하는 것이 핵심 계약이다.
# """

# TODO 1. build_metadata(festival, intro) -> dict를 구현한다.
#
# festival_raw flat 필드 매핑
# contentid -> doc_id
# title -> title
# eventstartdate/eventenddate -> event_start/event_end
# addr1 -> address, mapx -> longitude, mapy -> latitude
# homepage -> homepage, modifiedtime -> modified_at
#
# metadata = {}를 만든 뒤 명시적으로 필드를 채운다.
# 값은 festival.get("field", "")로 읽고 doc_id는 str()로 변환한다.
# intro가 존재할 때만 sponsor1, sponsor2, eventplace, playtime,
# agelimit, usetimefestival을 update()로 추가한다.
# mapx/mapy 숫자 변환이 필요하면 try/except ValueError를 사용한다.

# TODO 2. build_festival_document(festival, intro, info_rows) -> dict를 구현한다.
#
# 1. contentid = str(festival.get("contentid", ""))를 만든다.
# 2. collect_text_parts(festival, intro, info_rows)를 호출한다.
# 3. build_document_text(parts)를 호출해 text를 만든다.
# 4. build_metadata(festival, intro)를 호출한다.
# 5. {"doc_id": ..., "title": ..., "text": ..., "metadata": ...}를 반환한다.
#
# 한 레코드에서 여러 Document를 만들지 않는다.
# 이 파일은 파일 저장이나 reject 판단을 직접 하지 않는다.

# TODO 3. 함수 간 자료형을 명확히 한다.
#
# festival: dict
# intro: dict | None
# info_rows: list[dict]
# text: str
# metadata: dict
# document: dict
#
# 잘못된 입력을 조용히 건너뛰기보다 담당 5가 판단할 수 있도록
# 누락값을 빈 값으로 보존한다.

# TODO 4. 단위 테스트를 작성한다.
#
# - 모든 flat 필드가 있는 정상 레코드
# - intro가 없는 레코드
# - 좌표가 빈 문자열 또는 숫자로 변환되지 않는 레코드
# - text 조각이 하나도 없는 레코드
# - doc_id가 원본 contentid와 같은지 확인
# TODO 5. metadata 스키마와 좌표 변환 실패 처리 정책을 고정한다.
#
# 모든 문서가 동일한 metadata key를 갖도록 key 목록을 먼저 고정한다.
# 값이 없는 필드는 None 대신 기본값(일반 문자열은 "")을 사용한다.
# mapx는 longitude, mapy는 latitude로 매핑한다.
# 좌표가 빈 문자열이면 빈 값으로 보존하고, 숫자로 변환할 수 없는 값은
# validation 단계에서 invalid_longitude 또는 invalid_latitude 오류로 처리한다.
# 원본 contentid는 document의 doc_id와 metadata의 doc_id에 동일하게 사용한다.