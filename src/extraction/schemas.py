"""LLM Structured Output과 파이프라인 파일 사이의 공통 데이터 계약."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    """Ontology에서 허용하는 entity 종류."""

    FESTIVAL = "Festival"
    LOCATION = "Location"
    ORGANIZATION = "Organization"
    PROGRAM = "Program"
    THEME = "Theme"
    AUDIENCE = "Audience"
    ARTIST = "Artist"
    PRODUCT = "Product"


class RelationType(str, Enum):
    """Ontology에서 허용하는 relation 종류."""

    HELD_IN = "HELD_IN"
    ORGANIZES = "ORGANIZES"
    HAS_PROGRAM = "HAS_PROGRAM"
    HAS_THEME = "HAS_THEME"
    FEATURES = "FEATURES"
    TARGETS = "TARGETS"
    PROVIDES = "PROVIDES"


class Triple(BaseModel):
    """검증 전후에 공통으로 사용하는 Triple 계약."""

    model_config = ConfigDict(str_strip_whitespace=True)

    subject: str = Field(min_length=1)
    subject_type: EntityType

    relation: RelationType

    object: str = Field(min_length=1)
    object_type: EntityType

    source_doc_id: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class Extraction(BaseModel):
    """LLM Structured Output 응답 모델."""

    triples: list[Triple] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """한 문서의 추출 결과와 재현용 raw 응답을 담는다."""

    source_doc_id: str = Field(min_length=1)
    triples: list[Triple] = Field(default_factory=list)

    raw_response: str | None = None
    error: str | None = None