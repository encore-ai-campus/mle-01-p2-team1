"""
LLM Entity / Relation Extraction용 Festival Document 생성 모듈

역할
- 여러 API에 흩어진 비정형 설명문을 하나의 text로 만든다.
- 검색/필터링용 정형 metadata를 별도로 구성한다.
- 최종적으로 축제 하나를 하나의 Document로 만든다.

최종 Document 개념

doc_id
title
text

event_start
event_end
address
longitude
latitude
homepage
modified_at

sponsor1
sponsor2
eventplace
playtime
agelimit
usetimefestival
"""


# TODO: 한 축제에서 사용할 비정형 텍스트 조각들을 수집하는 함수를 작성한다.
#
# 함수명 예시
# collect_text_parts(...)
#
# 수집 대상
# 1. festivals_2026_full.json
#    - common.overview
#
# 2. festival_info_2026.json
#    - 선택된 info[].infotext
#
# 3. festival_intro_2026.json
#    - intro.program
#    - intro.subevent
#    - intro.placeinfo
#
# 해야 할 일
# 1. overview를 가져온다.
# 2. 선택된 info 텍스트를 가져온다.
# 3. program을 가져온다.
# 4. subevent를 가져온다.
# 5. placeinfo를 가져온다.
# 6. 각 텍스트에 clean_text를 적용한다.
# 7. 빈 텍스트는 제외한다.
# 8. 텍스트 조각 리스트를 반환한다.


# TODO: 서로 다른 필드에 반복된 동일 텍스트를 제거하는 함수를 작성한다.
#
# 함수명 예시
# remove_duplicate_text_parts(text_parts)
#
# 예시
# overview:
# "다양한 체험 프로그램이 운영된다."
#
# program:
# "다양한 체험 프로그램이 운영된다."
#
# 위와 같은 경우 한 번만 남긴다.
#
# 해야 할 일
# 1. 텍스트를 처음부터 순서대로 확인한다.
# 2. 이미 나온 동일 문자열인지 검사한다.
# 3. 처음 등장한 텍스트만 남긴다.
# 4. 원래 등장 순서는 유지한다.
# 5. 중복 제거 결과를 반환한다.
#
# 현재 단계에서는 exact duplicate만 처리한다.
# fuzzy matching이나 embedding 기반 중복 제거는 필요할 때 확장한다.


# TODO: 최종 LLM 입력용 text를 만드는 함수를 작성한다.
#
# 함수명 예시
# build_document_text(...)
#
# 처리 순서
# 1. collect_text_parts로 텍스트 후보를 수집한다.
# 2. remove_duplicate_text_parts로 중복을 제거한다.
# 3. 남은 텍스트를 하나의 Document text로 연결한다.
# 4. 최종 text를 반환한다.
#
# 권장
# 모든 내용을 공백 하나로 붙이기보다는
# 원래 텍스트 조각 사이의 문단 구분을 어느 정도 유지한다.
#
# 이유
# - 사람이 읽기 쉽다.
# - 이후 evidence 검토가 쉽다.


# TODO: 축제의 정형 metadata를 만드는 함수를 작성한다.
#
# 함수명 예시
# build_metadata(...)
#
# festivals_2026_full.json에서 가져올 값
#
# common.contentid
# -> doc_id
#
# common.title
# -> title
#
# search.eventstartdate
# -> event_start
#
# search.eventenddate
# -> event_end
#
# common.addr1
# -> address
#
# common.mapx
# -> longitude
#
# common.mapy
# -> latitude
#
# common.homepage
# -> homepage
#
# common.modifiedtime
# -> modified_at
#
#
# festival_intro_2026.json에서 가져올 값
#
# intro.sponsor1
# -> sponsor1
#
# intro.sponsor2
# -> sponsor2
#
# intro.eventplace
# -> eventplace
#
# intro.playtime
# -> playtime
#
# intro.agelimit
# -> agelimit
#
# intro.usetimefestival
# -> usetimefestival
#
#
# 해야 할 일
# 1. 필요한 정형 필드를 각 원본 위치에서 가져온다.
# 2. 빈 값은 통일된 결측 표현으로 처리한다.
# 3. 날짜 형식을 검증한다.
# 4. 좌표가 숫자로 변환 가능한지 검증한다.
# 5. metadata 객체를 반환한다.
#
# 중요
# 이 metadata 자체는 LLM Relation Extraction 결과가 아니다.
# 검색, 필터, 화면 표시, 그래프 보강 등에 사용한다.


# TODO: 축제 하나를 최종 Document 하나로 만드는 함수를 작성한다.
#
# 함수명 예시
# build_festival_document(...)
#
# 해야 할 일
# 1. festivals_2026_full의 한 축제 레코드를 입력받는다.
# 2. contentid를 확인한다.
# 3. intro lookup에서 동일 contentid 데이터를 찾는다.
# 4. info lookup에서 동일 contentid 데이터를 찾는다.
# 5. build_document_text로 비정형 text를 생성한다.
# 6. build_metadata로 정형 metadata를 생성한다.
# 7. text와 metadata를 하나의 Document로 합친다.
# 8. 최종 Document를 반환한다.
#
# 최종 목표
# 축제 하나 = Document 하나