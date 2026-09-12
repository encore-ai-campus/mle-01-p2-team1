"""
축제 프로젝트 원본 JSON 로딩 모듈

역할
- JSON 파일을 UTF-8로 읽는다.
- 파일의 원본 구조는 변경하지 않는다.
- festivals / intro / info 데이터를 각각 불러온다.

주의
- nearby, stays 데이터는 LLM 문서 전처리 대상이 아니므로
  여기의 festival document 생성 파이프라인에는 포함하지 않는다.
- nearby와 stays는 이후 Graph Enrichment 단계에서 별도로 사용한다.
"""


# TODO: JSON 파일 하나를 읽어 Python 객체로 반환하는 함수를 작성한다.
#
# 함수명 예시
# load_json(path)
#
# 해야 할 일
# 1. 파일 경로를 입력받는다.
# 2. UTF-8 인코딩으로 JSON 파일을 연다.
# 3. JSON 내용을 Python 객체로 변환한다.
# 4. 읽은 데이터를 반환한다.
#
# 주의
# - 이 함수에서는 데이터 내용을 수정하지 않는다.
# - 결측값 처리, HTML 제거 등의 전처리는 다른 모듈에서 수행한다.


# TODO: 축제 Document 생성에 필요한 원본 JSON 세 개를 불러오는 함수를 작성한다.
#
# 함수명 예시
# load_festival_sources(...)
#
# 불러올 데이터
# 1. festival_raw.json
# 2. festival_intro_2026.json
# 3. festival_info_2026.json
#
# 반환할 것
# - festival 데이터
# - intro 데이터
# - info 데이터
#
# 주의
# - festival_nearby_5km.json과 stays_all.json은 여기서 합치지 않는다.
