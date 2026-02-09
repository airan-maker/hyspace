"""
Graph Search Service

Neo4j 노드 검색 및 필터링 서비스
"""

from ..neo4j_client import Neo4jClient


def search_graph_nodes(
    query: str | None = None,
    label: str | None = None,
    risk: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """그래프 노드를 검색합니다."""

    session = Neo4jClient.get_session()
    if not session:
        return []

    with session:
        # 동적 Cypher 생성
        where_clauses = []
        params: dict = {"limit": limit}

        # 라벨 필터
        label_filter = f":{label}" if label else ""

        # 텍스트 검색
        if query:
            where_clauses.append(
                "(toLower(n.name) CONTAINS toLower($query) OR "
                "toLower(n.key) CONTAINS toLower($query) OR "
                "toLower(toString(coalesce(n.vendor, ''))) CONTAINS toLower($query) OR "
                "toLower(toString(coalesce(n.category, ''))) CONTAINS toLower($query))"
            )
            params["query"] = query

        # 리스크 필터
        if risk:
            where_clauses.append(
                "(n.supply_risk = $risk OR n.criticality = $risk OR n.yield_impact = $risk)"
            )
            params["risk"] = risk

        where_str = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cypher = f"""
            MATCH (n{label_filter})
            {where_str}
            RETURN n, labels(n) as nodeLabels,
                   size([(n)-[]-() | 1]) as connectionCount
            ORDER BY connectionCount DESC
            LIMIT $limit
        """

        result = session.run(cypher, **params)

        nodes = []
        for record in result:
            node = record["n"]
            labels = record["nodeLabels"]
            conn_count = record["connectionCount"]

            props = dict(node)
            nodes.append({
                "id": node.element_id,
                "name": props.get("name", props.get("key", "")),
                "label": labels[0] if labels else "Unknown",
                "labels": labels,
                "connection_count": conn_count,
                "properties": props,
            })

        return nodes


def get_available_labels() -> list[str]:
    """사용 가능한 노드 라벨 목록을 반환합니다."""

    session = Neo4jClient.get_session()
    if not session:
        return []

    with session:
        result = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
        return [record["label"] for record in result]
