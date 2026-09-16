"""Ontology v1 정의와 Relation Signature 규칙을 관리하는 모듈."""

# 구현 메모
#
# TODO 1. 교안의 RELATION_SIGNATURES처럼 relation을 key로 사용하는 표를 작성한다.
#
# value는 (subject_type, object_type, criterion) 구조로 작성한다.
# 입력: 팀이 수동 검토로 합의한 Ontology 표
# 처리: 허용된 5개 Relation과 주어/목적어 타입을 등록
# 출력: prompts.py와 validate.py가 함께 사용하는 유일한 원본 규칙
#
# 예시 후보
# - HELD_IN: Festival -> Location
# - HAS_ACTIVITY: Festival -> Activity
# - HAS_THEME: Festival -> Theme
# - HELD_DURING: Festival -> Period
# - TARGETS: Festival -> Audience
#
# 기존 SIGNATURES처럼 같은 규칙을 별도의 표에 다시 작성하지 않는다.
#
# TODO 2. 교안의 NODE_TYPES처럼 RELATION_SIGNATURES의 값에서
# subject_type과 object_type을 모아 중복 없는 EntityType 목록을 만든다.
# enum 값을 이곳에 다시 직접 나열하지 않아야 두 목록이 달라지지 않는다.
#
# TODO 3. RELATION_SIGNATURES의 key에서 RelationType 목록을 만든다.
# 별도의 관계 목록을 수동으로 관리하지 않고 원본 표에서 파생한다.
#
# TODO 4. is_allowed_signature(subject_type, relation, object_type)를 구현한다.
# RELATION_SIGNATURES에서 relation을 조회하고 주어/목적어 타입을 비교한다.
# 허용 조합이면 True, 관계가 없거나 타입 방향이 다르면 False를 반환한다.
#
# TODO 5. 허용 Signature 5개와 금지 조합 5개를 테스트한다.
# TODO 6. 각 Entity의 정의·포함·제외·애매 사례를 문서화한다.
# Freeze point: 15시 Go/No-Go 이후 enum과 RELATION_SIGNATURES는 승인 없이 변경하지 않는다.

from types import MappingProxyType
from typing import Final, TypeAlias

from src.extraction.schemas import EntityType, RelationType


RelationSignature: TypeAlias = tuple[EntityType, EntityType, str]


RELATION_SIGNATURES: Final[MappingProxyType[RelationType, RelationSignature]] = (
    MappingProxyType(
        {
            RelationType.HELD_IN: (
                EntityType.FESTIVAL,
                EntityType.LOCATION,
                "Festival is held in a specific location.",
            ),
            RelationType.HAS_ACTIVITY: (
                EntityType.FESTIVAL,
                EntityType.ACTIVITY,
                "Festival includes a specific activity or program.",
            ),
            RelationType.HAS_THEME: (
                EntityType.FESTIVAL,
                EntityType.THEME,
                "Festival has a specific theme.",
            ),
            RelationType.HELD_DURING: (
                EntityType.FESTIVAL,
                EntityType.PERIOD,
                "Festival is held during a specific period.",
            ),
            RelationType.TARGETS: (
                EntityType.FESTIVAL,
                EntityType.AUDIENCE,
                "Festival targets a specific audience.",
            ),
        }
    )
)

ALLOWED_ENTITY_TYPES: Final[tuple[EntityType, ...]] = tuple(
    dict.fromkeys(
        entity_type
        for subject_type, object_type, _ in RELATION_SIGNATURES.values()
        for entity_type in (subject_type, object_type)
    )
)

ALLOWED_RELATION_TYPES: Final[tuple[RelationType, ...]] = tuple(
    RELATION_SIGNATURES
)


def is_allowed_signature(
    subject_type: EntityType,
    relation: RelationType,
    object_type: EntityType,
) -> bool:
    """Return whether a subject-relation-object type combination is allowed."""

    signature = RELATION_SIGNATURES.get(relation)

    if signature is None:
        return False

    allowed_subject_type, allowed_object_type, _ = signature
    return (subject_type, object_type) == (
        allowed_subject_type,
        allowed_object_type,
    )

# Entity documentation
#
# FESTIVAL
# - Definition: A named festival or organized event.
# - Include: Seoul World Fireworks Festival, Boryeong Mud Festival
# - Exclude: individual activities, locations, themes
# - Ambiguous: an event whose name does not clearly indicate whether it is a festival
#
# LOCATION
# - Definition: A place or area where a festival is held.
# - Include: Yeouido Hangang Park, Seoul, Gwangalli Beach
# - Exclude: festival names, activities, periods
# - Ambiguous: a broad region when the actual festival venue is not specified
#
# ACTIVITY
# - Definition: An activity, performance, or program offered by a festival.
# - Include: fireworks show, parade, craft experience
# - Exclude: festival names, themes, audiences
# - Ambiguous: an activity that may itself be described as a separate event
#
# THEME
# - Definition: A central subject, concept, or motif of a festival.
# - Include: mud, cherry blossoms, traditional culture
# - Exclude: locations, dates, audience groups
# - Ambiguous: a seasonal expression that could represent either a theme or a period
#
# PERIOD
# - Definition: A date, season, or time range when a festival is held.
# - Include: October 3, 2026, October 3 to October 5, every spring
# - Exclude: locations, themes, activities
# - Ambiguous: a seasonal term that may also be used as part of the festival theme
#
# AUDIENCE
# - Definition: A group of people that a festival specifically targets.
# - Include: families, children, foreign tourists
# - Exclude: activities, locations, periods
# - Ambiguous: a group mentioned as possible visitors but not explicitly targeted
