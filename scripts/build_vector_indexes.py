"""neo4j_data.json의 노드에 임베딩을 저장하고 타입별 Vector Index를 만든다."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

from src.graph.build_indexes import create_typed_vector_indexes, store_node_embeddings


def main() -> None:
    load_dotenv(".env")
    data = json.loads(Path("data/processed/04_graph/neo4j_data.json").read_text(encoding="utf-8"))
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ.get("NEO4J_USER", os.environ["NEO4J_USERNAME"]), os.environ["NEO4J_PASSWORD"]),
    )
    try:
        written = store_node_embeddings(driver, data["nodes"])
        create_typed_vector_indexes(driver)
        print(json.dumps({"embeddings_written": written, "indexes_created": 4}, ensure_ascii=False))
    finally:
        driver.close()


if __name__ == "__main__":
    main()
