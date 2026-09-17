"""Text2Cypher, Retrieval, 최종 QA 품질을 평가하는 골격."""

from typing import Any, Sequence


# 입력: qa_gold.json, 질문별 실행 결과
# 출력: qa_report.json
# TODO 1. question, expected_entity, expected_relation/expected_answer를 갖는 Golden QA를 만든다.
# TODO 2. Text2Cypher 성공 여부와 실행 가능한 query 비율을 계산한다.
# TODO 3. Vector와 Full-text의 Hit@K를 계산한다.
# TODO 4. 정답 순위를 사용해 MRR을 계산한다.
# TODO 5. 최종 answer의 manual_correct_rate 또는 answer_precision을 기록한다.
# TODO 6. method별 상세 오류와 총합 지표를 qa_report.json으로 저장한다.


# TODO 7. Accommodation/Experience 대상 Golden QA를 추가한다.
# TODO 8. nearby/숙소 질의에 대해 거리 조건, Top-k, entity hit 결과를 평가한다.

def calculate_hit_at_k(expected: str, results: Sequence[dict[str, Any]], k: int) -> float:
    """검색 결과 k개 안에 기대 Entity가 있는지 계산한다."""
    raise NotImplementedError


def calculate_mrr(expected: str, results: Sequence[dict[str, Any]]) -> float:
    """기대 Entity의 reciprocal rank를 계산한다."""
    raise NotImplementedError


def evaluate_qa(gold_rows: Sequence[dict[str, Any]], run_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """QA 전체 지표와 질문별 결과를 집계한다."""
    raise NotImplementedError


# 완료 조건: Text2Cypher 성공률, Vector/Full-text Hit@K, MRR, 최종 답변 정확도가 보고된다.
# Freeze point: Golden QA와 metric 정의는 비교 실험 시작 후 변경하지 않는다.
