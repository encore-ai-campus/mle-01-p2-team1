"""Entity와 Relation의 허용 조합을 관리하는 Ontology 모듈."""

from types import MappingProxyType
from typing import Final, TypeAlias

from src.extraction.schemas import EntityType, RelationType


SignatureKey: TypeAlias = tuple[EntityType, RelationType, EntityType]


# TODO: 아래 표를 Ontology의 유일한 원본으로 사용한다.
# 같은 Relation이 여러 Subject/Object 조합에 등장하므로
# (SubjectType, RelationType, ObjectType) 전체를 key로 사용한다.
RELATION_SIGNATURES: Final = MappingProxyType({
    (EntityType.FESTIVAL, RelationType.HELD_IN, EntityType.LOCATION):
        "축제가 특정 장소에서 개최됨",
    (EntityType.FESTIVAL, RelationType.TARGETS, EntityType.AUDIENCE):
        "축제가 특정 대상을 대상으로 함",
    (EntityType.FESTIVAL, RelationType.HAS_PROGRAM, EntityType.PROGRAM):
        "축제가 특정 프로그램을 포함함",
    (EntityType.FESTIVAL, RelationType.HAS_THEME, EntityType.THEME):
        "축제가 특정 주제와 관련됨",
    (EntityType.FESTIVAL, RelationType.FEATURES, EntityType.ARTIST):
        "축제에 특정 아티스트가 참여함",
    (EntityType.FESTIVAL, RelationType.PROVIDES, EntityType.PRODUCT):
        "축제가 특정 상품을 제공함",
    (EntityType.ORGANIZATION, RelationType.ORGANIZES, EntityType.FESTIVAL):
        "기관이 축제를 주최함",
    (EntityType.PROGRAM, RelationType.HELD_IN, EntityType.LOCATION):
        "프로그램이 특정 장소에서 진행됨",
    (EntityType.PROGRAM, RelationType.TARGETS, EntityType.AUDIENCE):
        "프로그램이 특정 대상을 대상으로 함",
    (EntityType.ARTIST, RelationType.HAS_THEME, EntityType.THEME):
        "아티스트가 특정 주제와 관련됨",
    (EntityType.AUDIENCE, RelationType.HAS_PROGRAM, EntityType.PROGRAM):
        "대상이 특정 프로그램과 관련됨",
    (EntityType.PRODUCT, RelationType.HELD_IN, EntityType.LOCATION):
        "상품이 특정 장소와 관련됨",
    (EntityType.THEME, RelationType.FEATURES, EntityType.ARTIST):
        "주제가 특정 아티스트와 관련됨",
})


# TODO: 아래 목록은 RELATION_SIGNATURES의 key에서 자동으로 파생한다.
ALLOWED_ENTITY_TYPES: Final[tuple[EntityType, ...]] = tuple(
    dict.fromkeys(
        entity_type
        for subject_type, _, object_type in RELATION_SIGNATURES
        for entity_type in (subject_type, object_type)
    )
)

ALLOWED_RELATION_TYPES: Final[tuple[RelationType, ...]] = tuple(
    dict.fromkeys(relation for _, relation, _ in RELATION_SIGNATURES)
)


def is_allowed_signature(
    subject_type: EntityType,
    relation: RelationType,
    object_type: EntityType,
) -> bool:
    """주어-관계-목적어 타입 조합이 허용되는지 반환한다."""
    return (subject_type, relation, object_type) in RELATION_SIGNATURES


# Freeze point: 15시 Go/No-Go 이후 enum과 Signature는 승인 없이 변경하지 않는다.
