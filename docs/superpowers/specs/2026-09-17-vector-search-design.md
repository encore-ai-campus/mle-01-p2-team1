# Vector Search Integration Design

## Goal

Connect the existing embedding and retrieval modules to Streamlit so semantic festival and location queries can use Neo4j vector indexes.

## Design

Use typed Neo4j labels and one vector index per searchable type: `festival_vec`, `location_vec`, `accommodation_vec`, and `experience_vec`. Store 1536-dimensional `text-embedding-3-small` vectors on nodes. Streamlit will construct an `OpenAIEmbeddings` client, route semantic questions to vector retrieval, and keep Text2Cypher for graph conditions and aggregations. Location-oriented queries may use vector candidates before relationship traversal.

## Constraints

- Preserve existing Text2Cypher behavior and read-only validation.
- Do not recreate Neo4j data; index/embedding setup must be explicit and repeatable.
- Keep retrieval results compatible with `generate_answer()`.
- Add tests before implementation and run the full suite.
