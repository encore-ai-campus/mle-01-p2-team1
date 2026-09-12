"""담당 1. 원본 JSON 로딩·정규화·lookup 생성 가이드

이 파일의 책임은 파일을 읽고, 후속 단계가 사용할 입력 구조를 준비하는 것이다.
텍스트 정제나 Document 생성은 이 파일에서 구현하지 않는다.

입력
    config.py의 FESTIVAL_RAW_PATH
    config.py의 FESTIVAL_INTRO_PATH
    config.py의 FESTIVAL_INFO_PATH

출력 계약
    festival_rows: list[dict]
    intro_lookup: dict[str, dict]
    info_lookup: dict[str, list[dict]]
"""

# TODO 1. load_json(path: str) -> list | dict를 구현한다.
#
# 구현 순서
# 1. Path(path).open("r", encoding="utf-8")으로 파일을 연다.
# 2. json.load(file)로 Python 객체를 만든다.
# 3. 파일이 없으면 FileNotFoundError를 그대로 구분할 수 있게 한다.
# 4. JSON 문법 오류는 JSONDecodeError로 확인할 수 있게 한다.
# 5. 원본 객체를 수정하지 않고 반환한다.

# TODO 2. normalize_festival(row: dict) -> dict를 구현한다.
#
# festival_raw.json은 contentid, title, eventstartdate, eventenddate,
# addr1, mapx, mapy, homepage, modifiedtime, overview 등이 최상위에 있다.
# row.get("field", "")를 사용해 없는 필드도 예외 없이 처리한다.
# contentid는 str()로 변환하고, 나머지 값은 의미를 바꾸지 않고 보존한다.

# TODO 3. build_lookup(rows, key="contentid")를 구현한다.
#
# 단일 레코드 데이터는 {str(row[key]): row} 형태의 dict로 만든다.
# info처럼 한 contentid에 여러 레코드가 연결될 수 있는 데이터는
# collections.defaultdict(list)를 사용해 {contentid: [row, ...]}로 그룹화한다.
# for row in rows 반복문에서 key가 없거나 빈 값인 레코드는 별도 누락 목록에 기록한다.
# 중복 contentid는 조용히 덮어쓰지 말고 duplicate_ids에 기록한다.

# TODO 4. load_festival_sources(base_dir: str) 함수를 작성한다.
#
# festival_rows = [normalize_festival(row) for row in load_json(festival_path)]
# 형태로 축제 목록을 정규화한다.
# intro_lookup과 info_lookup을 각각 생성해 run_preprocessing.py에 반환한다.
# 반환값은 tuple보다 이름 있는 dict 또는 dataclass를 사용하면 담당자 간 계약을
# 확인하기 쉽다. 이 단계에서 결측값을 추측해 채우지는 않는다.

# TODO 5. 로딩 단위 테스트를 작성한다.
#
# - 정상 배열 로딩
# - 빈 배열 로딩
# - 없는 파일
# - 잘못된 JSON
# - contentid 없는 row
# - info의 동일 contentid 여러 건

# TODO 6. intro/info lookup과 infotext 선별을 이 파일에서 함께 구현한다.
#
# merge_festival.py에 흩어져 있던 연결 로직은 이 담당 영역에 통합한다.
# build_intro_lookup(intro_rows)는 contentid를 key로 하는 dict를 만든다.
# build_info_lookup(info_rows)는 defaultdict(list)를 사용해 contentid별 배열을 만든다.
# select_info_texts(info_items)는 for item in info_items로 순회하며
# infoname을 확인하고, 설명형 항목의 infotext만 반환한다.
# 전화번호·URL·날짜·가격처럼 단독 값만 있는 항목은 제외한다.
