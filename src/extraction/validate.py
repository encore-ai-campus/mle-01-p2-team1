"""Raw Triple을 고정된 5단계 순서로 검증하는 모듈."""

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class ValidationRecord:
    """Triple과 검증 결과를 함께 보관한다."""
    triple: dict
    passed: bool
    stage: str
    error_codes: list[str] = field(default_factory=list)


# TODO 1. check_relation_signature(row) -> str | None을 교안대로 구현한다.
# 1. relation이 허용 목록에 있는지 확인한다.
# 2. Ontology의 RELATION_SIGNATURES에서 기대하는 주어/목적어 타입을 조회한다.
# 3. row의 subject_type/object_type과 비교한다.
# 4. 통과하면 None, 실패하면 사람이 읽을 수 있는 오류 메시지를 반환한다.
def check_relation_signature(row: dict) -> str | None:
    """Relation과 주어/목적어 타입의 방향을 검사한다."""
    raise NotImplementedError


# TODO 2. check_evidence(row, documents_by_id) -> str | None을 교안대로 구현한다.
# 1. evidence가 문자열이고 비어 있지 않은지 확인한다.
# 2. source_doc_id로 원문 문서를 찾는다.
# 3. 공백/줄바꿈만 정규화한 evidence가 원문에 포함되는지 검사한다.
# 원문에 없는 문장이나 요약문을 새로 만들지 않는다.
def check_evidence(
    row: dict,
    documents_by_id: dict[str, dict[str, str]],
) -> str | None:
    """Evidence가 실제 출처 문서에 포함되는지 검사한다."""
    raise NotImplementedError


# TODO 3. triple_key(row) -> tuple을 교안대로 구현한다.
# 기본 후보는 (subject, relation, object)이다.
# 현재 프로젝트 요구사항에 따라 source_doc_id를 네 번째 값으로 포함한다.
def triple_key(row: dict) -> tuple:
    """중복 검사용 정규화 key를 만든다."""
    raise NotImplementedError


# TODO 4. validate_triples(raw_triples, source_text_by_doc)를 구현한다.
# 반드시 schema -> relation -> signature -> evidence -> duplicate 순서를 지킨다.
# 앞 단계에서 실패한 Triple은 즉시 rejected에 넣고 다음 단계로 보내지 않는다.
# 오류 코드는 SCHEMA_INVALID, RELATION_INVALID, SIGNATURE_INVALID,
# EVIDENCE_NOT_FOUND, DUPLICATE 중 하나 이상을 남긴다.
def validate_triples(
    raw_triples: Sequence[dict],
    source_text_by_doc: dict[str, str],
) -> tuple[list[ValidationRecord], list[ValidationRecord]]:
    """검증을 수행하고 clean/rejected 결과를 반환한다."""
    raise NotImplementedError


# 완료 조건: Reject마다 실패 단계와 오류 코드가 있고, clean은 5단계를 모두 통과한다.
# Freeze point: 위 5단계 검증 순서는 팀 합의 후 변경하지 않는다.
