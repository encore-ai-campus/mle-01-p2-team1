"""모든 문서에 공통 적용하는 추출 Prompt 생성 규칙."""

from src.extraction.schemas import EntityType, RelationType

SYSTEM_INSTRUCTIONS = """TODO: 역할, 출력 형식, 허용 enum, 근거 보존 원칙을 작성한다."""
EXTRACTION_RULES = """TODO: 원문에 명시된 정보만 추출하고 추론/보완하지 않는 규칙을 작성한다."""


# TODO 1. build_ontology_block(signatures) -> str를 교안대로 구현한다.
#
# 권장 처리 순서
# 1. lines = ["[허용 관계]"]로 시작한다.
# 2. signatures.items()를 순회하며 relation, subject_type, object_type, criterion을 꺼낸다.
# 3. "- RELATION: (SubjectType) -> (ObjectType) # criterion" 형식으로 append한다.
# 4. "\n".join(lines)를 반환한다.
#
# 입력은 ontology.py의 RELATION_SIGNATURES를 사용한다.
# 이 함수는 Prompt를 호출하지 않고 Ontology 설명 문자열만 만든다.
def build_ontology_block(signatures: dict) -> str:
    """교안의 RELATION_SIGNATURES를 Prompt용 텍스트로 변환한다."""
    raise NotImplementedError


# TODO 2. build_extraction_prompt(source_doc_id, text) -> str를 구현한다.
#
# 권장 구성 순서
# 1. 시스템 역할과 작업 목적을 넣는다.
# 2. 허용 EntityType, RelationType, signature 규칙을 넣는다.
# 3. Triple 필드 7개와 각 필드의 의미를 설명한다.
# 4. evidence는 원문에서 그대로 복사한다는 규칙을 넣는다.
# 5. source_doc_id와 원문 text를 구분된 영역으로 넣는다.
#
# 원문에 없는 날짜·장소·대상을 상식으로 보완하지 않는다.
# 근거가 없거나 애매하면 Triple을 만들지 않고 빈 배열을 반환하도록 지시한다.
# source_doc_id를 entity 이름으로 오인하지 않도록 긴 ID와 간단한 문서 예시로 테스트한다.
def build_extraction_prompt(source_doc_id: str, text: str) -> str:
    """문서 1건을 LLM에 전달할 최종 Prompt를 생성한다."""
    raise NotImplementedError


# 완료 조건: 같은 입력은 같은 문자열을 만들고, 허용 enum/금지 추론/evidence 규칙을 모두 포함한다.
# 확인 방법: Prompt 문자열에 6개 EntityType, 5개 RelationType, 7개 Triple 필드명이 포함되는지 테스트한다.
# Freeze point: Prompt와 Schema는 샘플 10~20건 검토 전까지 함께 교차 검토한다.
