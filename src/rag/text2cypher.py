"""자연어 질문을 읽기 전용 Cypher로 변환하는 골격."""

import logging
import re
from typing import Any

from src.extraction.ontology import RELATION_SIGNATURES


logger = logging.getLogger(__name__)

_WRITE_CLAUSE_PATTERN = re.compile(
    r"\b(?:ALTER|CALL|CREATE|DELETE|DENY|DROP|FOREACH|GRANT|INSERT|LOAD\s+CSV|"
    r"MERGE|REMOVE|RENAME|REVOKE|SET|START|STOP|TERMINATE)\b",
    re.IGNORECASE,
)

_ALLOWED_LABELS = frozenset({"Entity"})
_BASE_NODE_PROPERTIES = frozenset({"entity_type", "canonical_name"})
_EXTRA_NODE_PROPERTIES = frozenset(
    {
        "extra_id",
        "name",
        "address",
        "latitude",
        "longitude",
        "text",
        "source_file",
    }
)
_ALLOWED_NODE_PROPERTIES = _BASE_NODE_PROPERTIES | _EXTRA_NODE_PROPERTIES
_ONTOLOGY_RELATIONSHIP_PROPERTIES = frozenset({"source_doc_id", "evidence"})
_NEARBY_RELATIONSHIP_PROPERTIES = frozenset({"distance_meters", "source_file"})
_ALLOWED_RELATIONSHIP_PROPERTIES = (
    _ONTOLOGY_RELATIONSHIP_PROPERTIES | _NEARBY_RELATIONSHIP_PROPERTIES
)
_ALLOWED_PROPERTIES = _ALLOWED_NODE_PROPERTIES | _ALLOWED_RELATIONSHIP_PROPERTIES
_ALLOWED_ENTITY_TYPES = frozenset(
    str(getattr(entity_type, "value", entity_type))
    for signature in RELATION_SIGNATURES
    for entity_type in (signature[0], signature[2])
) | {"Accommodation", "Experience"}
_ALLOWED_RELATION_TYPES = frozenset(
    str(getattr(signature[1], "value", signature[1]))
    for signature in RELATION_SIGNATURES
) | {"NEARBY"}
_ALLOWED_SIGNATURES = frozenset(
    (
        str(getattr(subject_type, "value", subject_type)),
        str(getattr(relation, "value", relation)),
        str(getattr(object_type, "value", object_type)),
    )
    for subject_type, relation, object_type in RELATION_SIGNATURES
) | {
    ("Festival", "NEARBY", "Accommodation"),
    ("Festival", "NEARBY", "Experience"),
}

_IDENTIFIER = r"(?:`([^`]+)`|([A-Za-z_]\w*))"
_NODE_PATTERN = re.compile(r"\(([^()]*)\)")
_RELATIONSHIP_PATTERN = re.compile(r"\[([^\[\]]*)\]")
_LABEL_PATTERN = re.compile(rf":\s*{_IDENTIFIER}")
_MAP_KEY_PATTERN = re.compile(rf"(?:^|,)\s*{_IDENTIFIER}\s*:")
_VARIABLE_PATTERN = re.compile(rf"^\s*{_IDENTIFIER}")
_PROPERTY_ACCESS_PATTERN = re.compile(
    rf"\b{_IDENTIFIER}\s*\.\s*{_IDENTIFIER}"
)
_ENTITY_TYPE_PATTERN = re.compile(
    r"\bentity_type\b\s*(?::|=)\s*(['\"])(.*?)\1", re.IGNORECASE
)
_PATH_PATTERN = re.compile(
    r"(?P<left>\([^()]*\))\s*(?P<incoming><-)?-\s*"
    r"(?P<relationship>\[[^\[\]]*\])\s*-\s*(?P<outgoing>>)?\s*"
    r"(?P<right>\([^()]*\))"
)


