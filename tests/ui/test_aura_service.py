from src.ui.aura_service import resolve_connection_settings, choose_festival_name
from src.ui.chat_graph_page import build_graph_figure_data, filter_experience_edges


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


def test_build_graph_figure_data_deduplicates_nodes_and_keeps_edges():
    rows = [{"subject": "축제", "subject_type": "Festival", "relation": "HAS_THEME", "object": "음악", "object_type": "Theme"}]
    nodes, edges = build_graph_figure_data(rows)
    assert len(nodes) == 2
    assert edges == [("축제", "음악", "HAS_THEME")]


def test_choose_festival_name_returns_selected_option():
    assert choose_festival_name(["축제 A", "축제 B"], "축제 B") == "축제 B"


def test_filter_experience_edges_hides_experience_by_default():
    rows = [
        {"subject_type": "Festival", "object_type": "Experience"},
        {"subject_type": "Festival", "object_type": "Program"},
    ]
    assert len(filter_experience_edges(rows, show_experience=False)) == 1
