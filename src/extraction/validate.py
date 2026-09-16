"""Raw Triple을 고정된 5단계 순서로 검증하는 모듈."""

import re
from dataclasses import dataclass, field
from typing import Sequence

from pydantic import ValidationError

from src.extraction.ontology import RELATION_SIGNATURES
from src.extraction.schemas import EntityType, RelationType, Triple


@dataclass
class ValidationRecord:
    """Triple과 검증 결과를 함께 보관한다."""

    triple: dict
    passed: bool
    stage: str
    error_codes: list[str] = field(default_factory=list)


def normalize_text(value: str) -> str:
    """앞뒤 공백과 연속 공백을 비교 가능한 형태로 정규화한다."""
    return re.sub(r"\s+", " ", value).strip()


def check_relation_signature(row: dict) -> str | None:
    """Relation과 주어/목적어 타입의 Signature를 검사한다."""
    relation_value = row.get("relation")

    try:
        relation = RelationType(relation_value)
    except (TypeError, ValueError):
        return "허용되지 않은 관계"

    signature = RELATION_SIGNATURES.get(relation)
    if signature is None:
        return "허용되지 않은 관계"

    expected_subject_type, expected_object_type, _ = signature

    try:
        subject_type = EntityType(row.get("subject_type"))
        object_type = EntityType(row.get("object_type"))
    except (TypeError, ValueError):
        return "허용되지 않은 Entity 타입"

    if subject_type != expected_subject_type:
        return "주어 타입이 relation signature와 다름"

    if object_type != expected_object_type:
        return "목적어 타입이 relation signature와 다름"

    return None


def check_evidence(
    row: dict,
    documents_by_id: dict[str, dict[str, str]],
) -> str | None:
    """Evidence가 실제 출처 문서에 포함되는지 검사한다."""
    evidence = row.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        return "evidence가 비어 있음"

    document = documents_by_id.get(str(row.get("source_doc_id", "")))
    if document is None:
        return "출처 문서가 없음"

    source_text = document.get("text", "")
    if normalize_text(evidence) not in normalize_text(source_text):
        return "evidence가 원문에 없음"

    return None


def triple_key(row: dict) -> tuple[str, str, str, str]:
    """중복 검사용 정규화 key를 만든다."""
    return (
        normalize_text(str(row.get("subject", ""))),
        str(row.get("relation", "")),
        normalize_text(str(row.get("object", ""))),
        str(row.get("source_doc_id", "")),
    )


def validate_triples(
    raw_triples: Sequence[dict],
    source_text_by_doc: dict[str, str],
) -> tuple[list[ValidationRecord], list[ValidationRecord]]:
    """schema -> relation -> signature -> evidence -> duplicate 순서로 검증한다."""
    documents_by_id = {
        str(doc_id): {"text": text}
        for doc_id, text in source_text_by_doc.items()
    }

    clean_records: list[ValidationRecord] = []
    rejected_records: list[ValidationRecord] = []
    seen_keys: set[tuple[str, str, str, str]] = set()

    for raw_row in raw_triples:
        try:
            triple = Triple.model_validate(raw_row)
            row = triple.model_dump()
        except ValidationError as error:
            rejected_records.append(
                ValidationRecord(
                    triple=raw_row,
                    passed=False,
                    stage="schema",
                    error_codes=["SCHEMA_INVALID"],
                )
            )
            continue

        try:
            RelationType(row.get("relation"))
            relation_is_known = True
        except (TypeError, ValueError):
            relation_is_known = False

        if not relation_is_known:
            rejected_records.append(
                ValidationRecord(
                    triple=row,
                    passed=False,
                    stage="relation",
                    error_codes=["RELATION_INVALID"],
                )
            )
            continue

        reason = check_relation_signature(row)
        if reason is not None:
            rejected_records.append(
                ValidationRecord(
                    triple=row,
                    passed=False,
                    stage="signature",
                    error_codes=["SIGNATURE_INVALID"],
                )
            )
            continue

        reason = check_evidence(row, documents_by_id)
        if reason is not None:
            rejected_records.append(
                ValidationRecord(
                    triple=row,
                    passed=False,
                    stage="evidence",
                    error_codes=["EVIDENCE_NOT_FOUND"],
                )
            )
            continue

        key = triple_key(row)
        if key in seen_keys:
            rejected_records.append(
                ValidationRecord(
                    triple=row,
                    passed=False,
                    stage="duplicate",
                    error_codes=["DUPLICATE"],
                )
            )
            continue

        seen_keys.add(key)
        clean_records.append(
            ValidationRecord(
                triple=row,
                passed=True,
                stage="pass",
            )
        )

    return clean_records, rejected_records


# 완료 조건: 앞 단계 실패 항목은 뒤 단계로 이동하지 않고, Reject마다 오류 코드가 있다.
# Freeze point: schema -> relation -> signature -> evidence -> duplicate 순서는 변경하지 않는다.
