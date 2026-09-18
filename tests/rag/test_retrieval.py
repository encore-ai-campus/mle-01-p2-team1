from src.rag.retrieval import normalize_results, vector_retrieve


class _FakeEmbedder:
    def embed_query(self, query):
        assert query == "festival question"
        return [0.1, 0.2]


class _FakeSession:
    def __init__(self, rows, calls):
        self._rows = rows
        self._calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def run(self, query, **parameters):
        self._calls.append((query, parameters))
        return self._rows


class _FakeDriver:
    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    def session(self):
        return _FakeSession(self._rows, self.calls)


def test_normalize_results_preserves_first_provenance_value():
    rows = [
        {
            "name": "Festival A",
            "entity_type": "Festival",
            "score": 0.9,
            "source_doc_id": ["doc-1", "doc-2"],
            "evidence": ["first evidence", "second evidence"],
        }
    ]

    result = normalize_results(rows, source="vector")

    assert result[0]["source_doc_id"] == "doc-1"
    assert result[0]["evidence"] == "first evidence"


def test_vector_retrieve_requests_and_returns_relationship_provenance():
    driver = _FakeDriver(
        [
            {
                "name": "Festival A",
                "entity_type": "Festival",
                "score": 0.9,
                "source_doc_id": "doc-1",
                "evidence": "festival evidence",
            }
        ]
    )

    result = vector_retrieve(
        "festival question",
        driver,
        _FakeEmbedder(),
        top_k=1,
        entity_type="Festival",
    )

    query, parameters = driver.calls[0]
    assert "relationship.source_doc_id" in query
    assert "relationship.evidence" in query
    assert parameters["index_name"] == "festival_vec"
    assert result[0]["source_doc_id"] == "doc-1"
    assert result[0]["evidence"] == "festival evidence"
