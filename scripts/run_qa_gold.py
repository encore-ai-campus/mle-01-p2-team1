import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.rag.answer import build_answer_context, generate_answer
from src.rag.text2cypher import generate_cypher, validate_read_only_cypher
from src.rag.retrieval import fulltext_retrieve, vector_retrieve


REPORTS = ROOT / "data/processed/05_reports"


def main() -> None:
    load_dotenv(ROOT / ".env")
    gold_path = REPORTS / "qa_golden.json"
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    for row in gold:
        row["qa_id"] = row.pop("id", row.get("qa_id"))
    gold_path.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"), temperature=0)
    embedder = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    )
    results = []
    try:
        for index, row in enumerate(gold, start=1):
            item = {
                "qa_id": row["qa_id"], "question": row["question"],
                "text2cypher_success": False, "query_executable": False,
                "manual_correct": None,
            }
            item["fulltext_results_by_index"] = {}
            item["vector_results_by_index"] = {}
            for index_name in ("festival_fulltext", "program_fulltext", "accommodation_fulltext"):
                try:
                    item["fulltext_results_by_index"][index_name] = [
                        result["name"] for result in fulltext_retrieve(row["question"], driver, 5, index_name)
                        if result.get("name")
                    ]
                except Exception as error:
                    item.setdefault("retrieval_errors", []).append(f"{index_name}: {error}")
            for index_name in ("festival_vec", "program_vec", "accommodation_vec"):
                try:
                    item["vector_results_by_index"][index_name] = [
                        result["name"] for result in vector_retrieve(row["question"], driver, embedder, 5, index_name)
                        if result.get("name")
                    ]
                except Exception as error:
                    item.setdefault("retrieval_errors", []).append(f"{index_name}: {error}")
            try:
                cypher = generate_cypher(row["question"], llm)
                validate_read_only_cypher(cypher)
                with driver.session() as session:
                    rows = [record.data() for record in session.run(cypher)]
                item.update({"text2cypher_success": True, "query_executable": True, "cypher": cypher, "results": rows})
                item["answer"] = generate_answer(row["question"], build_answer_context(rows), llm, "text2cypher")["answer"]
            except Exception as error:
                item["error"] = str(error)
            results.append(item)
            print(f"[{index}/{len(gold)}] {row['qa_id']} {'OK' if item['query_executable'] else 'FAIL'}", flush=True)
    finally:
        driver.close()
    (REPORTS / "qa_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
