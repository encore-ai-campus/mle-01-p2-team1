"""문서 로딩부터 단건/배치 Triple 추출과 raw 저장까지의 경계를 정의한다."""

from pathlib import Path
from typing import Any, Sequence

from src.extraction.schemas import Extraction, ExtractionResult

# [교안 대응 TODO]
# TODO A. extract_document(text, model_factory) -> list[dict]를 교안 순서로 구현한다.
# 1. build_extraction_prompt(...)를 호출한다.
# 2. model_factory().with_structured_output(Extraction)을 연결한다.
# 3. chain.invoke({"text": text})를 호출한다.
# 4. result.triples를 model_dump()하여 list[dict]로 반환한다.
# TODO B. extract_documents는 문서를 순회하며 extract_document를 호출하고
# triple_id와 source_doc_id를 추가한다. 교안의 doc_id는 source_doc_id로 통일한다.
# TODO C. extract_one/extract_batch는 위 교안형 함수를 감싸 재시도와 raw 응답 보존을 추가한다.


# TODO 1. load_documents(path: Path) -> list[dict[str, str]]를 구현한다.
#
# 권장 처리 순서
# 1. path의 확장자와 프로젝트 입력 형식을 확인한다.
# 2. JSON 배열을 읽거나 JSONL을 한 줄씩 읽어 Python 객체로 변환한다.
# 3. 각 객체에서 source_doc_id와 text를 읽고 문자열인지 확인한다.
# 4. 유효한 문서를 입력 순서 그대로 list에 append한다.
#
# 필수 조건: source_doc_id와 text가 없거나 타입이 잘못되면 문서 위치가 포함된 오류를 낸다.
# 빈 text, 빈 파일, 중복 source_doc_id를 어떻게 처리할지 팀 규칙을 TODO로 결정한다.
# 이 함수는 text 정제, HTML 제거, Triple 추출을 하지 않는다.
def load_documents(path: Path) -> list[dict[str, str]]:
    """JSON/JSONL 입력을 읽어 최소 문서 계약을 검증한다."""
    raise NotImplementedError


# TODO 2. extract_one(document, max_retries) -> ExtractionResult를 구현한다.
#
# 권장 처리 순서
# 1. document에서 source_doc_id와 text를 읽는다.
# 2. prompts.build_extraction_prompt(source_doc_id, text)로 Prompt를 만든다.
# 3. LLM에 Structured Output 형식으로 요청한다.
# 4. 응답 원문을 보존한 뒤 schemas.ExtractionResult로 파싱한다.
# 5. 성공하면 triples와 raw_response를 반환한다.
#
# 호출 실패 시 문서 ID, 현재 재시도 횟수, 오류 내용을 기록한다.
# 재시도 횟수를 초과하면 해당 문서 결과만 error 상태로 남기고 배치를 중단하지 않는다.
# Pydantic 파싱 실패 시 raw 응답을 버리지 않는다.
# 이 함수는 Entity Resolution이나 Neo4j 저장을 하지 않는다.
def extract_one(document: dict[str, str], max_retries: int = 2) -> ExtractionResult:
    """문서 한 건을 추출한다."""
    raise NotImplementedError


# TODO 3. extract_batch(documents, max_retries) -> list[ExtractionResult]를 구현한다.
#
# 권장 처리 순서
# 1. results = []로 시작한다.
# 2. documents를 for document in documents로 순회한다.
# 3. extract_one(document, max_retries)를 호출한다.
# 4. 성공/실패 결과 모두 results에 append한다.
# 5. 전체 문서를 처리한 뒤 results를 반환한다.
#
# 한 문서의 LLM 호출 실패가 나머지 문서 처리를 막지 않아야 한다.
# 결과 순서는 입력 문서 순서를 유지하고, 실패 결과에도 source_doc_id를 남긴다.
def extract_batch(
    documents: Sequence[dict[str, str]], max_retries: int = 2
) -> list[ExtractionResult]:
    """문서 전체를 순서대로 추출한다."""
    raise NotImplementedError


# TODO 4. save_raw_results(results, output_path) -> None을 구현한다.
#
# 권장 처리 순서
# 1. results를 JSON 직렬화 가능한 dict/list 구조로 변환한다.
# 2. output_path의 부모 디렉터리가 없으면 생성한다.
# 3. UTF-8과 ensure_ascii=False로 triples_raw.json을 저장한다.
# 4. 저장한 파일을 다시 읽을 수 있는 형태인지 확인한다.
#
# Pydantic 파싱 실패 결과의 raw_response와 error를 반드시 보존한다.
# 이 함수는 clean/rejected 판정을 하지 않는다.
def save_raw_results(results: Sequence[ExtractionResult], output_path: Path) -> None:
    """검증 전 추출 결과를 JSON으로 저장한다."""
    raise NotImplementedError


# 예시: {"source_doc_id": "doc-001", "text": "축제는 서울에서 열린다."}
# 완료 조건: 실패 문서가 있어도 나머지 결과가 저장되고, 출력 JSON을 다시 읽을 수 있다.
# Freeze point: raw 포맷은 validate/evaluate 구현 전에 합의한다.
