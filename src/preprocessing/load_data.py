"""전처리 1단계: 원본 JSON 로딩과 lookup 생성 TODO."""

# TODO 1. load_json(path: str) -> list | dict를 구현한다.
# TODO 2. normalize_festival(row: dict) -> dict를 구현한다. contentid는 문자열로 통일한다.
# TODO 3. build_lookup(rows, key="contentid")를 구현한다. 중복 key는 목록으로 그룹화한다.
# TODO 4. load_festival_sources(base_dir: str)를 구현하고 세 source를 반환한다.
# TODO 5. 정상/빈 JSON, 파일 없음, 잘못된 JSON, contentid 누락 테스트를 작성한다.
# TODO 6. intro/info lookup과 infotext 선별을 구현한다.
# TODO 7. intro/info API wrapper를 해제한다.
# intro row는 {contentid, intro: [...], error}, info row는 {contentid, info: [...], error}이다.
# intro_lookup에는 상세 dict, info_lookup에는 contentid별 info 배열을 저장한다.
# TODO 8. 최상위 list와 각 row의 dict 여부를 검증하고 오류 위치를 포함해 예외 처리한다.
