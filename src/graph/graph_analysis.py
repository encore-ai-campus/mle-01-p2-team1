"""Neo4j GDS 기반 Graph 분석을 연결하는 골격."""

from typing import Any


# 입력: Neo4j driver, 분석 대상 Node/Relationship 범위
# 출력: graph_analysis_report.json
# TODO 1. 분석용 graph projection의 대상 label과 relationship을 정한다.
# TODO 2. PageRank를 실행하고 상위 Node와 점수를 저장한다.
# TODO 3. Louvain 또는 Leiden community detection을 실행한다.
# TODO 4. 분석 결과를 단순 숫자가 아니라 Entity/관계 맥락과 함께 해석한다.
# TODO 5. projection 삭제 여부와 분석 실행 시간을 report에 기록한다.


def create_graph_projection(driver: Any, graph_name: str) -> None:
    """GDS 분석용 named graph projection을 만든다."""
    raise NotImplementedError


def run_pagerank(driver: Any, graph_name: str, limit: int = 10) -> list[dict[str, Any]]:
    """PageRank 상위 Node를 반환한다."""
    raise NotImplementedError


def run_community_detection(driver: Any, graph_name: str) -> list[dict[str, Any]]:
    """Community detection 결과를 반환한다."""
    raise NotImplementedError


def build_graph_analysis_report(driver: Any, graph_name: str = "festival_graph") -> dict[str, Any]:
    """Graph 분석 결과를 하나의 report로 묶는다."""
    raise NotImplementedError


# 완료 조건: projection, PageRank, community 결과와 해석용 대표 Node가 저장된다.
# Freeze point: 분석 projection 구성과 알고리즘 파라미터는 결과 비교 전 고정한다.