def _identifier(match: re.Match[str], first_group: int = 1) -> str:
    return match.group(first_group) or match.group(first_group + 1)


def _mask_string_literals(cypher: str) -> str:
    """Mask quoted values while preserving positions used by regex checks."""
    chars = list(cypher)
    quote: str | None = None
    escaped = False

    for index, char in enumerate(cypher):
        if quote is None:
            if char in {"'", '"'}:
                quote = char
            continue

        if escaped:
            chars[index] = " "
            escaped = False
        elif char == "\\":
            chars[index] = " "
            escaped = True
        elif char == quote:
            quote = None
        else:
            chars[index] = " "

    if quote is not None:
        raise ValueError("Invalid Cypher syntax: unterminated string literal")
    return "".join(chars)


def _validate_syntax(cypher: str, masked_cypher: str) -> None:
    if not cypher.strip():
        raise ValueError("Invalid Cypher syntax: query is empty")
    if "```" in cypher or "//" in masked_cypher or "/*" in masked_cypher:
        raise ValueError("Invalid Cypher syntax: markup and comments are not allowed")

    statement = masked_cypher.strip()
    if statement.endswith(";"):
        statement = statement[:-1].rstrip()
    if ";" in statement:
        raise ValueError("Invalid Cypher syntax: multiple statements are not allowed")
    if not re.match(r"(?:OPTIONAL\s+MATCH|MATCH|UNWIND|WITH|RETURN)\b", statement, re.I):
        raise ValueError("Invalid Cypher syntax: query must start with a read clause")
    if not re.search(r"\bRETURN\b", statement, re.I):
        raise ValueError("Invalid Cypher syntax: query must contain RETURN")

    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for char in statement:
        if char in "([{":
            stack.append(char)
        elif char in pairs and (not stack or stack.pop() != pairs[char]):
            raise ValueError("Invalid Cypher syntax: unbalanced delimiters")
    if stack:
        raise ValueError("Invalid Cypher syntax: unbalanced delimiters")


