"""Raw Triple을 고정된 5단계 순서로 검증하는 모듈."""

import re
from dataclasses import dataclass, field
from typing import Sequence

from pydantic import ValidationError

from src.extraction.ontology import is_allowed_signature
from src.extraction.schemas import EntityType, RelationType, Triple


@dataclass
class ValidationRecord:
    """Triple과 검증 결과, 단계, 오류 코드를 함께 보관한다."""

    triple: dict
    passed: bool
    stage: str
    error_codes: list[str] = field(default_factory=list)


def normalize_text(value: str) -> str:
    """연속 공백을 하나로 바꿔 Evidence 포함 여부를 비교한다."""
    return re.sub(r"\s+", " ", value).strip()


def check_relation_signature(row: dict) -> str | None:
    """Relation과 Subject/Object 타입의 허용 조합을 확인한다."""
    try:
        relation = RelationType(row.get("relation"))
        subject_type = EntityType(row.get("subject_type"))
        object_type = EntityType(row.get("object_type"))
    except (TypeError, ValueError):
        return "허용되지 않은 Entity 또는 Relation 타입"

    if not is_allowed_signature(subject_type, relation, object_type):
        return "주어/목적어 타입 조합이 Relation Signature와 다름"
    return None


def check_evidence(row: dict, documents_by_id: dict[str, dict[str, str]]) -> str | None:
    """Evidence가 해당 source 문서에 실제로 포함되는지 확인한다."""
    evidence = row.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        return "Evidence가 비어 있음"
    document = documents_by_id.get(str(row.get("source_doc_id", "")))
    if document is None:
        return "Source 문서가 없음"
    if normalize_text(evidence) not in normalize_text(document.get("text", "")):
        return "Evidence가 원문에 없음"
    return None


def triple_key(row: dict) -> tuple[str, str, str, str]:
    """중복 판정용 정규화 key를 만든다."""
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
    documents_by_id = {str(doc_id): {"text": text} for doc_id, text in source_text_by_doc.items()}
    clean_records: list[ValidationRecord] = []
    rejected_records: list[ValidationRecord] = []
    seen_keys: set[tuple[str, str, str, str]] = set()

    for raw_row in raw_triples:
        try:
            row = Triple.model_validate(raw_row).model_dump(mode="json")
        except ValidationError:
            rejected_records.append(ValidationRecord(raw_row, False, "schema", ["SCHEMA_INVALID"]))
            continue

        try:
            RelationType(row.get("relation"))
        except (TypeError, ValueError):
            rejected_records.append(ValidationRecord(row, False, "relation", ["RELATION_INVALID"]))
            continue

        if check_relation_signature(row) is not None:
            rejected_records.append(ValidationRecord(row, False, "signature", ["SIGNATURE_INVALID"]))
            continue

        if check_evidence(row, documents_by_id) is not None:
            rejected_records.append(ValidationRecord(row, False, "evidence", ["EVIDENCE_NOT_FOUND"]))
            continue

        key = triple_key(row)
        if key in seen_keys:
            rejected_records.append(ValidationRecord(row, False, "duplicate", ["DUPLICATE"]))
            continue
        seen_keys.add(key)
        clean_records.append(ValidationRecord(row, True, "pass"))

    return clean_records, rejected_records
