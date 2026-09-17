"""Neo4j Full-text/Vector 검색을 위한 index 생성 골격."""

import re
from typing import Any, Final, Sequence, TypedDict

from src.extraction.schemas import EntityType


class EntitySearchConfig(TypedDict):
    """EntityType별 검색 설정."""

    properties: tuple[str, ...]
    index_name: str


EMBEDDING_MODEL: Final[str] = "text-embedding-3-small"
EMBEDDING_DIMENSIONS: Final[int] = 1536
VECTOR_SIMILARITY_FUNCTION: Final[str] = "cosine"


# 입력: Neo4j driver, Node text 구성 규칙, embedding model
# 출력: Full-text index, Vector index, index_report.json

# TODO 1. EntityType별 검색 대상 property와 index 이름을 결정한다.

ENTITY_SEARCH_CONFIG: Final[dict[EntityType | str, EntitySearchConfig]] = {
    EntityType.FESTIVAL: {"properties": ("canonical_name", "description", "overview"), "index_name": "festival_fulltext"},
    EntityType.PROGRAM: {"properties": ("canonical_name", "description"), "index_name": "program_fulltext"},
    EntityType.THEME: {"properties": ("canonical_name",), "index_name": "theme_fulltext"},
    EntityType.LOCATION: {"properties": ("canonical_name",), "index_name": "location_fulltext"},
    EntityType.ORGANIZATION: {"properties": ("canonical_name",), "index_name": "organization_fulltext"},
    EntityType.AUDIENCE: {"properties": ("canonical_name",), "index_name": "audience_fulltext"},
    EntityType.ARTIST: {"properties": ("canonical_name",), "index_name": "artist_fulltext"},
    EntityType.PRODUCT: {"properties": ("canonical_name",), "index_name": "product_fulltext"},
    "Accommodation": {"properties": ("name", "text", "address"), "index_name": "accommodation_fulltext"},
}

# TODO 2. Festival description/overview, Program name+description, Theme name의 임베딩 text를 만든다.

def build_embedding_text(
    entity_type: EntityType | str,
    node: dict[str, Any],
) -> str:
    """EntityType에 따라 임베딩용 text를 만든다."""

    if entity_type == EntityType.FESTIVAL:
        parts = [
            node.get("description"),
            node.get("overview"),
        ]

    elif entity_type == EntityType.PROGRAM:
        parts = [
            node.get("name"),
            node.get("description"),
        ]

    elif entity_type == EntityType.THEME:
        parts = [
            node.get("name"),
        ]
    elif entity_type == "Accommodation":
        parts = [
            node.get("name"),
            node.get("text"),
            node.get("address"),
        ]
    else:
        parts = []

    # None이나 빈 문자열을 제외하고 하나의 문자열로 합침
    text = " ".join(
        value
        for part in parts
        if part is not None and (value := str(part).strip())
    )
    return text or str(node.get("canonical_name") or node.get("name") or "").strip()


# TODO 3. 임베딩 모델과 차원·거리(metric)를 고정하고 Node에 vector property를 저장한다.

