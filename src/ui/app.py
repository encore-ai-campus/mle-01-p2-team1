"""Streamlit에서 실제 Neo4j Text2Cypher를 시험하는 화면."""
import os
import sys
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def render_qa_page(services: dict[str, Any]) -> None:
    import streamlit as st
    st.title("GraphRAG Text2Cypher 테스트")
    question = st.text_area("질문", value="등록된 축제의 총 개수를 알려줘", height=90)
    if not st.button("실행", type="primary") or not question.strip():
        return
    generated_cypher = None
    try:
        result = services["text2cypher"](question.strip())
        st.subheader("답변")
        st.write(result["answer"]["answer"])
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
        def text2cypher_service(question: str) -> dict[str, Any]:
            cypher = generate_cypher(question, llm)
            # 화면 오류 진단을 위해 생성 query를 호출부에 전달한다.
            text2cypher_service.last_cypher = cypher
            validate_read_only_cypher(cypher)
            with driver.session() as session:
                rows = [record.data() for record in session.run(cypher)]
            answer = generate_answer(
                question,
                build_answer_context(rows),
                llm,
                retrieval_method="text2cypher",
            )
            return {"cypher": cypher, "rows": rows, "answer": answer}
        return {"text2cypher": text2cypher_service}
    services = create_services()
    render_qa_page(services)

if __name__ == "__main__":
    main()
