"""검색 또는 Text2Cypher 결과를 근거와 함께 최종 답변으로 만드는 골격."""

from typing import Any, Sequence


# 입력: 검색 결과 또는 Cypher 결과, 원문 근거, 사용자 질문
# 출력: answer, sources, retrieval_method
# TODO 1. 결과를 LLM이 읽을 수 있는 제한된 context 문자열로 변환한다.
# TODO 2. context에 없는 정보를 생성하지 않는 답변 prompt를 작성한다.
# TODO 3. source_doc_id와 evidence를 sources에 포함한다.
# TODO 4. 결과가 없거나 근거가 부족하면 모른다고 답하는 규칙을 넣는다.
# TODO 5. 최종 응답 schema와 retrieval_method 값을 고정한다.


def build_answer_context(rows: Sequence[dict[str, Any]]) -> str:
    """검색 결과를 답변용 context로 만든다."""
    raise NotImplementedError


def generate_answer(question: str, context: str, llm: Any) -> dict[str, Any]:
    """근거 context에 기반한 최종 답변을 만든다."""
    raise NotImplementedError


# 최소 예시: {"answer": "...", "sources": [{"source_doc_id": "...", "evidence": "..."}], "retrieval_method": "vector"}
# 완료 조건: 근거 없는 답변은 생성하지 않고 모든 답변에 출처를 연결한다.
# Freeze point: answer 응답 key는 app과 QA 작성 이후 변경하지 않는다.
