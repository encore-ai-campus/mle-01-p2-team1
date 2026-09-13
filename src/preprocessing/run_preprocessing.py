"""전처리 전체 workflow를 연결하는 실행 가이드.

이 파일은 담당 모듈의 함수를 정해진 순서로 호출한다.
세부적인 데이터 정제와 Document 생성은 각 담당 파일에서 구현한다.
"""

# TODO 1. load_data.py의 데이터 로딩 함수를 호출한다.
# festival_rows, intro_lookup, info_lookup를 준비한다.
# 입력 파일 경로는 config.py의 경로 상수를 사용한다.

# TODO 2. 결과를 저장할 컨테이너를 준비한다.
# processed_documents = []
# reject_logs = []
# seen_doc_ids = set()
# source_count = len(festival_rows)

# TODO 3. festival_rows를 한 번 순회하며 축제별 Document를 생성한다.
# 각 레코드의 contentid로 intro와 info를 조회하고,
# document_builder.py의 생성 함수를 호출한다.
# 생성된 Document는 validation_output.py의 검증 함수에 전달한다.

# TODO 4. 검증 결과에 따라 문서를 분리한다.
# 오류가 없으면 processed_documents에 추가한다.
# 오류가 있으면 doc_id, title, 오류 원인, text 길이를 reject_logs에 기록한다.
# 하나의 레코드에서 오류가 발생해도 전체 처리는 중단하지 않는다.

# TODO 5. 검증된 결과를 저장한다.
# 성공 문서는 PROCESSED_DOCUMENTS_PATH에 JSONL로 저장한다.
# reject 기록은 REJECT_LOG_PATH에 저장한다.
# 전체 처리 건수와 성공·실패 통계는 PREPROCESSING_REPORT_PATH에 저장한다.

# TODO 6. 저장 후 결과를 다시 확인한다.
# 성공 문서 수와 reject 문서 수의 합이 원본 처리 건수와 같은지 확인한다.
# 저장된 JSONL의 각 줄이 정상적인 JSON인지 확인한다.
# 성공 문서의 doc_id가 중복되지 않는지 확인한다.

# 최종 workflow:
# load_data -> lookup 생성 -> text_processing
# -> document_builder -> validation_output -> 결과 저장
# TODO 7. run_preprocessing()과 main guard를 정의한다.
# TODO 8. 전체 실패와 개별 record 실패의 예외 처리 정책을 정의한다.
# TODO 9. intro/info 누락 및 API error 통계를 report에 기록한다.
