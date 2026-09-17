"""검색 또는 Text2Cypher 결과를 근거와 함께 최종 답변으로 만드는 골격."""

import json
from typing import Any, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field


_MAX_CONTEXT_ROWS = 20
_MAX_CONTEXT_CHARS = 6_000
_TRUNCATION_MARKER = " …[truncated]"
RetrievalMethod = Literal["vector", "text2cypher"]


# 입력: 검색 결과 또는 Cypher 결과, 원문 근거, 사용자 질문
# 출력: answer, sources, retrieval_method
ANSWER_PROMPT = """당신은 검색 결과를 근거로 답변하는 질의응답 도우미입니다.
주어진 context에 명시된 정보만 사용하여 질문에 답하세요.
context에 없는 내용을 외부 지식, 추측 또는 임의의 해석으로 추가하거나 보완하지 마세요.
답변의 모든 사실은 context에서 직접 확인할 수 있어야 합니다.
Text2Cypher 결과를 context로 받은 경우에는 Text2Cypher 결과의 반환 컬럼과 값 자체를 근거로 사용할 수 있습니다.
이 경우 source_doc_id/evidence가 없어도 답변하고, sources는 빈 배열로 반환하세요.
답변에 사용한 출처를 "sources" 배열로 포함하세요.
각 출처는 context의 "source_doc_id"와 "evidence"를 포함해야 합니다.
결과가 없거나 근거가 부족하면 "모르겠습니다."라고 답하세요.
이 경우 "sources"는 빈 배열로 반환하세요.

[context]
{context}

[질문]
{question}
"""
class AnswerSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_doc_id: str
    evidence: str


class AnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    sources: list[AnswerSource] = Field(default_factory=list)
    retrieval_method: RetrievalMethod = "vector"


def build_answer_context(rows: Sequence[dict[str, Any]]) -> str:
    """검색 결과를 답변용 context로 만든다."""
    lines: list[str] = []
    used_characters = 0

    for index, row in enumerate(rows[:_MAX_CONTEXT_ROWS], start=1):
        serialized = json.dumps(
            row,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )
        line = f"[{index}] {serialized}"
        separator_length = 1 if lines else 0
        remaining = _MAX_CONTEXT_CHARS - used_characters - separator_length

        if remaining <= 0:
            break
        if len(line) > remaining:
            if remaining > len(_TRUNCATION_MARKER):
                line = line[: remaining - len(_TRUNCATION_MARKER)] + _TRUNCATION_MARKER
            else:
                line = line[:remaining]
            lines.append(line)
            break

        lines.append(line)
        used_characters += separator_length + len(line)

    return "\n".join(lines)


def _fallback_text2cypher_answer(context: str, answer: str) -> str:
    """LLM이 결과가 있는데 모른다고 할 때 조회값을 직접 표시한다."""
    if answer.strip() != "모르겠습니다." or not context.strip():
        return answer
    values: list[str] = []
    for line in context.splitlines():
        try:
            row = json.loads(line.split("] ", 1)[1])
        except (IndexError, json.JSONDecodeError):
            continue
        for value in row.values():
            if value is not None and str(value) not in values:
                values.append(str(value))
    return f"조회 결과: {', '.join(values)}" if values else answer


def generate_answer(
    question: str,
    context: str,
    llm: Any,
    retrieval_method: RetrievalMethod = "vector",
) -> dict[str, Any]:
    """근거 context에 기반한 최종 답변을 만든다."""
    prompt = ANSWER_PROMPT.format(
        question=question,
        context=context,
    )

    structured_llm = llm.with_structured_output(AnswerResponse)
    result = structured_llm.invoke(prompt)

    if not isinstance(result, AnswerResponse):
        result = AnswerResponse.model_validate(result)

    response = AnswerResponse(
        answer=(
            _fallback_text2cypher_answer(context, result.answer)
            if retrieval_method == "text2cypher"
            else result.answer
        ),
        sources=result.sources,
        retrieval_method=retrieval_method,
    )
    return response.model_dump(mode="json")


# 최소 예시: {"answer": "...", "sources": [{"source_doc_id": "...", "evidence": "..."}], "retrieval_method": "vector"}
# 완료 조건: 근거 없는 답변은 생성하지 않고 모든 답변에 출처를 연결한다.
# Freeze point: answer 응답 key는 app과 QA 작성 이후 변경하지 않는다.
