"""Optional Neo4j Aura access for the Streamlit UI."""
from __future__ import annotations

import os
from typing import Any


def resolve_connection_settings(secrets: Any = None, environ: dict[str, str] | None = None) -> dict[str, str]:
    """Resolve Cloud ``NEO4J_*`` first, then local ``AURA_*`` settings."""
    values = environ if environ is not None else os.environ
    secrets = secrets or {}

    def value(*names: str) -> str:
        for name in names:
            candidate = values.get(name) or (secrets.get(name) if hasattr(secrets, "get") else None)
            if candidate:
                return str(candidate)
        return ""

    return {
        "uri": value("NEO4J_URI", "AURA_URI"),
        "user": value("NEO4J_USER", "AURA_USER"),
        "password": value("NEO4J_PASSWORD", "AURA_PASSWORD"),
    }


def connect_aura(secrets: Any = None):
    """Return a verified driver, or ``None`` when Aura is unavailable."""
    settings = resolve_connection_settings(secrets)
    if not all(settings.values()):
        return None
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings["uri"], auth=(settings["user"], settings["password"])
        )
        driver.verify_connectivity()
        return driver
    except Exception:
        return None


def fetch_graph_edges(driver: Any, limit: int = 30, query: str = "") -> list[dict[str, Any]]:
    """Fetch evidence-bearing graph edges from Aura for the graph page."""
    if driver is None:
        return []
    limit = max(5, min(int(limit), 200))
    cypher = """
    MATCH (s)-[r]->(o)
    WHERE ($search_query = '' OR toLower(coalesce(s.canonical_name, s.name, '')) CONTAINS toLower($search_query)
       OR toLower(coalesce(o.canonical_name, o.name, '')) CONTAINS toLower($search_query)
       OR toLower(type(r)) CONTAINS toLower($search_query))
    RETURN coalesce(s.canonical_name, s.name, s.title) AS subject,
           s.entity_type AS subject_type,
           type(r) AS relation,
           coalesce(o.canonical_name, o.name, o.title) AS object,
           o.entity_type AS object_type,
           r.source_doc_id AS source_doc_id,
           r.evidence AS evidence
    ORDER BY subject, relation, object
    LIMIT $limit
    """
    try:
        with driver.session() as session:
            return [record.data() for record in session.run(cypher, search_query=query.strip(), limit=limit)]
    except Exception:
        return []


def retrieve_aura_festivals(driver: Any, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Run Aura full-text search for festival answers with visible evidence."""
    if driver is None or not query.strip():
        return []
    cypher = """
    CALL db.index.fulltext.queryNodes('festival_fulltext', $query)
    YIELD node, score
    RETURN node.canonical_name AS name, node.entity_type AS entity_type,
           score, node.overview AS text, node.source_doc_ids AS source_doc_id
    ORDER BY score DESC, name ASC
    LIMIT $top_k
    """
    try:
        with driver.session() as session:
            rows = [record.data() for record in session.run(cypher, query=query.strip(), top_k=top_k)]
        return [{**row, "source": "aura_fulltext"} for row in rows]
    except Exception:
        return []
