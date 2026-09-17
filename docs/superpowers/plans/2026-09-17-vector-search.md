# Vector Search Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect Neo4j vector indexes and existing retrieval code to Streamlit for semantic festival and location search.

**Architecture:** Store `text-embedding-3-small` vectors on typed-label nodes and query per-type Neo4j vector indexes. Add an embedding/index setup entry point, expose vector and full-text services in Streamlit, and route semantic questions through them while preserving Text2Cypher for graph questions.

**Tech Stack:** Python 3.12, Neo4j Python driver, LangChain OpenAI embeddings, Streamlit, pytest.

**Spec:** `docs/superpowers/specs/2026-09-17-vector-search-design.md`

## Global Constraints

- Vector dimensions: 1536.
- Embedding model: `text-embedding-3-small`.
- Index names: `festival_vec`, `location_vec`, `accommodation_vec`, `experience_vec`.
- Existing Text2Cypher read-only validation must remain intact.

### Task 1: Type-aware vector index helpers

**Files:** Modify `src/graph/build_indexes.py`; Test `tests/graph/test_build_indexes.py`.

- [ ] Add failing tests for creating four typed indexes and reporting their readiness.
- [ ] Implement a typed index configuration constant and helper that creates each index using the existing vector property and dimensions.
- [ ] Run `PYTHONPATH=. ./.venv/bin/pytest tests/graph/test_build_indexes.py -q`.

### Task 2: Type-aware vector retrieval

**Files:** Modify `src/rag/retrieval.py`; Test `tests/rag/test_retrieval.py`.

- [ ] Add failing tests proving a requested entity type selects its matching index and returns normalized rows.
- [ ] Extend `vector_retrieve()` with an optional `entity_type` argument while preserving the existing `index_name` override.
- [ ] Run the retrieval tests and then the full suite.

### Task 3: Streamlit service wiring

**Files:** Modify `src/ui/app.py`; Test `tests/ui/test_app_services.py` if service construction is extracted.

- [ ] Add a failing test for service registration and route dispatch.
- [ ] Create the embedding client, typed vector service, and full-text service; dispatch through `route_question()`.
- [ ] Keep the existing generated Cypher and result display for Text2Cypher and add result display for vector/full-text paths.
- [ ] Run the full test suite and manually verify the Streamlit page.

### Task 4: Operational setup documentation

**Files:** Modify `README.md`; Create `scripts/build_vector_indexes.py`.

- [ ] Document the one-time embedding/index setup command and required environment variables.
- [ ] Make the setup script load `neo4j_data.json`, write embeddings, and create typed indexes without deleting nodes.
- [ ] Run a dry structural test and document expected Neo4j index names.

