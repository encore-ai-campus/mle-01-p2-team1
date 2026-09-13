"""전처리 4단계: Festival Document와 metadata 생성 TODO."""

# TODO 1. build_metadata(festival, intro) -> dict를 구현한다.
# flat field와 intro의 sponsor/eventplace/playtime/agelimit/usetimefestival을 매핑한다.
# TODO 2. build_festival_document(festival, intro, info_rows) -> dict를 구현한다.
# {doc_id, title, text, metadata} 구조를 반환한다.
# TODO 3. 함수 입력 자료형을 명확히 한다. intro는 dict | None, info_rows는 list[dict]이다.
# TODO 4. 정상 record, intro 없음, 좌표 오류, 빈 텍스트 단위 테스트를 작성한다.
# TODO 5. metadata 스키마와 좌표 변환 실패 정책을 고정한다.
