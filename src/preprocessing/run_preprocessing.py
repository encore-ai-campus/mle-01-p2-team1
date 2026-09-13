"""전처리 전체 workflow 실행 TODO."""

# TODO 1. load_data.py에서 festival_rows, intro_lookup, info_lookup을 준비한다.
# TODO 2. processed_documents, reject_logs, seen_doc_ids를 준비한다.
# TODO 3. festival_rows를 순회하며 contentid로 intro/info를 조회하고 Document를 생성한다.
# TODO 4. validation 결과에 따라 성공 문서와 reject log를 분리한다.
# TODO 5. 성공 문서, reject log, report를 저장한다.
# TODO 6. 저장 후 성공/실패 합계, JSONL 파싱, doc_id 중복을 검증한다.
# TODO 7. run_preprocessing()과 main guard를 구현한다.
# python -m src.preprocessing.run_preprocessing으로 실행 가능해야 한다.
# TODO 8. 파일/저장 실패는 중단하고 개별 record 실패는 reject 후 계속한다.
# TODO 9. intro/info 누락, API error, contentid 매칭 실패 수를 report에 기록한다.
# TODO 10. 각 모듈의 정상/오류 입력과 저장 결과 단위 테스트를 작성한다.
