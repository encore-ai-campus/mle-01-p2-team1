"""추출부터 검증과 평가까지 공통 실행 순서를 연결하는 실행 모듈."""

import argparse
import json
from pathlib import Path
from typing import Any

from src.extraction.evaluate import save_summary, summarize_validation
from src.extraction.extract import extract_batch, load_documents, make_model, save_raw_results, select_sample_documents
from src.extraction.validate import ValidationRecord, validate_triples


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """실행 모드와 입출력 경로를 CLI 인자로 받는다."""
    parser = argparse.ArgumentParser(description="Triple 추출 파이프라인 실행")
    parser.add_argument("--mode", choices=("sample", "full"), default="sample")
    parser.add_argument("--input", type=Path, default=Path("data/processed/01_preprocessing/festivals_documents.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/02_extraction"))
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--go-threshold", type=float, default=0.95)
    parser.add_argument("--raw-input", type=Path, help="추출을 생략하고 기존 Raw JSON을 검증한다.")
    return parser.parse_args(argv)


def _load_raw_records(path: Path) -> list[dict[str, Any]]:
    """기존 Raw 결과 JSON 배열을 읽는다."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Raw 결과는 JSON 배열이어야 합니다.")
    return data


def _write_records(records: list[ValidationRecord], path: Path) -> None:
    """검증 레코드를 JSON으로 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{"triple": r.triple, "passed": r.passed, "stage": r.stage, "error_codes": r.error_codes} for r in records]
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    """추출, Raw 저장, 5단계 검증, 평가 요약을 순서대로 실행한다."""
    args.output_dir.mkdir(parents=True, exist_ok=True)
    documents = load_documents(args.input)
    selected = select_sample_documents(documents) if args.mode == "sample" else documents
    raw_path = args.raw_input or args.output_dir / ("triples_sample_raw.json" if args.mode == "sample" else "triples_raw.json")

    if args.raw_input is None:
        results = extract_batch(selected, model_factory=make_model, max_retries=args.max_retries)
        save_raw_results(results, raw_path)
        raw_records = [result.model_dump(mode="json") for result in results]
    else:
        raw_records = _load_raw_records(raw_path)

    source_text_by_doc = {doc["source_doc_id"]: doc["text"] for doc in selected}
    raw_triples = [triple for record in raw_records for triple in record.get("triples", [])]
    clean, rejected = validate_triples(raw_triples, source_text_by_doc)
    clean_name = "triples_sample_clean.json" if args.mode == "sample" else "triples_clean.json"
    rejected_name = "triples_sample_rejected.json" if args.mode == "sample" else "triples_rejected.json"
    _write_records(clean, args.output_dir / clean_name)
    _write_records(rejected, args.output_dir / rejected_name)

    summary = summarize_validation(clean, rejected)
    summary["mode"] = args.mode
    summary["document_count"] = len(selected)
    ratio = summary["clean_count"] / summary["total_count"] if summary["total_count"] else 0.0
    summary["go_no_go"] = "GO" if ratio >= args.go_threshold else "NO-GO"
    save_summary(summary, args.output_dir / "validation_summary.json")
    return summary


def main() -> None:
    """명령줄 실행 진입점."""
    print(json.dumps(run_pipeline(parse_args()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
