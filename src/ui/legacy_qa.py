"""Streamlit에서 실제 Neo4j Text2Cypher를 시험하는 화면."""
import os
import re
import sys
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def render_qa_page(services: dict[str, Any], router: Any) -> None:
    import streamlit as st
    st.title("GraphRAG Text2Cypher 테스트")
    question = st.text_area("질문", value="등록된 축제의 총 개수를 알려줘", height=90)
    if not st.button("실행", type="primary") or not question.strip():
        return
    generated_cypher = None
    try:
        selected_tool = router(question.strip())["selected_tool"]
        service = services.get(selected_tool, services["text2cypher"])
        result = service(question.strip())
        st.subheader("답변")
        st.write(result["answer"]["answer"])
        if result.get("cypher"):
            st.subheader("생성된 Cypher")
            st.code(result["cypher"], language="cypher")
        st.subheader(f"Neo4j 결과 ({len(result['rows'])}건)")
        st.dataframe(result["rows"], use_container_width=True)
    except Exception as error:
        st.error(f"실행 실패: {error}")
        generated_cypher = getattr(services["text2cypher"], "last_cypher", None)
        if generated_cypher:
            st.subheader("실패한 Cypher")
            st.code(generated_cypher, language="cypher")

def main() -> None:
    import streamlit as st
    from langchain_openai import ChatOpenAI
    from neo4j import GraphDatabase
    from src.rag.answer import build_answer_context, generate_answer
    from src.rag.router import route_question
    from src.rag.retrieval import hybrid_festival_retrieve, vector_retrieve
    from src.rag.text2cypher import generate_cypher, validate_read_only_cypher
    load_dotenv()
    st.set_page_config(page_title="Festival GraphRAG", layout="wide")
    required = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "OPENAI_API_KEY")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        st.error(".env에 필요한 설정이 없습니다: " + ", ".join(missing))
        return
    @st.cache_resource
    def create_services() -> dict[str, Any]:
        driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"), temperature=0)
        from langchain_openai import OpenAIEmbeddings
        embedder = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1536)
        region_pattern = re.compile(
            r"(서울|부산|대구|인천|광주|대전|울산|세종|제주|경기|강원|충북|충남|전북|전남|경북|경남)"
        )
        def text2cypher_service(question: str) -> dict[str, Any]:
            cypher = generate_cypher(question, llm)
            # 화면 오류 진단을 위해 생성 query를 호출부에 전달한다.
            text2cypher_service.last_cypher = cypher
            validate_read_only_cypher(cypher)
            with driver.session() as session:
                rows = [record.data() for record in session.run(cypher)]
            # 구조화 조건으로 결과가 없을 때 의미 기반 후보로 보강한다.
            if not rows:
                location_match = re.search(
                    r"(?:canonical_name\s+CONTAINS|CONTAINS)\s+'([^']+)'",
                    cypher,
                )
                location_hint = location_match.group(1) if location_match else None
                rows = hybrid_festival_retrieve(
                    question, driver, embedder, location_hint=location_hint, top_k=5
                )
            answer = generate_answer(
                question,
                build_answer_context(rows),
                llm,
                retrieval_method="text2cypher",
            )
            return {"cypher": cypher, "rows": rows, "answer": answer}
        def vector_service(question: str) -> dict[str, Any]:
            region_match = region_pattern.search(question)
            region = region_match.group(1) if region_match else None
            if region:
                results = hybrid_festival_retrieve(
                    question, driver, embedder, location_hint=region, top_k=5
                )
            else:
                results = []
                for entity_type in ("Festival", "Location", "Accommodation", "Experience"):
                    results.extend(vector_retrieve(question, driver, embedder, top_k=5, entity_type=entity_type))
                results = sorted(results, key=lambda row: (-row["score"], row.get("name") or ""))[:5]
            answer = generate_answer(question, build_answer_context(results), llm, retrieval_method="vector")
            return {"rows": results, "answer": answer}
        return {"text2cypher": text2cypher_service, "vector": vector_service}
    services = create_services()
    render_qa_page(services, route_question)

if __name__ == "__main__":
    main()
