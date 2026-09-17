"""Text2Cypher, Retrieval, 최종 QA 정확도를 평가하는 모듈."""

import json
from math import isfinite
from numbers import Real
from pathlib import Path
from typing import Any, Sequence

INPUT_PATH = "qa_gold.json"
GOLD_PATH = INPUT_PATH
RESULT_PATH = "qa_results.json"
OUTPUT_PATH = "qa_report.json"
K = 5


# 입력: qa_gold.json, 질문별 실행 결과
# 출력: qa_report.json
# TODO 1. question, expected_entity, expected_relation/expected_answer를 포함하는 Golden QA를 만든다.
# TODO 2. Text2Cypher 성공 여부와 실행 가능한 query 비율을 계산한다.
# TODO 3. Vector와 Full-text의 Hit@K를 계산한다.
# TODO 4. 정답 순위를 사용해 MRR을 계산한다.
# TODO 5. 최종 answer의 manual_correct_rate 또는 answer_precision을 기록한다.
# TODO 6. method별 상세 오류와 총합 지표를 qa_report.json으로 저장한다.


# 완료 7. qa_gold.json에 Accommodation/Experience 대상 Golden QA를 추가했다.
# TODO 8. nearby/숙소 질의에 대해 거리 조건, Top-k, entity hit 결과를 평가한다.


def _retrieved_items(row: dict[str, Any], method: str) -> Sequence[str]:
    """평가 행에서 지정한 검색 방식의 결과 목록을 가져온다."""
    value = row.get(f"{method}_results", ())
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _top_k_items(row: dict[str, Any]) -> Sequence[str]:
    """nearby Top-k 결과가 목록일 때만 반환한다."""
    value = row.get("top_k_results", ())
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _entity_hit(row: dict[str, Any]) -> bool:
    """명시된 entity_hit을 우선하고, 없으면 Top-k 포함 여부로 계산한다."""
    if row.get("entity_hit") is not None:
        return bool(row["entity_hit"])
    return row.get("expected_entity") in _top_k_items(row)


def _rate(values: Sequence[bool | int | float]) -> float:
    """빈 목록을 포함해 비율을 안전하게 계산한다."""
    return round(sum(values) / len(values), 4) if values else 0.0


def _normalize_answer(value: Any) -> str:
    """답변 비교를 위해 공백과 대소문자를 정규화한다."""
    return " ".join(str(value or "").split()).casefold()


def _is_nearby_row(row: dict[str, Any]) -> bool:
    """nearby 전용 필드가 있으면 method 누락 행도 nearby로 식별한다."""
    return row.get("method") == "nearby" or any(
        field in row for field in ("top_k_results", "distance_km", "max_distance_km", "entity_hit")
    )


def _distance_condition(row: dict[str, Any]) -> bool:
    """거리와 허용 거리 값이 모두 유효할 때만 거리 조건을 판정한다."""
    distance = row.get("distance_km")
    max_distance = row.get("max_distance_km")
    valid_numbers = all(
        isinstance(value, Real) and not isinstance(value, bool) and isfinite(value)
        for value in (distance, max_distance)
    )
    return valid_numbers and distance <= max_distance


