"""검색·GraphRAG QA·Graph 확인 화면을 연결하는 Streamlit 골격."""

from typing import Any


# 입력: router, retrieval, text2cypher, answer 서비스
# 출력: Streamlit 화면
# TODO 1. 축제 검색 화면에서 query와 filter를 받고 Full-text 결과를 보여준다.
# TODO 2. GraphRAG Q&A 화면에서 질문, 선택 tool, 답변, source evidence를 보여준다.
# TODO 3. Knowledge Graph 화면에서 Festival 중심 subgraph와 연결 타입을 보여준다.
# TODO 4. 파이프라인 통계 화면에서 Triple 수, Schema 준수율, Reject율, ER/Graph 지표를 보여준다.
# TODO 5. 외부 시스템 오류를 사용자에게 안전하게 표시하고 비밀값은 화면에 노출하지 않는다.


def render_search_page(services: dict[str, Any]) -> None:
    """축제 검색 페이지를 렌더링한다."""
    raise NotImplementedError


def render_qa_page(services: dict[str, Any]) -> None:
    """GraphRAG QA 페이지를 렌더링한다."""
    raise NotImplementedError


def render_graph_page(services: dict[str, Any]) -> None:
    """Knowledge Graph 페이지를 렌더링한다."""
    raise NotImplementedError


def main() -> None:
    """Streamlit 앱 진입점."""
    raise NotImplementedError


# 완료 조건: 검색, QA, Graph, 품질 지표를 서로 독립적으로 확인할 수 있다.
# Freeze point: 화면에서 사용하는 서비스 인터페이스는 백엔드 모듈 합의 후 고정한다.