def _validate_schema(cypher: str, masked_cypher: str) -> None:
    node_variable_types: dict[str, str | None] = {}
    relationship_variable_types: dict[str, set[str]] = {}

    for node_match in _NODE_PATTERN.finditer(masked_cypher):
        node = node_match.group(1)
        original_node = cypher[node_match.start(1) : node_match.end(1)]
        entity_type_match = _ENTITY_TYPE_PATTERN.search(original_node)
        entity_type = entity_type_match.group(2) if entity_type_match else None
        variable_match = _VARIABLE_PATTERN.match(node)
        if variable_match is not None:
            node_variable_types[_identifier(variable_match)] = entity_type
        labels = {_identifier(match) for match in _LABEL_PATTERN.finditer(node)}
        if not labels <= _ALLOWED_LABELS:
            raise ValueError("Node label is not allowed by the graph schema")

        map_start = node.find("{")
        if map_start >= 0:
            properties = {
                _identifier(match)
                for match in _MAP_KEY_PATTERN.finditer(node[map_start + 1 :])
            }
            allowed_properties = _BASE_NODE_PROPERTIES
            if entity_type in {"Accommodation", "Experience"}:
                allowed_properties |= _EXTRA_NODE_PROPERTIES
            if not properties <= allowed_properties:
                raise ValueError("Node property is not allowed by the graph schema")

    for relationship_match in _RELATIONSHIP_PATTERN.finditer(masked_cypher):
        relationship = relationship_match.group(1)
        variable_match = _VARIABLE_PATTERN.match(relationship)
        relationship_types = {
            _identifier(match)
            for match in _LABEL_PATTERN.finditer(relationship)
        }
        if variable_match is not None:
            relationship_variable_types[_identifier(variable_match)] = relationship_types
        if not relationship_types or not relationship_types <= _ALLOWED_RELATION_TYPES:
            raise ValueError("Relationship type is not allowed by the graph schema")

        map_start = relationship.find("{")
        if map_start >= 0:
            properties = {
                _identifier(match)
                for match in _MAP_KEY_PATTERN.finditer(relationship[map_start + 1 :])
            }
            allowed_properties = set()
            if relationship_types & {"NEARBY"}:
                allowed_properties.update(_NEARBY_RELATIONSHIP_PROPERTIES)
            if relationship_types - {"NEARBY"}:
                allowed_properties.update(_ONTOLOGY_RELATIONSHIP_PROPERTIES)
            if not properties <= allowed_properties:
                raise ValueError("Relationship property is not allowed by the graph schema")

    for match in _PROPERTY_ACCESS_PATTERN.finditer(masked_cypher):
        variable = _identifier(match)
        property_name = _identifier(match, 3)
        if variable in node_variable_types:
            allowed_properties = _BASE_NODE_PROPERTIES
            if node_variable_types[variable] in {"Accommodation", "Experience"}:
                allowed_properties |= _EXTRA_NODE_PROPERTIES
        elif variable in relationship_variable_types:
            relationship_types = relationship_variable_types[variable]
            allowed_properties = frozenset()
            if relationship_types & {"NEARBY"}:
                allowed_properties |= _NEARBY_RELATIONSHIP_PROPERTIES
            if relationship_types - {"NEARBY"}:
                allowed_properties |= _ONTOLOGY_RELATIONSHIP_PROPERTIES
        else:
            allowed_properties = _ALLOWED_PROPERTIES
        if property_name not in allowed_properties:
            raise ValueError("Property is not allowed by the graph schema")

    for match in _ENTITY_TYPE_PATTERN.finditer(cypher):
        if match.group(2) not in _ALLOWED_ENTITY_TYPES:
            raise ValueError("Entity type is not allowed by the graph schema")

    for path_match in _PATH_PATTERN.finditer(cypher):
        relationship_match = _LABEL_PATTERN.search(path_match.group("relationship"))
        left_type = _ENTITY_TYPE_PATTERN.search(path_match.group("left"))
        right_type = _ENTITY_TYPE_PATTERN.search(path_match.group("right"))
        if relationship_match is None or left_type is None or right_type is None:
            continue
        if bool(path_match.group("incoming")) == bool(path_match.group("outgoing")):
            raise ValueError("Relationship direction is not allowed by the graph schema")

        left = left_type.group(2)
        right = right_type.group(2)
        relation = _identifier(relationship_match)
        signature = (left, relation, right)
        if path_match.group("incoming"):
            signature = (right, relation, left)
        if signature not in _ALLOWED_SIGNATURES:
            raise ValueError("Relationship signature is not allowed by the graph schema")


# 입력: question, 고정 Graph schema, LLM
# 출력: read-only Cypher와 실행 결과 또는 오류 로그
TEXT2CYPHER_PROMPT = """당신은 자연어 질문을 Neo4j 읽기 전용 Cypher로 변환하는 도우미입니다.
아래 Graph schema를 유일한 사실의 원천으로 사용하세요.

[Graph schema]
{schema}

[규칙]
- Entity 라벨만 사용하세요. 스키마에 없는 label이나 relation을 만들거나 사용하지 마세요.
- 위 schema에 명시된 relation 타입과 방향만 사용하세요.
- entity_type, canonical_name처럼 schema에 명시된 속성만 사용하세요.
- CREATE, MERGE, DELETE, SET, REMOVE, DROP, LOAD CSV 등 데이터를 변경하거나 외부 데이터를
  읽는 구문은 사용하지 마세요. MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, ORDER BY,
  SKIP, LIMIT, UNWIND, 집계 등 읽기 구문만 사용하세요.
- 질문에 답할 수 없으면 임의의 label/relation을 추측하지 말고 결과가 없도록 작성하세요.
- 설명, 마크다운 코드 펜스, 주석 없이 실행할 Cypher 문장만 출력하세요.

[질문]
{question}
"""


