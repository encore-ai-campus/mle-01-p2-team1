from datetime import date

import pytest
from pydantic import ValidationError

import src.rag.answer as answer_module
from src.rag.answer import ANSWER_PROMPT, AnswerResponse, build_answer_context


def test_answer_prompt_restricts_answer_to_supplied_context():
    prompt = ANSWER_PROMPT.format(
        question="축제는 언제 열려?",
        context="축제는 10월 3일에 열린다.",
    )

    assert "주어진 context에 명시된 정보만" in prompt
    assert "외부 지식" in prompt
    assert "축제는 10월 3일에 열린다." in prompt
    assert "축제는 언제 열려?" in prompt


def test_answer_prompt_requires_source_document_id_and_evidence():
    prompt = ANSWER_PROMPT.format(question="질문", context="근거")

    assert '"sources"' in prompt
    assert '"source_doc_id"' in prompt
    assert '"evidence"' in prompt


def test_answer_prompt_allows_text2cypher_result_columns_without_source_fields():
    prompt = ANSWER_PROMPT.format(question="질문", context='[1] {"festival_name":"임실N장미축제"}')

    assert "Text2Cypher 결과의 반환 컬럼" in prompt
    assert "source_doc_id/evidence가 없어도" in prompt


def test_answer_prompt_requires_unknown_answer_when_evidence_is_insufficient():
    prompt = ANSWER_PROMPT.format(question="질문", context="")

    assert "결과가 없거나 근거가 부족하면" in prompt
    assert '"모르겠습니다."' in prompt
    assert '"sources"는 빈 배열' in prompt


def test_build_answer_context_formats_rows_as_numbered_json_lines():
    rows = [
        {"name": "부산축제", "score": 0.9},
        {"start_date": date(2026, 9, 17)},
    ]

    assert build_answer_context(rows) == (
        '[1] {"name":"부산축제","score":0.9}\n'
        '[2] {"start_date":"2026-09-17"}'
    )


def test_text2cypher_answer_falls_back_to_nonempty_result_when_llm_says_unknown():
    result = answer_module._fallback_text2cypher_answer(
        '[1] {"festival_name":"임실N장미축제"}', "모르겠습니다."
    )

    assert result == "조회 결과: 임실N장미축제"


def test_build_answer_context_limits_rows_and_total_characters():
    rows = [{"id": index, "text": "가" * 1_000} for index in range(100)]

    context = build_answer_context(rows)

    assert len(context) <= 6_000
    assert '"id":0' in context
    assert '"id":99' not in context


def test_answer_response_enforces_fixed_schema_and_retrieval_method():
    answer_response = getattr(answer_module, "AnswerResponse", None)

    assert answer_response is not None

    response = answer_response(
        answer="서울에서 열립니다.",
        sources=[
            {
                "source_doc_id": "doc-001",
                "evidence": "축제는 서울에서 열립니다.",
            }
        ],
    )
    assert response.model_dump() == {
        "answer": "서울에서 열립니다.",
        "sources": [
            {
                "source_doc_id": "doc-001",
                "evidence": "축제는 서울에서 열립니다.",
            }
        ],
        "retrieval_method": "vector",
    }

    text2cypher_response = answer_response(
        answer="서울에서 열립니다.",
        sources=[],
        retrieval_method="text2cypher",
    )
    assert text2cypher_response.retrieval_method == "text2cypher"

    with pytest.raises(ValidationError):
        answer_response(
            answer="서울에서 열립니다.",
            sources=[],
            retrieval_method="graph",
        )

    with pytest.raises(ValidationError):
        answer_response(
            answer="서울에서 열립니다.",
            sources=[],
            unexpected="value",
        )


class FakeStructuredLLM:
    def __init__(self) -> None:
        self.prompt: str | None = None

    def invoke(self, prompt: str) -> dict:
        self.prompt = prompt
        return {
            "answer": "서울에서 열립니다.",
            "sources": [
                {
                    "source_doc_id": "doc-001",
                    "evidence": "축제는 서울에서 열립니다.",
                }
            ],
            "retrieval_method": "vector",
        }


class FakeLLM:
    def __init__(self) -> None:
        self.schema = None
        self.structured_llm = FakeStructuredLLM()

    def with_structured_output(self, schema):
        self.schema = schema
        return self.structured_llm


def test_generate_answer_returns_the_actual_retrieval_method():
    llm = FakeLLM()

    result = answer_module.generate_answer(
        question="어디에서 열려?",
        context='[1] {"source_doc_id":"doc-001"}',
        llm=llm,
        retrieval_method="text2cypher",
    )

    assert llm.schema is AnswerResponse
    assert "어디에서 열려?" in llm.structured_llm.prompt
    assert '"source_doc_id":"doc-001"' in llm.structured_llm.prompt
    assert result == {
        "answer": "서울에서 열립니다.",
        "sources": [
            {
                "source_doc_id": "doc-001",
                "evidence": "축제는 서울에서 열립니다.",
            }
        ],
        "retrieval_method": "text2cypher",
    }
