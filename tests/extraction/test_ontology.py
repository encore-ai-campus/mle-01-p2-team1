from src.extraction.ontology import (
    ALLOWED_ENTITY_TYPES,
    ALLOWED_RELATION_TYPES,
    RELATION_SIGNATURES,
    is_allowed_signature,
)
from src.extraction.schemas import EntityType, RelationType


def test_allowed_entity_types_are_derived_from_relation_signatures():
    assert ALLOWED_ENTITY_TYPES == (
        EntityType.FESTIVAL,
        EntityType.LOCATION,
        EntityType.AUDIENCE,
        EntityType.PROGRAM,
        EntityType.THEME,
        EntityType.ARTIST,
        EntityType.PRODUCT,
        EntityType.ORGANIZATION,
    )


def test_allowed_relation_types_are_derived_from_relation_signatures():
    expected = tuple(dict.fromkeys(relation for _, relation, _ in RELATION_SIGNATURES))
    assert ALLOWED_RELATION_TYPES == expected


def test_all_declared_signatures_are_allowed():
    for subject_type, relation, object_type in RELATION_SIGNATURES:
        assert is_allowed_signature(
            subject_type,
            relation,
            object_type,
        )


def test_invalid_signatures_are_rejected():
    invalid_signatures = [
        (
            EntityType.LOCATION,
            RelationType.HELD_IN,
            EntityType.FESTIVAL,
        ),
        (
            EntityType.FESTIVAL,
            RelationType.HELD_IN,
            EntityType.PROGRAM,
        ),
        (
            EntityType.FESTIVAL,
            RelationType.HAS_THEME,
            EntityType.AUDIENCE,
        ),
        (
            EntityType.PRODUCT,
            RelationType.ORGANIZES,
            EntityType.FESTIVAL,
        ),
    ]

    for subject_type, relation, object_type in invalid_signatures:
        assert not is_allowed_signature(
            subject_type,
            relation,
            object_type,
        )
