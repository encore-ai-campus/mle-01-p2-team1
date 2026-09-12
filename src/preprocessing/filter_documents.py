"""
전처리된 Festival Document 품질 검사 모듈

역할
- LLM에 넘겨도 되는 문서인지 검사한다.
- 짧은 문서, 필수값 누락, 중복 문서를 식별한다.
- 탈락한 문서는 삭제만 하지 않고 reject_reason을 남긴다.

중요
프로젝트 평가에서
'어떤 기준으로 몇 건을 제거했는가'를 설명할 수 있어야 한다.
"""


# TODO: 필수 필드가 존재하는지 검사하는 함수를 작성한다.
#
# 함수명 예시
# check_required_fields(document)
#
# 필수 후보
# - doc_id
# - title
# - text
#
# 해야 할 일
# 1. doc_id가 존재하는지 확인한다.
# 2. title이 존재하는지 확인한다.
# 3. text가 존재하는지 확인한다.
# 4. 누락된 항목이 있으면 이유를 반환한다.
# 5. 모두 존재하면 통과시킨다.


# TODO: 본문 길이가 최소 기준 이상인지 검사하는 함수를 작성한다.
#
# 함수명 예시
# check_min_length(document, min_length)
#
# 해야 할 일
# 1. document의 text 길이를 계산한다.
# 2. 팀에서 정한 최소 길이와 비교한다.
# 3. 기준 이상이면 통과한다.
# 4. 기준보다 짧으면 short_text 사유를 반환한다.
#
# 주의
# 처음부터 200자 같은 기준을 임의로 고정하지 않는다.
# 실제 데이터 길이 분포를 확인한 뒤 팀 기준을 정한다.


# TODO: 중복 문서를 검사하는 함수를 작성한다.
#
# 함수명 예시
# check_duplicate_document(...)
#
# 검사할 중복
# 1. 동일 contentid
# 2. 동일한 최종 text
#
# 해야 할 일
# 1. 이미 등장한 doc_id인지 확인한다.
# 2. 이미 등장한 text인지 확인한다.
# 3. 중복이면 어떤 종류의 중복인지 반환한다.
# 4. 중복이 아니면 통과한다.
#
# 주의
# contentid가 다른데 text가 같은 경우는
# 실제 서로 다른 축제일 가능성도 있으므로 reject log로 추적한다.


# TODO: 한 Document의 모든 품질 검사를 실행하는 함수를 작성한다.
#
# 함수명 예시
# validate_document(...)
#
# 검사 순서 예시
# 1. 필수 필드 검사
# 2. 본문 길이 검사
# 3. 중복 검사
#
# 해야 할 일
# - 통과 여부를 반환한다.
# - 실패했다면 reject_reason을 함께 반환한다.
#
# reject_reason 예시
# missing_doc_id
# missing_title
# missing_text
# short_text
# duplicate_contentid
# duplicate_text
# api_error


# TODO: 전처리 결과 통계를 만드는 함수를 작성한다.
#
# 함수명 예시
# build_preprocessing_report(...)
#
# 계산할 값
# - 원본 축제 수
# - 최종 통과 문서 수
# - reject 문서 수
# - reject_reason별 건수
# - 최종 text 평균 길이
# - 중앙값
# - 최소 길이
# - 최대 길이
#
# 목적
# 프로젝트 발표 및 README에서
# 전처리 기준과 결과를 숫자로 설명하기 위함이다.