def _load_json_rows(path: str | Path) -> list[dict[str, Any]]:
    """JSON 배열 형식의 QA 행을 읽는다."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path} must contain a JSON array of objects")
    return rows


def _qa_key(row: dict[str, Any]) -> tuple[str, str]:
    """QA 행을 안정적으로 식별할 qa_id 또는 question 키를 반환한다."""
    if row.get("qa_id"):
        return "qa_id", str(row["qa_id"])
    if row.get("question"):
        return "question", str(row["question"])
    raise ValueError("Each QA row must contain qa_id or question")


def _merge_gold_and_run_rows(
    gold_rows: Sequence[dict[str, Any]],
    run_rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """QA 식별자로 Golden QA와 실행 결과를 병합한다."""
    gold_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in gold_rows:
        key = _qa_key(row)
        aliases = [key]
        if row.get("qa_id") and row.get("question"):
            aliases.append(("question", str(row["question"])))
        for alias in aliases:
            if alias in gold_by_key and gold_by_key[alias] is not row:
                raise ValueError(f"Duplicate Golden QA key: {alias[1]}")
            gold_by_key[alias] = row

    results = []
    seen_run_keys: set[tuple[str, str]] = set()
    for run_row in run_rows:
        key = _qa_key(run_row)
        if key in seen_run_keys:
            raise ValueError(f"Duplicate QA result key: {key[1]}")
        seen_run_keys.add(key)
        gold_row = gold_by_key.get(key)
        if gold_row is None and run_row.get("question"):
            gold_row = gold_by_key.get(("question", str(run_row["question"])))
        if gold_row is None:
            raise ValueError(f"No matching Golden QA for result: {key[1]}")
        results.append({**gold_row, **run_row})
    return results


def calculate_hit_at_k(expected: str, results: Sequence[dict[str, Any]], k: int) -> float:
    """검색 결과 k개 안에 기대 Entity가 있는지 계산한다."""
    if k <= 0 or not results:
        return 0.0
    hits = []
    for row in results:
        retrieved = row.get("results", row.get("retrieved", row.get("vector_results", ())))
        valid_results = isinstance(retrieved, Sequence) and not isinstance(retrieved, (str, bytes))
        hits.append(expected in retrieved[:k] if valid_results else False)
    return _rate(hits)


def calculate_mrr(expected: str, results: Sequence[dict[str, Any]]) -> float:
    """기대 Entity의 reciprocal rank를 계산한다."""
    reciprocal_ranks = []
    for row in results:
        retrieved = row.get("results", row.get("retrieved", row.get("vector_results", ())))
        if not isinstance(retrieved, Sequence) or isinstance(retrieved, (str, bytes)):
            reciprocal_ranks.append(0.0)
            continue
        reciprocal_ranks.append(reciprocal_rank(retrieved, expected))
    return _rate(reciprocal_ranks)


def hit_at_k(retrieved: Sequence[str], expected: str, k: int) -> int:
    """단일 검색 결과가 k위 이내 정답을 포함하는지 반환한다."""
    return int(k > 0 and expected in retrieved[:k])


def reciprocal_rank(retrieved: Sequence[str], expected: str) -> float:
    """단일 검색 결과에서 정답의 reciprocal rank를 반환한다."""
    return next(
        (1 / rank for rank, item in enumerate(retrieved, start=1) if item == expected),
        0.0,
    )


def evaluate_qa(
    gold_rows: Sequence[dict[str, Any]],
    run_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """QA 전체 지표와 질문별 결과를 집계한다."""
    results = _merge_gold_and_run_rows(gold_rows, run_rows)
    report: dict[str, Any] = {
        "text2cypher_success_rate": _rate([bool(row.get("text2cypher_success")) for row in results]),
        "executable_query_rate": _rate([bool(row.get("query_executable")) for row in results]),
    }

    for method in ("vector", "fulltext"):
        retrieved = [_retrieved_items(row, method) for row in results]
        expected = [row.get("expected_entity", "") for row in results]
        report[f"{method}_hit@{K}"] = _rate([
            hit_at_k(items, target, K) for items, target in zip(retrieved, expected)
        ])
        report[f"{method}_mrr"] = _rate([
            reciprocal_rank(items, target) for items, target in zip(retrieved, expected)
        ])

    manual_rows = [row for row in results if row.get("manual_correct") is not None]
    report["manual_correct_rate"] = (
        _rate([bool(row["manual_correct"]) for row in manual_rows])
        if manual_rows
        else None
    )
    answer_rows = [
        row for row in results
        if row.get("manual_correct") is None and row.get("expected_answer") is not None
    ]
    report["answer_precision"] = _rate([
        _normalize_answer(row.get("answer"))
        == _normalize_answer(row.get("expected_answer"))
        for row in answer_rows
    ])
    report["errors_by_method"] = {
        "text2cypher": [row for row in results if not row.get("text2cypher_success", False)],
        "vector": [row for row in results if row.get("expected_entity") not in _retrieved_items(row, "vector")],
        "fulltext": [row for row in results if row.get("expected_entity") not in _retrieved_items(row, "fulltext")],
        "answer": [
            row for row in results
            if row.get("manual_correct") is False
            or (
                row.get("manual_correct") is None
                and row.get("expected_answer") is not None
                and _normalize_answer(row.get("answer"))
                != _normalize_answer(row.get("expected_answer"))
            )
        ],
    }

    nearby_rows = [row for row in results if _is_nearby_row(row)]
    report["nearby"] = {
        "evaluated_rows": len(nearby_rows),
        "rows_missing_method": sum(row.get("method") != "nearby" for row in nearby_rows),
        "distance_condition_rate": _rate([
            _distance_condition(row)
            for row in nearby_rows
        ]),
        "topk_hit_rate": _rate([
            row.get("expected_entity") in _top_k_items(row) for row in nearby_rows
        ]),
        "entity_hit_rate": _rate([_entity_hit(row) for row in nearby_rows]),
    }
    report["summary"] = {
        key: report[key]
        for key in (
            "text2cypher_success_rate", "executable_query_rate",
            f"vector_hit@{K}", f"fulltext_hit@{K}",
            "vector_mrr", "fulltext_mrr", "manual_correct_rate",
            "answer_precision",
        )
    }
    report["results"] = results
    report["total"] = len(results)
    return report


def main(
    gold_path: str | Path = GOLD_PATH,
    result_path: str | Path = RESULT_PATH,
    output_path: str | Path = OUTPUT_PATH,
) -> dict[str, Any]:
    """Golden QA와 실행 결과 파일을 읽어 평가 보고서를 저장한다."""
    gold_rows = _load_json_rows(gold_path)
    run_rows = _load_json_rows(result_path)
    report = evaluate_qa(gold_rows, run_rows)
    Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


# 완료 조건: Text2Cypher 성공률, Vector/Full-text Hit@K, MRR, 최종 답변 정확도가 보고된다.
# Freeze point: Golden QA와 metric 정의는 비교 실험 시작 후 변경하지 않는다.


if __name__ == "__main__":
    main()
