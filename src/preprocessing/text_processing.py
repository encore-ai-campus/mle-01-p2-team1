"""전처리 2~3단계: 텍스트 수집과 정제 TODO."""

# TODO 1. collect_text_parts(festival, intro, info_rows) -> list[str]를 구현한다.
# overview, info의 infotext, intro의 program/subevent/placeinfo를 수집한다.
# TODO 2. clean_text(value: str) -> str를 구현한다. entity, HTML, 연속 공백을 정리한다.
# TODO 3. remove_duplicate_text_parts(parts) -> list[str]를 구현한다.
# TODO 4. build_document_text(parts) -> str를 구현한다. 빈 입력은 빈 문자열을 반환한다.
# TODO 5. HTML/entity/None/공백/중복/빈 리스트 경계값 테스트를 작성한다.
# TODO 6. dict/list 전체가 본문으로 들어가지 않도록 문자열 필드만 수집하는 정책을 정한다.
