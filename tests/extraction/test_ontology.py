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
        EntityType.ACTIVITY,
        EntityType.THEME,
        EntityType.PERIOD,
        EntityType.AUDIENCE,
    )


def test_allowed_relation_types_are_derived_from_relation_signatures():
    assert ALLOWED_RELATION_TYPES == tuple(RELATION_SIGNATURES)


def test_all_declared_signatures_are_allowed():
    for relation, (
        subject_type,
        object_type,
        _,
    ) in RELATION_SIGNATURES.items():
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
            EntityType.ACTIVITY,
        ),
        (
            EntityType.ACTIVITY,
            RelationType.HAS_ACTIVITY,
            EntityType.FESTIVAL,
        ),
        (
            EntityType.FESTIVAL,
            RelationType.HAS_THEME,
            EntityType.AUDIENCE,
        ),
        (
            EntityType.PERIOD,
            RelationType.HELD_DURING,
            EntityType.FESTIVAL,
        ),
    ]

    for subject_type, relation, object_type in invalid_signatures:
        assert not is_allowed_signature(
            subject_type,
            relation,
            object_type,
        )
