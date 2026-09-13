"""담당 5. Document 검증·분리·저장·통계 가이드

이 파일은 최종 단계의 책임을 모은다. 검증 함수, reject log 생성,
JSONL 저장, 결과 통계를 구현한다. 원본 텍스트를 다시 정제하지 않는다.
"""

# TODO 1. validate_document(document) -> list[str]를 구현한다.
#
# required = ["doc_id", "title", "text", "metadata"]를 for field in required로
# 순회한다. document.get(field)가 비어 있으면 missing_<field>를 errors에 추가한다.
# text 길이가 MIN_TEXT_LENGTH보다 짧으면 short_text를 추가한다.
# metadata의 event_start/event_end 형식과 좌표 숫자 여부도 별도 오류 코드로 기록한다.
# 오류가 없으면 빈 list를 반환한다. bool 하나가 아니라 여러 오류를 반환해야
# reject 원인을 한 번에 확인할 수 있다.

# TODO 2. make_reject_log(document, errors) -> dict를 구현한다.
#
# doc_id, title, reject_reason, text_length를 포함한다.
# reject_reason은 errors를 list로 보존하거나 ","로 join한다.
# 원문 전체 text를 reject log에 복사하지 않아 로그가 불필요하게 커지지 않게 한다.

# TODO 3. save_jsonl(path, rows)와 save_json(path, value)를 구현한다.
#
# Path(path).parent.mkdir(parents=True, exist_ok=True)로 디렉터리를 만든다.
# open(path, "w", encoding="utf-8")을 사용한다.
# JSONL은 for row in rows 반복문에서 json.dumps(row, ensure_ascii=False) 뒤
# 개행을 붙여 한 줄씩 저장한다. 저장 후 다시 읽어 json.loads()가 되는지 확인한다.

# TODO 4. build_preprocessing_report(processed, rejects, source_count)를 구현한다.
#
# success_count, reject_count, missing_text_count, short_text_count,
# duplicate_doc_id_count를 계산한다.
# text_lengths = [len(doc["text"]) for doc in processed]로 길이를 모으고
# 최소·최대·평균을 계산한다. 0건일 때 min/max에서 예외가 나지 않게 처리한다.

# TODO 5. 출력 파일을 정의한다.
#
# config.py의 PROCESSED_DOCUMENTS_PATH
# config.py의 REJECT_LOG_PATH
# config.py의 PREPROCESSING_REPORT_PATH
