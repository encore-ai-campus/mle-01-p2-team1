"""모든 문서에 공통 적용하는 추출 Prompt 생성 규칙."""

from src.extraction.ontology import RELATION_SIGNATURES
from langchain_core.prompts import ChatPromptTemplate



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
    lines = ["[허용 Entity-Relation-Entity Signature]"]

    for (subject_type, relation, object_type), criterion in signatures.items():
        lines.append(
            f"- subject_type={subject_type.value}, "
            f"relation={relation.value}, "
            f"object_type={object_type.value}: "
            f"{criterion}"
        )

    return "\n".join(lines)

# TODO 2. build_extraction_prompt(source_doc_id, text) -> ChatPromptTemplate를 구현한다.
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
def build_extraction_prompt(source_doc_id: str, text: str) -> ChatPromptTemplate:
    """문서 1건을 LLM에 전달할 최종 Prompt를 생성한다."""
    ontology = build_ontology_block(RELATION_SIGNATURES)

    system_prompt = (
        "너는 문서에서 지식 그래프 트리플을 추출하는 도구다.\n\n"
        f"{ontology}\n\n"
        "[규칙]\n"
        "- Triple의 subject_type, relation, object_type 조합은 위 Signature 중 하나와 정확히 일치해야 한다.\n"
        "- subject와 object는 문장에 등장한 순서가 아니라 Signature에 표시된 방향으로 배치한다.\n"
        "- Signature에 없는 조합은 추출하지 않는다.\n"
        "- 주어와 목적어에는 원문에 명시된 개체 이름만 적는다.\n"
        "- 개체명은 원문 표기를 그대로 유지한다.\n"
        "- evidence는 관계를 뒷받침하는 원문의 연속된 구간을 그대로 복사한다.\n"
        "- evidence를 요약·생략·수정하거나 문장부호를 추가하지 않는다.\n"
        '- evidence에 "...", "…", "[중략]"을 사용하지 않는다.\n'
        "- evidence는 반드시 원문 text의 부분 문자열이어야 한다.\n"
        "- 근거가 없는 관계는 추출하지 않는다.\n"
        "- source_doc_id는 entity가 아니라 문서 식별자이며, [문서 ID] 값을 각 Triple에 그대로 넣는다.\n"
        "- 적절한 EntityType이 없으면 억지로 분류하지 않고 추출하지 않는다.\n"
        "- 지명이 언급되었다는 이유만으로 HELD_IN을 추출하지 않는다. 개최 장소나 위치 관계가 명시된 경우에만 추출한다.\n"
        "- 프로그램이 목록으로 나열된 경우 각 프로그램 항목을 빠짐없이 개별 Triple로 추출한다.\n"
        "- 본문 설명과 프로그램 목록을 모두 확인하여 추출 가능한 관계를 일부만 선택하지 말고 모두 추출한다.\n"
            "- 원문에서 근거가 확인되는 추출 가능한 관계를 일부만 선택하지 말고 모두 추출한다.\n"
            "- 다른 Festival/Program의 설명이나 상위 개체의 속성을 현재 개체의 관계로 확장하거나 추론하지 않는다.\n"
            "- 하나의 문장에 여러 행사, 프로그램, 장소, 출연자 또는 대상이 함께 등장하면 원문에서 직접 연결된 개체 쌍에 대해서만 Triple을 추출한다.\n"
    )

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "[문서 ID]\n{source_doc_id}\n\n"
        "[문서]\n{text}",),
    ])




# 완료 조건: 같은 입력은 같은 문자열을 만들고, 허용 enum/금지 추론/evidence 규칙을 모두 포함한다.
# 확인 방법: Prompt 문자열에 6개 EntityType, 5개 RelationType, 7개 Triple 필드명이 포함되는지 테스트한다.
# Freeze point: Prompt와 Schema는 샘플 10~20건 검토 전까지 함께 교차 검토한다.
