"""샘플 검토와 전체 검증 통계를 집계하고 요약 파일을 저장한다."""

from pathlib import Path
from typing import Any, Sequence

from src.extraction.validate import ValidationRecord

# [교안 대응 TODO]
# TODO A. 교안의 Counter(row["reject_reason"] for row in reject_triples) 집계를 구현한다.
# TODO B. 교안에는 없는 단계별 통계, 샘플 평가, validation_summary.json 저장은 그대로 유지한다.


# TODO 1: 단계별 통과/실패 수, 오류 코드별 수, 중복 수를 집계한다.
# 0건 입력도 0으로 출력하며, 사람이 읽기 쉬운 전체 수와 후속 Go/No-Go 계산용 수를 함께 둔다.
def summarize_validation(
    clean: Sequence[ValidationRecord], rejected: Sequence[ValidationRecord]
) -> dict[str, Any]:
    """검증 결과를 JSON 직렬화 가능한 요약으로 만든다."""
    raise NotImplementedError


# TODO 2: 샘플 10~20건의 사람 검토 결과(정답/오답/보류)를 입력받아 평가 시트 구조를 만든다.
# 검토 항목에는 source_doc_id, Triple, 판정, 오류 설명, 검토자, 검토 시각을 포함한다.
def evaluate_sample(records: Sequence[ValidationRecord]) -> dict[str, Any]:
    """샘플 검토 결과를 집계한다."""
    raise NotImplementedError


# TODO 3: sample/full 모드 공통으로 validation_summary.json을 저장한다.
# JSON 직렬화 불가능한 Enum/Path는 저장 전 문자열로 변환하고, 저장 후 재로드 테스트를 한다.
def save_summary(summary: dict[str, Any], output_path: Path) -> None:
    """요약 통계를 JSON으로 저장한다."""
    raise NotImplementedError


# 완료 조건: raw 총량, clean/rejected 수, 단계별 오류, duplicate 수가 한눈에 재현된다.
# Freeze point: 요약 key 이름은 run_pipeline과 함께 고정한다.
