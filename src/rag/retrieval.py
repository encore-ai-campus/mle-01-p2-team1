"""Full-text Search와 Vector Search의 공통 Retriever 골격."""

from typing import Any, Sequence

DEFAULT_TOP_K = 5
VECTOR_CANDIDATE_MULTIPLIER = 4


# 입력: query, Neo4j driver, top_k
# 출력: name, entity_type, score, source를 갖는 동일 형식의 결과 목록
# TODO 1. Full-text index에 query를 보내고 score를 포함한 결과를 받는다.
# TODO 2. query embedding을 만든 뒤 Vector index를 조회한다.
# TODO 3. 두 검색 결과를 공통 schema로 변환한다.
# TODO 4. top_k 기본값과 tie 처리 규칙을 고정한다.


# TODO 5. Accommodation/Experience Node의 name, text, address를 검색 결과에 포함한다.
# TODO 6. 숙소/nearby 검색 결과에 distance_meters와 연결된 Festival 정보를 보존한다.


def _validate_top_k(top_k: int) -> int:
    """검색 결과 개수가 양의 정수인지 확인한다."""
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    return top_k


def _validate_query(query: str) -> str:
    """빈 검색어를 제거하고 검색어 형식을 확인한다."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    return query.strip()


def _first_text(value: Any) -> str | None:
    """Return the first non-empty provenance value as text."""
    if isinstance(value, (list, tuple)):
        value = next((item for item in value if item not in (None, "")), None)
    return None if value in (None, "") else str(value)


def fulltext_retrieve(
    query: str,
    driver,
    top_k: int = DEFAULT_TOP_K,
    index_name: str = "entity_ft",
) -> list[dict[str, Any]]:
    """Full-text index를 조회해 공통 Retriever 형식으로 반환한다.

    Args:
        query: 검색할 문자열.
        driver: Neo4j Driver 객체.
        top_k: 반환할 최대 결과 수.
        index_name: 사용할 Full-text index 이름.

    Returns:
        name, entity_type, score, source, text, address를 포함하는
        검색 결과 목록.
    """
    query = _validate_query(query)
    top_k = _validate_top_k(top_k)
    cypher = """
    CALL db.index.fulltext.queryNodes(
        $index_name,
        $search_query
    )
    YIELD node, score
    WITH node, score
        ORDER BY score DESC, coalesce(node.name, node.canonical_name, node.title) ASC, labels(node)[0] ASC
    LIMIT $top_k
    RETURN
        coalesce(node.name, node.canonical_name, node.title) AS name,
        labels(node)[0] AS entity_type,
        score,
        node.text AS text,
        node.address AS address
        ORDER BY score DESC, name ASC, entity_type ASC
    """

    with driver.session() as session:
        rows = session.run(
            cypher,
            index_name=index_name,
            search_query=query,
            top_k=top_k,
        )

        return normalize_results(rows, source="fulltext", top_k=top_k)


def vector_retrieve(
    query: str,
    driver,
    embedder,
    top_k: int = DEFAULT_TOP_K,
    index_name: str = "entity_vec",
    entity_type: str | None = None,
) -> list[dict[str, Any]]:
    """query를 임베딩한 뒤 Vector index를 조회해 공통 Retriever 형식으로 반환한다.

    Args:
        query: 검색할 문자열.
        driver: Neo4j Driver 객체.
        embedder: query embedding을 생성하는 객체.
        top_k: 반환할 최대 결과 수.
        index_name: 사용할 Vector index 이름.

    Returns:
        name, entity_type, score, source, text, address를 포함하는
        검색 결과 목록.
    """
    query = _validate_query(query)
    top_k = _validate_top_k(top_k)
    query_embedding = embedder.embed_query(query)
    if entity_type and index_name == "entity_vec":
        index_name = f"{entity_type.lower()}_vec"

    cypher = """
    CALL db.index.vector.queryNodes(
        $index_name,
        $candidate_k,
        $query_embedding
    )
    YIELD node, score
    WITH node, score
        ORDER BY score DESC, coalesce(node.name, node.canonical_name, node.title) ASC, labels(node)[0] ASC
    LIMIT $top_k
    OPTIONAL MATCH (node)-[relationship]-()
    WITH node, score,
         head([
             item IN collect({
                 source_doc_id: relationship.source_doc_id,
                 evidence: relationship.evidence
             })
             WHERE size(coalesce(item.source_doc_id, [])) > 0
               AND size(coalesce(item.evidence, [])) > 0
         ]) AS provenance
    RETURN
        coalesce(node.name, node.canonical_name, node.title) AS name,
        labels(node)[0] AS entity_type,
        score,
        node.text AS text,
        node.address AS address,
        head(provenance.source_doc_id) AS source_doc_id,
        head(provenance.evidence) AS evidence
    ORDER BY score DESC, name ASC, entity_type ASC
    """

    with driver.session() as session:
        rows = session.run(
            cypher,
            index_name=index_name,
            candidate_k=top_k * VECTOR_CANDIDATE_MULTIPLIER,
            top_k=top_k,
            query_embedding=query_embedding,
        )

        return normalize_results(rows, source="vector", top_k=top_k)


def hybrid_festival_retrieve(
    query: str,
    driver,
    embedder,
    location_hint: str | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """Vector 후보를 Festival-Location 관계로 검증해 반환한다."""
    candidates = vector_retrieve(
        query, driver, embedder, top_k=max(top_k * 10, 20), entity_type="Festival"
    )
    names = [row["name"] for row in candidates if row.get("name")]
    if not names:
        return []
    cypher = f"""
    MATCH (f:Festival)-[r:HELD_IN]->(l:Location)
    WHERE f.canonical_name IN $festival_names
      AND (
        {"l.canonical_name CONTAINS $location_hint OR any(e IN coalesce(r.evidence, []) WHERE e CONTAINS $location_hint)" if location_hint else "true"}
      )
    RETURN DISTINCT
        f.canonical_name AS festival,
        l.canonical_name AS location
    ORDER BY festival ASC
    LIMIT $top_k
    """
    with driver.session() as session:
        rows = session.run(
            cypher,
            festival_names=names,
            location_hint=location_hint,
            top_k=top_k,
        )
        return [{"festival": row["festival"], "location": row["location"]} for row in rows]


def normalize_results(
    rows: Sequence[Any],
    source: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """검색 결과를 공통 Retriever schema로 변환한다.

    Args:
        rows: Neo4j 검색 결과.
        source: 검색 방식. "fulltext", "vector", "nearby".
        top_k: 반환할 최대 결과 수.

    Returns:
        동일한 key 구조를 갖는 검색 결과 목록.
        nearby 검색에서는 festival이 연결된 Festival 객체 목록이다.
    """
    top_k = _validate_top_k(top_k)
    normalized = []
    for row in rows:
        score = row.get("score")
        normalized.append(
            {
                "name": row.get("name"),
                "entity_type": row.get("entity_type"),
                "score": float(score) if score is not None else 0.0,
                "source": source,
                "text": row.get("text"),
                "address": row.get("address"),
                "distance_meters": row.get("distance_meters"),
                "festival": row.get("festival"),
                "source_doc_id": _first_text(row.get("source_doc_id")),
                "evidence": _first_text(row.get("evidence")),
            }
        )
    return sort_results(normalized, top_k=top_k)


def sort_results(
    results: Sequence[dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """검색 결과를 고정된 tie 처리 규칙으로 정렬하고 top_k개를 반환한다.

    점수가 같으면 name 오름차순, 그다음 entity_type 오름차순으로 정렬한다.

    Args:
        results: 공통 Retriever schema의 검색 결과 목록.
        top_k: 반환할 최대 결과 수.

    Returns:
        고정된 tie 처리 규칙으로 정렬된 상위 검색 결과 목록.
    """
    top_k = _validate_top_k(top_k)
    sorted_results = sorted(
        results,
        key=lambda row: (
            -float(row.get("score", 0.0)),
            row.get("name") or "",
            row.get("entity_type") or "",
        ),
    )

    return sorted_results[:top_k]


def nearby_retrieve(
    query: str,
    driver,
    top_k: int = DEFAULT_TOP_K,
    index_name: str = "entity_ft",
) -> list[dict[str, Any]]:
    """숙소/nearby 검색 결과에 거리와 연결된 Festival 정보를 포함해 반환한다.

    Args:
        query: 검색할 문자열.
        driver: Neo4j Driver 객체.
        top_k: 반환할 최대 결과 수.
        index_name: 사용할 Full-text index 이름.

    Returns:
        검색 결과와 distance_meters, 연결된 Festival 정보를 포함한 목록.
    """
    query = _validate_query(query)
    top_k = _validate_top_k(top_k)
    cypher = """
    CALL db.index.fulltext.queryNodes(
        $index_name,
        $search_query
    )
    YIELD node, score
    WITH node, score
        ORDER BY score DESC, coalesce(node.name, node.canonical_name, node.title) ASC, labels(node)[0] ASC
    LIMIT $top_k

    OPTIONAL MATCH (festival:Festival)-[r:NEARBY]->(node)

    WITH node, score,
         collect(
             CASE
                 WHEN festival IS NULL THEN NULL
                 ELSE {
                     name: coalesce(festival.name, festival.canonical_name, festival.title),
                     source_doc_id: coalesce(festival.source_doc_id, festival.doc_id),
                     distance_meters: r.distance_meters
                 }
             END
         ) AS nearby
    WITH node, score, [item IN nearby WHERE item IS NOT NULL] AS nearby

    RETURN
        coalesce(node.name, node.canonical_name, node.title) AS name,
        labels(node)[0] AS entity_type,
        score,
        node.text AS text,
        node.address AS address,
        reduce(
            min_distance = NULL,
            item IN nearby |
            CASE
                WHEN item.distance_meters IS NULL THEN min_distance
                WHEN min_distance IS NULL OR item.distance_meters < min_distance
                    THEN item.distance_meters
                ELSE min_distance
            END
        ) AS distance_meters,
        nearby AS festival
    ORDER BY score DESC, name ASC, entity_type ASC
    """

    with driver.session() as session:
        rows = session.run(
            cypher,
            index_name=index_name,
            search_query=query,
            top_k=top_k,
        )

        return normalize_results(rows, source="nearby", top_k=top_k)

# 최소 예시: {"name": "유플페", "entity_type": "Festival", "score": 0.89, "source": "vector"}
# 완료 조건: 두 검색 방식이 같은 결과 계약과 top_k를 사용한다.
# Freeze point: 검색 결과 key와 score 의미는 QA 데이터 작성 전 고정한다.
