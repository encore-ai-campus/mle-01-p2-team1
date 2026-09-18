"""Neo4j GDS 기반 Graph 분석을 연결하는 골격."""

from typing import Any
import json
from pathlib import Path
import time


NODE_PROJECTION = (
    "Festival",
    "Location",
    "Audience",
    "Program",
    "Theme",
    "Artist",
    "Product",
    "Organization",
)

RELATIONSHIP_PROJECTION = (
    "HELD_IN",
    "TARGETS",
    "HAS_PROGRAM",
    "HAS_THEME",
    "FEATURES",
    "PROVIDES",
    "ORGANIZES",
)


# 입력: Neo4j driver, 분석 대상 Node/Relationship 범위
# 출력: graph_analysis_report.json
# TODO 1. 분석용 graph projection의 대상 label과 relationship을 정한다.
# TODO 2. PageRank를 실행하고 상위 Node와 점수를 저장한다.
# TODO 3. Louvain 또는 Leiden community detection을 실행한다.
# TODO 4. 분석 결과를 단순 숫자가 아니라 Entity/관계 맥락과 함께 해석한다.
# TODO 5. projection 삭제 여부와 분석 실행 시간을 report에 기록한다.

def create_graph_projection(
    driver: Any,
    graph_name: str,
) -> dict[str, Any]:
    """GDS 분석용 named graph projection을 만든다."""

    query = """
    CALL gds.graph.project(
        $graph_name,
        $node_projection,
        $relationship_projection
    )
    YIELD graphName, nodeCount, relationshipCount
    """

    with driver.session() as session:
        result = session.run(
            query,
            graph_name=graph_name,
            node_projection=list(NODE_PROJECTION),
            relationship_projection=list(RELATIONSHIP_PROJECTION),
        ).single()

    return dict(result) if result else {}


def _run_pagerank_rows(
    driver: Any,
    graph_name: str,
) -> list[dict[str, Any]]:
    query = """
    CALL gds.pageRank.stream($graph_name)
    YIELD nodeId, score
    WITH nodeId, gds.util.asNode(nodeId) AS node, score
    RETURN
        nodeId AS node_id,
        labels(node) AS labels,
        coalesce(node.canonical_name, node.name, node.title, node.id) AS name,
        score
    ORDER BY score DESC
    """

    with driver.session() as session:
        return [dict(row) for row in session.run(query, graph_name=graph_name)]