def store_node_embeddings(
    driver: Any,
    nodes: Sequence[dict[str, Any]],
    embedding_model: Any | None = None,
    batch_size: int = 500,
) -> int:
    """고정된 임베딩 설정으로 Entity Node에 vector property를 저장한다."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    if embedding_model is None:
        from langchain_openai import OpenAIEmbeddings

        embedding_model = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        )

    rows = []
    for node in nodes:
        entity_type = node.get("entity_type")
        try:
            entity_type = EntityType(entity_type)
        except (TypeError, ValueError):
            entity_type = entity_type if entity_type == "Accommodation" else None
        text = build_embedding_text(entity_type, node) if entity_type else ""
        if text:
            rows.append({
                "entity_type": node["entity_type"],
                "canonical_name": node["canonical_name"],
                "text": text,
            })

    written = 0
    query = """
    UNWIND $rows AS item
    MATCH (n:$(item.entity_type) {canonical_name: item.canonical_name})
    SET n.vector = item.vector
    """
    with driver.session() as session:
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            vectors = embedding_model.embed_documents([item["text"] for item in batch])
            if len(vectors) != len(batch):
                raise ValueError(
                    f"embedding count must be {len(batch)}, got {len(vectors)}"
                )
            if any(len(vector) != EMBEDDING_DIMENSIONS for vector in vectors):
                raise ValueError(f"embedding dimension must be {EMBEDDING_DIMENSIONS}")
            session.run(query, rows=[{**item, "vector": vector} for item, vector in zip(batch, vectors)]).consume()
            written += len(batch)
    return written


# TODO 4. Neo4j vector index와 Full-text index를 생성한다.

# TODO 5. index 상태가 ONLINE인지 확인하고 차원·대상 label을 report에 저장한다.

def build_index_report(driver: Any) -> dict[str, Any]:
    """Neo4j 인덱스의 상태와 vector 설정을 report로 반환한다."""
    query = """
    SHOW INDEXES
    YIELD name, type, state, labelsOrTypes, properties, options
    RETURN name, type, state, labelsOrTypes, properties, options
    """
    with driver.session() as session:
        rows = session.run(query).data()

    indexes = []
    for row in rows:
        state = row.get("state")
        if state != "ONLINE":
            raise RuntimeError(
                f"index {row.get('name')!r} is not ONLINE: {state!r}"
            )

        options = row.get("options") or {}
        index_config = options.get("indexConfig") or {}
        indexes.append({
            "name": row.get("name"),
            "type": row.get("type"),
            "state": state,
            "dimensions": index_config.get("vector.dimensions"),
            "labels": row.get("labelsOrTypes") or row.get("labels") or [],
        })
    return {"indexes": indexes}


# TODO 6. Accommodation의 name, text, address를 Full-text 검색 대상에 포함한다.

# TODO 7. Festival/Accommodation metadata를 검색·embedding용 text로 매핑한다.

def build_search_text(node: dict[str, Any]) -> str:
    """Node에서 검색과 임베딩에 사용할 text를 만든다."""
    entity_type = node.get("entity_type")
    config = ENTITY_SEARCH_CONFIG.get(entity_type)
    if config is None:
        return ""

    return " ".join(
        value
        for property_name in config["properties"]
        if (raw_value := node.get(property_name)) is not None
        and (value := str(raw_value).strip())
    )


def create_fulltext_index(driver: Any, index_name: str, labels: Sequence[str], properties: Sequence[str]) -> None:
    """Full-text index를 생성한다."""
    if not labels or not properties:
        raise ValueError("labels and properties must not be empty")

    identifiers = (index_name, *labels, *properties)
    if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value) for value in identifiers):
        raise ValueError("index names, labels, and properties must be valid identifiers")

    label_expression = "|".join(labels)
    property_expression = ", ".join(f"n.{property_name}" for property_name in properties)
    query = f"""
    CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
    FOR (n:{label_expression}) ON EACH [{property_expression}]
    """
    with driver.session() as session:
        session.run(query).consume()


def create_vector_index(driver: Any, index_name: str, dimensions: int, similarity_function: str = "cosine", label: str = "Entity") -> None:
    """Vector index를 생성한다."""
    if dimensions < 1:
        raise ValueError("dimensions must be positive")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", index_name):
        raise ValueError("index_name must be a valid identifier")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", label):
        raise ValueError("label must be a valid identifier")
    if similarity_function not in {"cosine", "euclidean"}:
        raise ValueError("unsupported vector similarity function")

    query = f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (n:{label}) ON (n.vector)
    OPTIONS {{indexConfig: {{
        `vector.dimensions`: {dimensions},
        `vector.similarity_function`: '{similarity_function}'
    }}}}
    """
    with driver.session() as session:
        session.run(query).consume()


# 완료 조건: Full-text와 Vector 검색이 각각 한 건 이상 반환되고 index 상태가 ONLINE이다.
# Freeze point: embedding model, vector dimension, index 이름은 승인 없이 변경하지 않는다.
