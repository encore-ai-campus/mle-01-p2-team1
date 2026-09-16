"""검증된 Triple의 Entity mention을 canonical entity로 통합하는 ER 골격."""

from typing import Any, Sequence


# 입력: validated_triples.json 또는 ValidationRecord의 clean Triple 목록
# 출력: resolved_entities.json, resolved_triples.json, er_candidates.json, er_report.json
# TODO 1. subject/object와 타입, 문서 ID, role을 Entity mention 목록으로 수집한다.
# TODO 2. 공백·특수문자·괄호 처리 규칙을 고정한 comparison_name 정규화 함수를 만든다.
# TODO 3. (entity_type, comparison_name)을 기준으로 exact match를 그룹화한다.
# TODO 4. 같은 타입 안에서만 fuzzy 후보를 만들고 similarity와 decision을 보존한다.
# TODO 5. embedding은 자동 병합이 아니라 후보 보강용으로만 연결한다.
# TODO 6. canonical_name을 결정하고 원본 이름과 매핑한다.
# TODO 7. 모든 Triple의 subject/object를 canonical_name으로 치환한다.
# TODO 8. ER 이후 중복 Triple을 제거하고 source_doc_id와 evidence를 보존한다.
# TODO 9. 병합 전후 Entity 수, 후보 수, 자동/수동 판정 수를 er_report에 저장한다.


def collect_entity_mentions(validated_triples: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Triple의 subject/object를 Entity mention 레코드로 수집한다."""
    raise NotImplementedError


def normalize_comparison_name(name: str) -> str:
    """Entity 비교용 이름을 정규화한다. 원본 name은 변경하지 않는다."""
    raise NotImplementedError


def resolve_entities(mentions: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """exact/fuzzy 후보를 만들고 canonical entity와 매핑 결과를 반환한다."""
    raise NotImplementedError


def apply_entity_mapping(triples: Sequence[dict[str, Any]], mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Entity mapping을 Triple의 subject/object에 반영한다."""
    raise NotImplementedError


def build_er_report(before: Sequence[dict[str, Any]], after: Sequence[dict[str, Any]], candidates: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """ER 전후 개수와 후보 통계를 만든다."""
    raise NotImplementedError


# 최소 예시: {"name": "유플페", "entity_type": "Festival", "source_doc_id": "1", "role": "subject"}
# 완료 조건: 타입이 다른 Entity는 병합하지 않고, 원본 이름·문서 ID·role을 재현할 수 있다.
# Freeze point: canonical_name 결정 규칙과 자동 병합 threshold는 팀 승인 없이 바꾸지 않는다.