def run_pagerank(
    driver: Any,
    graph_name: str,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """PageRank를 실행하고 상위 Node와 점수를 반환한다."""

    return [
        {key: row[key] for key in ("labels", "name", "score")}
        for row in _run_pagerank_rows(driver, graph_name)[:top_k]
    ]


def run_community_detection(
    driver: Any,
    graph_name: str,
    pagerank_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Louvain 결과와 각 Node의 PageRank 점수를 반환한다."""

    query = """
    CALL gds.louvain.stream($graph_name)
    YIELD nodeId, communityId
    RETURN nodeId AS node_id, communityId AS community_id
    """

    with driver.session() as session:
        community_rows = [dict(row) for row in session.run(query, graph_name=graph_name)]

    if pagerank_rows is None:
        pagerank_rows = _run_pagerank_rows(driver, graph_name)

    pagerank_by_node_id = {row["node_id"]: row for row in pagerank_rows}
    communities = []
    for row in community_rows:
        pagerank = pagerank_by_node_id[row["node_id"]]
        communities.append(
            {
                "labels": pagerank["labels"],
                "name": pagerank["name"],
                "community_id": row["community_id"],
                "pagerank_score": pagerank["score"],
            }
        )

    communities.sort(key=lambda row: (row["community_id"], -row["pagerank_score"]))

    return communities

def interpret_graph_results(
    pagerank_top_nodes: list[dict[str, Any]],
    communities: list[dict[str, Any]],
) -> dict[str, Any]:
    """분석 결과를 Entity/관계 맥락과 함께 해석한다."""

    interpretation: dict[str, Any] = {
        "pagerank": [],
        "communities": {},
    }

    for row in pagerank_top_nodes:
        label = row["labels"][0] if row["labels"] else "Unknown"
        name = row["name"]
        score = row["score"]

        interpretation["pagerank"].append(
            {
                "entity_type": label,
                "entity_name": name,
                "score": score,
                "meaning": (
                    f"{name}은(는) {label} Entity이며, "
                    "다른 Entity들과의 연결 구조에서 상대적으로 중요한 위치를 가진다."
                ),
            }
        )

    for row in communities:
        community_id = str(row["community_id"])
        label = row["labels"][0] if row["labels"] else "Unknown"

        interpretation["communities"].setdefault(
            community_id,
            {
                "entity_count": 0,
                "entity_types": {},
                "entities": [],
            },
        )

        group = interpretation["communities"][community_id]
        group["entity_count"] += 1
        group["entity_types"][label] = (
            group["entity_types"].get(label, 0) + 1
        )
        group["entities"].append(
            {
                "name": row["name"],
                "entity_type": label,
            }
        )

    for community_id, group in interpretation["communities"].items():
        type_counts = group["entity_types"]

        dominant_type = (
            max(type_counts, key=type_counts.get)
            if type_counts
            else "Unknown"
        )

        group["meaning"] = (
            f"Community {community_id}에는 "
            f"{group['entity_count']}개의 Entity가 포함되어 있으며, "
            f"{dominant_type} 유형이 가장 많이 포함되어 있다. "
            "같은 community에 속한 Entity들은 projection에 포함된 여러 관계를 통해 "
            "상대적으로 밀접하게 연결된 하위 그룹으로 해석할 수 있다."
        )

    return interpretation

def run_graph_analysis(
    driver: Any,
    graph_name: str,
    output_path: str | Path = "graph_analysis_report.json",
) -> dict[str, Any]:
    """그래프 분석 전체를 실행하고 report를 저장한다."""

    started_at = time.perf_counter()
    projection_created = False
    projection_dropped = False
    projection_drop_error: str | None = None
    report: dict[str, Any] = {}

    try:
        projection_result = create_graph_projection(
            driver=driver,
            graph_name=graph_name,
        )
        projection_created = bool(projection_result)

        pagerank_rows = _run_pagerank_rows(driver, graph_name)
        pagerank_top_nodes = [
            {key: row[key] for key in ("labels", "name", "score")}
            for row in pagerank_rows[:10]
        ]

        communities = run_community_detection(
            driver=driver,
            graph_name=graph_name,
            pagerank_rows=pagerank_rows,
        )

        interpretation = interpret_graph_results(
            pagerank_top_nodes=pagerank_top_nodes,
            communities=communities,
        )

        # 전체 PageRank 1위
        pagerank_representative = (
            pagerank_top_nodes[0]
            if pagerank_top_nodes
            else None
        )

        # community별 대표 Node
        community_representatives: dict[str, Any] = {}

        for row in communities:
            community_id = str(row["community_id"])
            name = row["name"]
            score = row["pagerank_score"]

            current = community_representatives.get(community_id)

            if current is None or score > current["pagerank_score"]:
                community_representatives[community_id] = {
                    "name": name,
                    "labels": row["labels"],
                    "pagerank_score": score,
                }

        report = {
            "projection": {
                **projection_result,
                "node_labels": list(NODE_PROJECTION),
                "relationship_types": list(RELATIONSHIP_PROJECTION),
            },

            "pagerank": {
                "top_nodes": pagerank_top_nodes,
                "representative_node": pagerank_representative,
            },

            "communities": {
                "results": communities,
                "representative_nodes": community_representatives,
            },

            "interpretation": interpretation,
        }

    finally:
        if projection_created:
            try:
                with driver.session() as session:
                    result = session.run(
                        """
                        CALL gds.graph.drop($graph_name, false)
                        YIELD graphName
                        RETURN graphName
                        """,
                        graph_name=graph_name,
                    ).single()

                    projection_dropped = result is not None
            except Exception as exc:
                projection_drop_error = str(exc)

        execution = {
            "projection_dropped": projection_dropped,
            "elapsed_seconds": round(
                time.perf_counter() - started_at,
                4,
            ),
        }

        if projection_drop_error is not None:
            execution["projection_drop_error"] = projection_drop_error

        report["execution"] = execution

    output_path = Path(output_path)

    output_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return report

# 완료 조건: projection, PageRank, community 결과와 해석용 대표 Node가 저장된다.
# Freeze point: 분석 projection 구성과 알고리즘 파라미터는 결과 비교 전 고정한다.
