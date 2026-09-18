from src.ui.aura_service import resolve_connection_settings


def test_resolve_connection_settings_accepts_aura_names():
    settings = resolve_connection_settings(
        {"AURA_URI": "neo4j+s://example", "AURA_USER": "neo4j", "AURA_PASSWORD": "secret"},
        {},
    )
    assert settings == {
        "uri": "neo4j+s://example",
        "user": "neo4j",
        "password": "secret",
    }


def test_resolve_connection_settings_prefers_cloud_neo4j_names():
    settings = resolve_connection_settings(
        {"AURA_URI": "wrong", "AURA_USER": "aura", "AURA_PASSWORD": "wrong"},
        {"NEO4J_URI": "neo4j+s://cloud", "NEO4J_USER": "neo4j", "NEO4J_PASSWORD": "cloud-secret"},
    )
    assert settings["uri"] == "neo4j+s://cloud"
