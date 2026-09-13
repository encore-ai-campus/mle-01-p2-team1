"""담당 4. Festival Document 및 metadata 생성 가이드

festival_raw의 flat 필드, intro/info lookup, 담당 3의 text를 결합한다.
축제 한 건을 입력받으면 Document 한 건만 반환하는 것이 핵심 계약이다.
"""

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
