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
#
# run_preprocessing() 안에서 load_data부터 결과 저장까지 전체 순서를 호출한다.
# 파일 마지막에 if __name__ == "__main__":를 작성한다.
# 실행 시에는 python -m src.preprocessing.run_preprocessing 명령으로 동작해야 한다.
# 함수는 최종 report dict를 반환해 다른 코드에서도 재사용할 수 있게 한다.

# TODO 8. 전체 실패와 개별 record 실패의 예외 처리 정책을 정의한다.
#
# 원본 파일을 읽을 수 없거나 출력 파일 저장에 실패하면 전체 작업을 중단한다.
# 특정 festival의 데이터가 잘못된 경우에는 해당 record만 reject log에 기록한다.
# reject 처리 후에는 다음 festival을 계속 처리한다.
# 예외를 무조건 삼키지 말고 reject_reason에 원인을 남긴다.

# TODO 9. intro/info 누락 및 API error 통계를 report에 기록한다.
#
# festival contentid가 intro_lookup에 없는 개수를 센다.
# festival contentid가 info_lookup에 없는 개수를 센다.
# intro/info wrapper의 error 값이 비어 있지 않은 row 개수를 센다.
# 이 통계를 preprocessing_report.json에 저장해 원본 데이터 품질을 확인한다.
