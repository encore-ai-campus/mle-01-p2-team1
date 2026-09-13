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
# TODO 6. MIN_TEXT_LENGTH, 날짜 형식, 좌표 범위 등 검증 기준을 정의한다.
#
# MIN_TEXT_LENGTH는 config.py 또는 이 파일의 상수로 한 곳에서 관리한다.
# event_start와 event_end는 값이 있을 때 숫자 8자리 YYYYMMDD인지 확인한다.
# longitude는 -180 이상 180 이하, latitude는 -90 이상 90 이하인지 확인한다.
# 각 규칙을 위반하면 하나의 오류만 반환하지 말고 오류 목록에 모두 추가한다.

# TODO 7. 재실행 시 출력 파일을 overwrite하는 정책을 정의한다.
#
# save_jsonl은 파일을 "w" 모드로 열어 이전 실행 결과를 먼저 지운다.
# 저장 전 부모 디렉터리가 없으면 mkdir(parents=True, exist_ok=True)로 만든다.
# 그래야 같은 명령을 여러 번 실행해도 문서가 중복으로 쌓이지 않는다.

# TODO 8. 저장 후 JSONL 파싱, 건수 합계, doc_id 중복, report 통계를 재검증한다.
#
# 저장된 JSONL을 다시 한 줄씩 읽고 json.loads가 성공하는지 확인한다.
# processed_count + reject_count가 source_count와 같은지 확인한다.
# 성공 문서의 doc_id가 중복되지 않는지 확인한다.
# report의 각 count가 실제 processed/reject 파일의 행 수와 같은지 확인한다.
# 검증 실패 시 성공으로 종료하지 말고 오류를 발생시킨다.
# TODO 9. 제거 사유별 전처리 통계를 report에 기록한다.
#
# 단순히 reject_count 하나만 세지 말고, 왜 문서가 최종 결과에서 제외되었는지
# 사유별로 나누어 집계한다.
#
# report에는 최소한 다음 항목을 포함한다.
# - source_count: 전처리 대상이었던 원본 문서 수
# - duplicate_removed_count: 중복으로 제거된 문서 수
# - short_text_removed_count: 기준 길이보다 짧아 제거된 문서 수
# - missing_text_count: 본문이 없어 제거된 문서 수
# - final_document_count: 최종 저장된 문서 수
# - reject_count: 최종적으로 reject log에 기록된 전체 문서 수
#
# final_document_count는 processed 문서의 실제 개수와 같아야 한다.
# 각 사유별 제거 건수의 합계가 reject_count와 일치하는지 검증한다.

# TODO 10. 중복 문서 제거와 중복 문서 통계를 구분한다.
#
# duplicate_doc_id_count는 처리 후 중복 ID가 발견된 개수이고,
# duplicate_removed_count는 중복 문서를 실제로 제외한 개수이다.
# 두 값은 의미가 다르므로 report에서 별도 필드로 관리한다.
#
# 중복 판단 기준은 contentid에서 만든 doc_id로 한다.
# 이미 처리한 doc_id가 다시 나오면 해당 문서는 processed 목록에 넣지 않고,
# reject log에 duplicate_doc_id 사유로 기록한다.
