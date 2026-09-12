"""
축제별 API 데이터 연결 모듈

역할
- 서로 다른 JSON 파일에 흩어진 축제 정보를 contentid 기준으로 연결한다.
- intro와 info 데이터를 contentid로 빠르게 조회할 수 있는 구조를 만든다.
- info 항목 중 LLM 본문에 사용할 서술형 내용만 선별한다.

중요
축제명(title)이 아니라 contentid를 조인 키로 사용한다.

이유
- 축제명은 공백이나 표기가 달라질 수 있다.
- contentid는 관광 API에서 동일 콘텐츠를 식별하기 위한 고유 키다.
"""


# TODO: intro 데이터를 contentid 기준 lookup 구조로 만드는 함수를 작성한다.
#
# 함수명 예시
# build_intro_lookup(intro_rows)
#
# 목표 구조
# contentid -> 해당 축제의 intro 정보
#
# 해야 할 일
# 1. intro 데이터 전체를 순회한다.
# 2. 각 레코드의 contentid를 확인한다.
# 3. contentid를 key로 저장한다.
# 4. 해당 축제의 intro 정보를 value로 저장한다.
# 5. 완성된 lookup을 반환한다.
#
# 주의
# - intro 배열이 비어 있는 축제도 있을 수 있다.
# - API error가 존재하는 경우도 고려한다.


# TODO: info 데이터를 contentid 기준 lookup 구조로 만드는 함수를 작성한다.
#
# 함수명 예시
# build_info_lookup(info_rows)
#
# 목표 구조
# contentid -> 해당 축제의 info 배열
#
# 해야 할 일
# 1. festival_info 데이터 전체를 순회한다.
# 2. contentid를 확인한다.
# 3. 해당 contentid의 info 배열을 저장한다.
# 4. 축제별 info를 빠르게 조회할 수 있는 lookup을 반환한다.


# TODO: info 배열에서 LLM 본문에 사용할 infotext만 선택하는 함수를 작성한다.
#
# 함수명 예시
# select_info_texts(info_items)
#
# 사용할 가능성이 높은 항목
# - 행사소개
# - 행사내용
# - 프로그램 관련 설명
# - 이용안내 중 서술형 내용
# - 교통/장소 관련 설명문
#
# 제외 후보
# - 전화번호만 있는 값
# - URL만 있는 값
# - 날짜만 있는 값
# - 가격 숫자만 있는 값
# - 빈 문자열
#
# 해야 할 일
# 1. info 배열을 순회한다.
# 2. infoname을 확인한다.
# 3. infotext를 가져온다.
# 4. infotext에 clean_text를 적용한다.
# 5. 빈 값은 제외한다.
# 6. 사용할 infoname인지 판단한다.
# 7. 선택된 infotext들을 리스트로 반환한다.
#
# 권장
# 실제 데이터의 infoname 종류와 빈도를 먼저 확인한 뒤
# 사용할 항목 목록을 팀에서 명확하게 정한다.