"""LLM Structured Output과 파이프라인 파일 사이의 공통 데이터 계약."""

from enum import Enum
from pydantic import BaseModel, Field

# [교안 대응 TODO]
# TODO A. 교안의 Extraction(BaseModel)을 추가하거나 ExtractionResult를 단건 응답 모델로 사용한다.
# triples: list[Triple] 필드를 갖게 하고, LLM Structured Output의 응답 모델로 연결한다.
# TODO B. model_dump() 결과가 현재 raw 저장 형식과 일치하는지 테스트한다.


class EntityType(str, Enum):
    """Ontology에서 허용하는 entity 종류."""
    FESTIVAL = "Festival"
    LOCATION = "Location"
    ACTIVITY = "Activity"
    THEME = "Theme"
    PERIOD = "Period"
    AUDIENCE = "Audience"


class RelationType(str, Enum):
    """Ontology에서 허용하는 relation 종류."""
    HELD_IN = "HELD_IN"
    HAS_ACTIVITY = "HAS_ACTIVITY"
    HAS_THEME = "HAS_THEME"
    HELD_DURING = "HELD_DURING"
    TARGETS = "TARGETS"


class Triple(BaseModel):
    """검증 전후에 공통으로 사용하는 Triple 계약."""
    subject: str
    subject_type: EntityType
    relation: RelationType
    object: str
    object_type: EntityType
    source_doc_id: str
    evidence: str


class ExtractionResult(BaseModel):
    """한 문서의 추출 결과와 재현용 raw 응답을 담는다."""
    source_doc_id: str
    triples: list[Triple] = Field(default_factory=list)
    raw_response: str | None = None
    error: str | None = None


# TODO 1. 교안의 Extraction 모델을 작성한다.
#
# Extraction은 LLM이 반환하는 Structured Output의 최소 껍데기다.
# source_doc_id, raw_response, error는 extract.py의 ExtractionResult가 담당하므로
# 이 모델에는 교안처럼 triples 필드만 둔다.
# 구현 순서:
# 1. triples 필드를 list[Triple] 타입으로 선언한다.
# 2. 기본값을 빈 리스트로 둘지 필수 입력으로 둘지 팀에서 결정한다.
# 3. extract.py에서 with_structured_output(Extraction)에 전달한다.
class Extraction(BaseModel):
    """교안의 단건 LLM Structured Output 응답 모델."""

    triples: list[Triple] = Field(default_factory=list)


# TODO 2: 위 필드가 필수이고 빈 subject/object/evidence를 허용하지 않도록 제약을 정한다.
# 입력 예: subject가 "", evidence가 공백뿐인 JSON을 준비한다.
# 기대 결과: ValidationError가 발생하고 어느 필드가 잘못되었는지 확인 가능해야 한다.
# TODO 3: LLM JSON 예시를 넣어 성공/실패 Pydantic 파싱 테스트를 작성한다.
# 성공 예시는 source_doc_id까지 포함한 Triple 1건, 실패 예시는 잘못된 enum과 누락 필드로 만든다.
# TODO 4: 파싱 실패 시 raw_response와 문서 ID가 보존되는지 확인한다.
# TODO 5: ExtractionResult가 빈 triples를 정상적인 “추출된 Triple 없음”으로 구분하는지 결정한다.
# 오류가 발생한 결과는 error 문자열과 raw_response를 함께 보존해야 한다.
# Freeze point: 필드명과 enum 값은 모든 팀원이 동의하기 전까지 변경 금지.
