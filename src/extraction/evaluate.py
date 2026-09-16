"""샘플 검토와 전체 검증 통계를 집계하고 요약 파일을 저장한다.

[교안 대응 TODO]
- TODO A. 교안의 Counter(row["reject_reason"] for row in reject_triples) 집계를 구현한다.
- TODO B. 교안에는 없는 단계별 통계, 샘플 평가, validation_summary.json 저장은 그대로 유지한다.
- TODO 1: 단계별 통과/실패 수, 오류 코드별 수, 중복 수를 집계한다.
- TODO 2: 샘플 10~20건의 사람 검토 결과(정답/오답/보류)를 입력받아 평가 시트 구조를 만든다.
- TODO 3: sample/full 모드 공통으로 validation_summary.json을 저장한다.

완료 조건: raw 총량, clean/rejected 수, 단계별 오류, duplicate 수가 한눈에 재현된다.
Freeze point: 요약 key 이름은 run_pipeline과 함께 고정한다.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any

from src.extraction.validate import ValidationRecord

VERDICTS = ("정답", "오답", "보류")
DEFAULT_VERDICT = "보류"
DUPLICATE_ERROR_CODE = "DUPLICATE"
LEGACY_DUPLICATE_REASON = "duplicate_doc_id"
DUPLICATE_MARKERS = {DUPLICATE_ERROR_CODE, LEGACY_DUPLICATE_REASON}


def _get(record: ValidationRecord | dict[str, Any], key: str, default: Any = None) -> Any:
    """ValidationRecord와 dict 입력을 같은 방식으로 읽는다."""
    if isinstance(record, dict):
        return record.get(key, default)

    return getattr(record, key, default)


def _count_error_codes(records: Sequence[ValidationRecord]) -> Counter[str]:
    """검증 레코드의 오류 코드를 평탄화해 집계한다."""
    return Counter(
        error_code
        for record in records
        for error_code in (_get(record, "error_codes", []) or [])
    )


def _count_reject_reasons(records: Sequence[ValidationRecord]) -> Counter[str]:
    """검증 레코드의 reject_reason 값을 집계한다."""
    return Counter(
        reject_reason
        for record in records
        if (reject_reason := _get(record, "reject_reason")) is not None
    )


def _is_duplicate_record(record: ValidationRecord | dict[str, Any]) -> bool:
    """중복 reject를 레코드 단위로 판정한다."""
    error_codes = set(_get(record, "error_codes", []) or [])
    reject_reason = _get(record, "reject_reason")

    return bool(error_codes & DUPLICATE_MARKERS) or reject_reason in DUPLICATE_MARKERS


def summarize_validation(
    clean: Sequence[ValidationRecord],
    rejected: Sequence[ValidationRecord],
) -> dict[str, Any]:
    """검증 결과를 JSON 직렬화 가능한 요약으로 만든다."""

    total_count = len(clean) + len(rejected)
    clean_count = len(clean)
    rejected_count = len(rejected)
    rejected_stage_counts = Counter(
        _get(row, "stage", "unknown") for row in rejected
    )
    reject_reason_counts = _count_reject_reasons(rejected)
    error_code_counts = _count_error_codes(rejected)
    duplicate_count = sum(1 for row in rejected if _is_duplicate_record(row))

    return {
        "total_count": total_count,
        "clean_count": clean_count,
        "rejected_count": rejected_count,
        "clean_stage_counts": dict(
            Counter(_get(row, "stage", "unknown") for row in clean)
        ),
        "rejected_stage_counts": dict(rejected_stage_counts),
        "reject_reason_counts": dict(reject_reason_counts),
        "error_code_counts": dict(error_code_counts),
        "duplicate_count": duplicate_count,
        "go_count": clean_count,
        "no_go_count": rejected_count,
    }


def evaluate_sample(
    records: Sequence[ValidationRecord],
) -> dict[str, Any]:
    """샘플 검토 결과를 집계한다."""

    verdict_counts = dict.fromkeys(VERDICTS, 0)

    review_rows = []

    for row in records:
        verdict = _get(row, "verdict", DEFAULT_VERDICT)

        if verdict not in verdict_counts:
            verdict = DEFAULT_VERDICT

        verdict_counts[verdict] += 1

        review_rows.append(
            {
                "source_doc_id": _get(row, "source_doc_id"),
                "triple": _get(row, "triple"),
                "verdict": verdict,
                "error_description": _get(row, "error_description", ""),
                "reviewer": _get(row, "reviewer", ""),
                "reviewed_at": _get(row, "reviewed_at", ""),
            }
        )

    total = len(review_rows)
    judged_count = verdict_counts["정답"] + verdict_counts["오답"]
    accuracy = verdict_counts["정답"] / judged_count if judged_count else 0.0

    return {
        "sample_count": total,
        "correct_count": verdict_counts["정답"],
        "incorrect_count": verdict_counts["오답"],
        "pending_count": verdict_counts["보류"],
        "accuracy": accuracy,
        "verdict_counts": verdict_counts,
        "reviews": review_rows,
    }


def _to_json_serializable(value: Any) -> Any:
    """Enum, Path 등을 JSON 직렬화 가능한 값으로 변환한다."""
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return _to_json_serializable(asdict(value))

    if isinstance(value, dict):
        return {
            str(key): _to_json_serializable(val)
            for key, val in value.items()
        }

    if isinstance(value, (set, frozenset)):
        return [_to_json_serializable(item) for item in sorted(value, key=str)]

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [_to_json_serializable(item) for item in value]

    return value


def save_summary(summary: dict[str, Any], output_path: Path) -> None:
    """요약 통계를 JSON으로 저장한다."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    serializable_summary = _to_json_serializable(summary)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(serializable_summary, f, ensure_ascii=False, indent=2)

    with output_path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded == serializable_summary, (
        "validation_summary.json 저장/재로드 결과가 다릅니다."
    )