def build_text2cypher_prompt(question: str) -> str:
    """고정 Graph schema와 자연어 질문을 Text2Cypher 프롬프트로 결합한다."""
    return TEXT2CYPHER_PROMPT.format(
        schema=build_graph_schema_block(),
        question=question,
    )


def build_graph_schema_block() -> str:
    """Ontology와 일치하는 Graph schema 설명을 만든다."""
    # Neo4j stores every graph node under the stable Entity label.  The
    # ontology type and canonical name remain queryable node properties.
    lines = [
        "Graph schema:",
        "Node label: Entity",
        "Nodes:",
        "- (:Entity {entity_type: <EntityType>, canonical_name: <string>})",
        "Node properties:",
        "- entity_type: EntityType",
        "- canonical_name: string",
        "- extra_id: string (Accommodation, Experience)",
        "- name: string (Accommodation, Experience)",
        "- address: string (Accommodation, Experience)",
        "- latitude: number (Accommodation, Experience)",
        "- longitude: number (Accommodation, Experience)",
        "- text: string (Accommodation, Experience)",
        "- source_file: string (Accommodation, Experience)",
        "Relationship properties:",
        "- source_doc_id: list[string] (ontology relationships)",
        "- evidence: list[string] (ontology relationships)",
        "- distance_meters: number (NEARBY)",
        "- source_file: string (NEARBY)",
        "Relationships (directed):",
    ]

    signatures = [
        (
            getattr(subject_type, "value", subject_type),
            getattr(relation, "value", relation),
            getattr(object_type, "value", object_type),
        )
        for subject_type, relation, object_type in RELATION_SIGNATURES
    ]
    signatures.extend(
        [
            ("Festival", "NEARBY", "Accommodation"),
            ("Festival", "NEARBY", "Experience"),
        ]
    )
    for subject_type, relation, object_type in signatures:
        lines.append(
            f"- (:Entity {{entity_type: '{subject_type}'}})"
            f"-[:{relation}]->"
            f"(:Entity {{entity_type: '{object_type}'}})"
        )

    return "\n".join(lines)


def generate_cypher(question: str, llm: Any) -> str:
    """자연어 질문에서 읽기 전용 Cypher를 생성한다."""
    response = llm.invoke(build_text2cypher_prompt(question))
    cypher = getattr(response, "content", response)
    if not isinstance(cypher, str):
        raise TypeError("LLM response content must be a string")
    return cypher.strip()


def validate_read_only_cypher(cypher: str) -> None:
    """쓰기·삭제 query와 허용되지 않은 구문을 차단한다."""
    masked_cypher = _mask_string_literals(cypher)
    if _WRITE_CLAUSE_PATTERN.search(masked_cypher):
        raise ValueError("Write operations are not allowed in read-only Cypher")
    _validate_syntax(cypher, masked_cypher)
    _validate_schema(cypher, masked_cypher)


def execute_text2cypher(driver: Any, question: str, llm: Any) -> list[dict[str, Any]]:
    """Cypher 생성·검사·실행을 연결한다."""
    cypher: str | None = None
    try:
        cypher = generate_cypher(question, llm)
        validate_read_only_cypher(cypher)
        with driver.session() as session:
            result = [
                record.data() if hasattr(record, "data") else dict(record)
                for record in session.run(cypher)
            ]
    except Exception as error:
        logger.exception(
            "Text2Cypher execution failed",
            extra={
                "question": question,
                "cypher": cypher,
                "error": str(error),
            },
        )
        raise

    logger.info(
        "Text2Cypher execution succeeded",
        extra={"question": question, "cypher": cypher, "error": None},
    )
    return result


# 완료 조건: 임의 쓰기 query가 실행되지 않고, 허용 schema 범위의 질문 결과만 반환된다.
# Freeze point: Text2Cypher에 제공하는 schema는 Graph 적재 구조와 함께 고정한다.