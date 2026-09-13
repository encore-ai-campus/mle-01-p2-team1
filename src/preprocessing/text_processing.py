"""담당 2·3. 텍스트 수집과 정제 가이드

담당 2는 원문 조각을 모으고, 담당 3은 그 조각을 정제한다.
두 작업은 같은 파일에 두되 함수 경계를 분리해 서로의 구현을 침범하지 않는다.
최종 결과는 Document가 아니라 text 문자열이다.
"""

# TODO 1. collect_text_parts(festival, intro, info_rows) -> list[str]를 구현한다.
#
# 권장 수집 순서
# 1. festival의 overview
# 2. info_rows를 for info in info_rows로 순회하며 infotext
# 3. intro의 program, subevent, placeinfo
#
# parts = []로 시작하고, source.get(field_name)으로 값을 읽는다.
# 값이 None이 아니고 str(value).strip()이 비어 있지 않을 때만 append한다.
# intro가 None이면 {}, info_rows가 None이면 []로 바꿔 반복문 오류를 막는다.
# 이 함수는 HTML 제거, 문장 수정, 중복 제거를 하지 않는다.

# TODO 2. clean_text(value: str) -> str를 구현한다.
#
# 처리 순서
# 1. html.unescape(value)로 &amp; 같은 entity를 복원한다.
# 2. re.sub(r"<[^>]+>", " ", value)로 HTML 태그를 제거한다.
# 3. re.sub(r"\\s+", " ", value).strip()으로 연속 공백을 정리한다.
# 원문의 의미와 문장 순서는 변경하지 않는다.

# TODO 3. remove_duplicate_text_parts(parts) -> list[str]를 구현한다.
#
# seen = set(), result = []를 준비한다.
# for part in parts 반복문에서 정제된 part가 비어 있지 않고
# part not in seen일 때만 seen.add(part)와 result.append(part)를 실행한다.
# set은 중복 확인에만 사용하고 result로 원래 등장 순서를 유지한다.
# fuzzy matching이나 embedding 기반 유사도 병합은 구현하지 않는다.

# TODO 4. build_document_text(parts) -> str를 구현한다.
#
# cleaned_parts = [clean_text(part) for part in parts]로 정제한 뒤
# unique_parts = remove_duplicate_text_parts(cleaned_parts)를 호출한다.
# 최종값은 "\\n\\n".join(unique_parts)로 만들고, 입력이 비어 있으면 ""을 반환한다.

# TODO 5. 경계값 테스트를 작성한다.
#
# - overview만 존재하는 경우
# - intro와 info가 None인 경우
# - HTML과 entity가 섞인 경우
# - 동일 조각이 반복되는 경우
# - 공백만 있는 조각과 빈 리스트
# TODO 6. dict/list 전체가 본문으로 들어가지 않도록 문자열 필드만 수집하는 정책을 정의한다.
