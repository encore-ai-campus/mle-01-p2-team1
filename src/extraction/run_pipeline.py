"""sample/full 실행 순서와 Go/No-Go 제어를 담당하는 얇은 오케스트레이터."""

from argparse import Namespace
from pathlib import Path
from typing import Any

# [교안 대응 TODO]
# TODO A. 교안 마지막 실행부처럼 extract -> validate -> save -> print 통계를 main에 연결한다.
# TODO B. 교안에 없는 sample/full 분기, Go/No-Go, 출력 경로 설정은 현재 프로젝트 요구사항으로 유지한다.


# TODO 1: --mode(sample|full), input, output, retry, threshold 경로/옵션을 정의한다.
# 기본 출력 파일명은 triples_raw.json, triples_clean.json, triples_rejected.json,
# validation_summary.json으로 통일하고, output 디렉터리만 CLI에서 받는다.
def parse_args(argv: list[str] | None = None) -> Namespace:
    """CLI 인자를 파싱한다."""
    raise NotImplementedError


# TODO 2: load -> extract -> raw 저장 -> 5단계 validate -> clean/rejected 저장 -> evaluate 순서를 연결한다.
# 각 단계의 입력/출력을 지역 변수로 분리해 중간 파일만으로 재실행할 수 있게 설계한다.
# TODO 3: sample 모드에서는 평가 시트를 만들고, full 모드에서는 전체 통계와 Go/No-Go 기준을 적용한다.
# 기준 미달이면 요약에 go_no_go="NO-GO"와 사유를 남기고, 기준은 코드 상수로 명시한다.
# TODO 4: 어느 단계 실패인지 명확히 출력하되 문서별 LLM 실패는 배치를 계속 진행한다.
# TODO 5: 모듈 실행은 `python -m src.extraction.run_pipeline` 기준으로 문서화한다.
def run_pipeline(args: Namespace) -> dict[str, Any]:
    """공통 파이프라인을 실행하고 요약을 반환한다."""
    raise NotImplementedError


def main() -> None:
    """CLI 진입점."""
    raise NotImplementedError


# 예시: python -m src.extraction.run_pipeline --mode sample --input data/docs.json
# 완료 조건: sample/full 모두 triples_raw.json, triples_clean.json, triples_rejected.json,
# validation_summary.json 경로가 TODO에서 연결되고, 기준 미달이면 Go가 아닌 상태로 종료한다.
# Freeze point: ER, Neo4j, GDS, Text2Cypher, Streamlit 단계는 추가하지 않는다.
