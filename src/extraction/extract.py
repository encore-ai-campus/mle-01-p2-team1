"""문서 로딩부터 단건/배치 Triple 추출과 raw 저장까지의 경계를 정의한다."""
import json
from pathlib import Path
from typing import Sequence

from src.extraction.prompts import build_extraction_prompt
from src.extraction.schemas import Extraction, ExtractionResult


def _build_extraction_request(
    source_doc_id: str,
    text: str,
    model_factory,
    include_raw: bool = False,
):
    prompt = build_extraction_prompt(source_doc_id, text)
    model = model_factory().with_structured_output(
        Extraction,
        include_raw=include_raw,
    )
    return prompt, model


def _dump_triples(triples) -> list[dict]:
    return [triple.model_dump() for triple in triples]

# [교안 대응 TODO]
# TODO A. extract_document(text, model_factory) -> list[dict]를 교안 순서로 구현한다.
# 1. build_extraction_prompt(...)를 호출한다.
# 2. model_factory().with_structured_output(Extraction)을 연결한다.
# 3. 완성된 prompt를 model.invoke(prompt)로 호출한다.
# 4. result.triples를 model_dump()하여 list[dict]로 반환한다.
def extract_document(text, model_factory) -> list[dict]:
    prompt, model = _build_extraction_request("", text, model_factory)
    result = model.invoke(prompt)
    return _dump_triples(result.triples)

# TODO B. extract_documents는 문서를 순회하며 extract_document를 호출하고
# triple_id와 source_doc_id를 추가한다. 교안의 doc_id는 source_doc_id로 통일한다.
def extract_documents(documents, model_factory) -> list[dict]:
    results = []

    for doc in documents:
        source_doc_id = doc.metadata["source_doc_id"]
        triples = extract_document(doc.page_content, model_factory)

        for i, triple in enumerate(triples):
            triple["triple_id"] = f"{source_doc_id}_{i}"
            triple["source_doc_id"] = source_doc_id
            results.append(triple)

    return results

# TODO C. extract_one/extract_batch는 위 교안형 함수를 감싸 재시도와 raw 응답 보존을 추가한다.
def _extract_text(
    source_doc_id: str,
    text: str,
    model_factory,
    max_retries: int = 3,
) -> ExtractionResult:
    last_error = None
    raw = None

    total_attempts = max_retries + 1

    for attempt in range(total_attempts):
        try:
            prompt, model = _build_extraction_request(
                source_doc_id,
                text,
                model_factory,
                include_raw=True,
            )
            response = model.invoke(prompt)

            raw = response.get("raw")
            parsed = response.get("parsed")
            parsing_error = response.get("parsing_error")

            if parsing_error is not None:
                raise parsing_error

            if parsed is None:
                raise ValueError("Structured Output parsing result is empty.")

            return ExtractionResult(
                source_doc_id=source_doc_id,
                triples=_dump_triples(parsed.triples),
                raw_response=(
                    str(raw)
                    if raw is not None
                    else None
                ),
                error=None,
            )

        except Exception as e:
            last_error = e
            print(
                f"[extract_one] source_doc_id={source_doc_id}, "
                f"attempt={attempt + 1}/{total_attempts}, "
                f"error={e}"
            )

    return ExtractionResult(
        source_doc_id=source_doc_id,
        triples=[],
        raw_response=(
            str(raw)
            if raw is not None
            else None
        ),
        error=str(last_error),
    )

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

    suffix = path.suffix.lower()

    if suffix == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(
                f"{path}: JSON 최상위 값은 배열(list)이어야 합니다."
            )

        rows = data

    elif suffix == ".jsonl":
        rows = []

        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"{path}:{line_no}: 올바른 JSON 형식이 아닙니다."
                    ) from e

    else:
        raise ValueError(
            f"{path}: 지원하지 않는 확장자입니다. .json 또는 .jsonl만 가능합니다."
        )

    documents: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for index, row in enumerate(rows):
        position = index + 1

        if not isinstance(row, dict):
            raise ValueError(
                f"{path}: 문서 {position}번째 항목은 객체(dict)여야 합니다."
            )

        source_doc_id = row.get("source_doc_id")
        text = row.get("text")

        if not isinstance(source_doc_id, str):
            raise ValueError(
                f"{path}: 문서 {position}번째의 source_doc_id가 없거나 문자열이 아닙니다."
            )

        if not isinstance(text, str):
            raise ValueError(
                f"{path}: 문서 {position}번째의 text가 없거나 문자열이 아닙니다."
            )

        # 팀 규칙: 빈 source_doc_id와 빈 text는 허용하지 않는다.
        if not source_doc_id.strip():
            raise ValueError(
                f"{path}: 문서 {position}번째의 source_doc_id가 비어 있습니다."
            )

        if not text.strip():
            raise ValueError(
                f"{path}: 문서 {position}번째의 text가 비어 있습니다."
            )

        # 팀 규칙: 중복 source_doc_id는 오류로 처리한다.
        if source_doc_id in seen_ids:
            raise ValueError(
                f"{path}: 문서 {position}번째의 source_doc_id "
                f"{source_doc_id!r}가 중복되었습니다."
            )

        seen_ids.add(source_doc_id)

        documents.append({
            "source_doc_id": source_doc_id,
            "text": text,
        })

    return documents


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
def extract_one(
    document: dict[str, str],
    model_factory,
    max_retries: int = 2,
) -> ExtractionResult:
    """문서 한 건을 추출한다."""

    source_doc_id = document["source_doc_id"]
    text = document["text"]

    result = _extract_text(
        source_doc_id,
        text,
        model_factory,
        max_retries=max_retries,
    )
    return result


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
    documents: Sequence[dict[str, str]],
    model_factory,
    max_retries: int = 2,
) -> list[ExtractionResult]:
    """문서 전체를 순서대로 추출한다."""

    results: list[ExtractionResult] = []

    for document in documents:
        result = extract_one(
            document,
            model_factory,
            max_retries=max_retries,
        )
        results.append(result)

    return results


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

def save_raw_results(
    results: Sequence[ExtractionResult],
    output_path: Path,
) -> None:
    """검증 전 추출 결과를 JSON으로 저장한다.

    예시 입력 문서:
    {"source_doc_id": "doc-001", "text": "축제는 서울에서 열린다."}

    완료 조건:
    - 실패 문서가 있어도 나머지 결과가 함께 저장된다.
    - 실패 결과의 raw_response와 error를 보존한다.
    - 저장된 JSON을 다시 읽을 수 있다.

    Freeze point:
    - validate/evaluate 구현 전에 raw 결과 포맷을 확정한다.
    """

    data = [
        result.model_dump(mode="json")
        for result in results
    ]

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    # 저장한 JSON이 다시 읽히는지 확인
    with output_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        json.load(f)

# 예시: {"source_doc_id": "doc-001", "text": "축제는 서울에서 열린다."}
# 완료 조건: 실패 문서가 있어도 나머지 결과가 저장되고, 출력 JSON을 다시 읽을 수 있다.
# Freeze point: raw 포맷은 validate/evaluate 구현 전에 합의한다.
