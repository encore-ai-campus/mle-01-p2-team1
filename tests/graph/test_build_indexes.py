from src.graph.build_indexes import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    VECTOR_SIMILARITY_FUNCTION,
    ENTITY_SEARCH_CONFIG,
    store_node_embeddings,
)


class FakeEmbeddingModel:
    def embed_documents(self, texts):
        return [[float(len(texts))] * EMBEDDING_DIMENSIONS for text in texts]


class FakeSession:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def run(self, query, **params):
        self.calls.append((query, params))

        class Result:
            def consume(self):
                return None

        return Result()


class FakeDriver:
    def __init__(self):
        self.session_obj = FakeSession()

    def session(self):
        return self.session_obj



def test_store_node_embeddings_uses_fixed_model_contract_and_vector_property():
    driver = FakeDriver()
    nodes = [{"entity_type": "Festival", "canonical_name": "A", "name": "A", "description": "desc"}]

    written = store_node_embeddings(driver, nodes, FakeEmbeddingModel())

    assert written == 1
    assert (EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, VECTOR_SIMILARITY_FUNCTION) == (
        "text-embedding-3-small",
        1536,
        "cosine",
    )
    rows = driver.session_obj.calls[0][1]["rows"]
    assert len(rows[0]["vector"]) == EMBEDDING_DIMENSIONS


def test_accommodation_fulltext_config_includes_name_text_and_address():
    assert ENTITY_SEARCH_CONFIG["Accommodation"] == {
        "properties": ("name", "text", "address"),
        "index_name": "accommodation_fulltext",
    }
