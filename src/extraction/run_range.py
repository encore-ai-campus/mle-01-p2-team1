"""문서 순번 구간을 재시작 가능하게 Triple 추출하는 실행 모듈."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.extraction.extract import (
    extract_one,
    load_documents,
    make_model,
    save_raw_results,
)
from src.extraction.schemas import ExtractionResult


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="문서 순번 구간 Triple 추출")
    parser.add_argument("--start", type=int, required=True, help="1-based 시작 문서 번호")
    parser.add_argument("--end", type=int, required=True, help="1-based 종료 문서 번호")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--input", type=Path, default=Path("data/processed/festivals_documents.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_checkpoint(path: Path) -> dict[str, ExtractionResult]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"checkpoint must contain a JSON list: {path}")
    return {
        str(row["source_doc_id"]): ExtractionResult.model_validate(row)
        for row in data
        if isinstance(row, dict) and row.get("source_doc_id")
    }


def run() -> None:
    args = parse_args()
    if args.start < 1 or args.end < args.start or args.batch_size < 1 or args.workers < 1:
        raise ValueError("invalid range or batch size")

    documents = load_documents(args.input)
    selected = documents[args.start - 1:args.end]
    expected_count = args.end - args.start + 1
    if len(selected) != expected_count:
        raise ValueError(f"requested docs {args.start}-{args.end}, but input has only {len(documents)} docs")

    checkpoint = load_checkpoint(args.output)
    ordered_results = [checkpoint[doc["source_doc_id"]] for doc in selected if doc["source_doc_id"] in checkpoint]
    pending = [doc for doc in selected if doc["source_doc_id"] not in checkpoint or checkpoint[doc["source_doc_id"]].error]

    for offset in range(0, len(pending), args.batch_size):
        batch = pending[offset:offset + args.batch_size]
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            results = list(
                executor.map(
                    lambda doc: extract_one(
                        doc,
                        model_factory=make_model,
                        max_retries=args.max_retries,
                    ),
                    batch,
                )
            )
        checkpoint.update({result.source_doc_id: result for result in results})
        ordered_results = [checkpoint[doc["source_doc_id"]] for doc in selected if doc["source_doc_id"] in checkpoint]
        save_raw_results(ordered_results, args.output)
        print(
            f"saved={len(ordered_results)}/{expected_count} "
            f"failed={sum(1 for result in ordered_results if result.error)}",
            flush=True,
        )

    ordered_results = [checkpoint[doc["source_doc_id"]] for doc in selected]
    save_raw_results(ordered_results, args.output)
    print(f"document_range={args.start}-{args.end}", flush=True)
    print(f"document_count={len(ordered_results)}", flush=True)
    print(f"output={args.output}", flush=True)
    print(f"failed={sum(1 for result in ordered_results if result.error)}", flush=True)
    print(f"triple_count={sum(len(result.triples) for result in ordered_results)}", flush=True)


if __name__ == "__main__":
    run()
