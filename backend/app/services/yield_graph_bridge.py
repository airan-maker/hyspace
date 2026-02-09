"""
Yield-Graph Bridge Service

수율 이벤트와 Neo4j 그래프 노드 간 매핑 서비스.
장비/공정/소재 정보를 통해 관련 그래프 서브그래프를 조회합니다.
"""

from ..neo4j_client import Neo4jClient


def get_graph_context_for_event(
    process_step: str | None = None,
    equipment_id: str | None = None,
    material: str | None = None,
) -> dict:
    """수율 이벤트에서 관련 그래프 컨텍스트를 조회합니다."""

    session = Neo4jClient.get_session()
    if not session:
        return {"nodes": [], "relationships": [], "suggested_queries": []}

    nodes = []
    relationships = []
    suggested_queries = []

    with session:
        # 1. 공정 단계로 관련 노드 조회
        if process_step:
            result = session.run(
                """
                MATCH (ps:ProcessStep)
                WHERE ps.name CONTAINS $step OR ps.key CONTAINS $step
                OPTIONAL MATCH (ps)-[r1:REQUIRES_EQUIPMENT]->(eq:Equipment)
                OPTIONAL MATCH (ps)-[r2:REQUIRES_MATERIAL]->(mat:Material)
                OPTIONAL MATCH (ps)-[r3:CAUSES_DEFECT]->(def:DefectType)
                OPTIONAL MATCH (ps)<-[:HAS_PROCESS_STEP]-(pn:ProcessNode)
                RETURN ps, eq, mat, def, pn,
                       collect(DISTINCT {type: type(r1), from: ps.name, to: eq.name}) as eq_rels,
                       collect(DISTINCT {type: type(r2), from: ps.name, to: mat.name}) as mat_rels,
                       collect(DISTINCT {type: type(r3), from: ps.name, to: def.name}) as def_rels
                LIMIT 1
                """,
                step=process_step,
            )

            for record in result:
                ps = record["ps"]
                if ps:
                    nodes.append({
                        "id": ps.element_id,
                        "label": "ProcessStep",
                        "name": ps.get("name", ""),
                        "properties": dict(ps),
                    })

                eq = record["eq"]
                if eq:
                    nodes.append({
                        "id": eq.element_id,
                        "label": "Equipment",
                        "name": eq.get("name", ""),
                        "properties": dict(eq),
                    })
                    relationships.append({
                        "type": "REQUIRES_EQUIPMENT",
                        "from": ps.get("name", ""),
                        "to": eq.get("name", ""),
                    })

                mat = record["mat"]
                if mat:
                    nodes.append({
                        "id": mat.element_id,
                        "label": "Material",
                        "name": mat.get("name", ""),
                        "properties": dict(mat),
                    })
                    relationships.append({
                        "type": "REQUIRES_MATERIAL",
                        "from": ps.get("name", ""),
                        "to": mat.get("name", ""),
                    })

                defect = record["def"]
                if defect:
                    nodes.append({
                        "id": defect.element_id,
                        "label": "DefectType",
                        "name": defect.get("name", ""),
                        "properties": dict(defect),
                    })
                    relationships.append({
                        "type": "CAUSES_DEFECT",
                        "from": ps.get("name", ""),
                        "to": defect.get("name", ""),
                    })

                pn = record["pn"]
                if pn:
                    nodes.append({
                        "id": pn.element_id,
                        "label": "ProcessNode",
                        "name": pn.get("name", ""),
                        "properties": dict(pn),
                    })

                suggested_queries.append(
                    f"MATCH (ps:ProcessStep {{name: '{ps.get('name', '')}'}})-[r]-(n) RETURN ps, r, n"
                )

        # 2. 장비 ID로 관련 노드 조회
        if equipment_id:
            result = session.run(
                """
                MATCH (eq:Equipment)
                WHERE eq.name CONTAINS $equip OR eq.key CONTAINS $equip
                OPTIONAL MATCH (eq)-[:HAS_FAILURE_MODE]->(fm:FailureMode)
                OPTIONAL MATCH (eq)<-[:REQUIRES_EQUIPMENT]-(ps:ProcessStep)
                RETURN eq,
                       collect(DISTINCT fm) as failure_modes,
                       collect(DISTINCT ps.name) as affected_steps
                LIMIT 1
                """,
                equip=equipment_id,
            )

            for record in result:
                eq = record["eq"]
                if eq:
                    eq_exists = any(n["name"] == eq.get("name", "") for n in nodes)
                    if not eq_exists:
                        nodes.append({
                            "id": eq.element_id,
                            "label": "Equipment",
                            "name": eq.get("name", ""),
                            "properties": dict(eq),
                        })

                    for fm in record["failure_modes"]:
                        if fm:
                            nodes.append({
                                "id": fm.element_id,
                                "label": "FailureMode",
                                "name": fm.get("name", fm.get("mode", "")),
                                "properties": dict(fm),
                            })
                            relationships.append({
                                "type": "HAS_FAILURE_MODE",
                                "from": eq.get("name", ""),
                                "to": fm.get("name", fm.get("mode", "")),
                            })

                    for step_name in record["affected_steps"]:
                        if step_name:
                            relationships.append({
                                "type": "REQUIRES_EQUIPMENT",
                                "from": step_name,
                                "to": eq.get("name", ""),
                            })

                    suggested_queries.append(
                        f"MATCH (eq:Equipment {{name: '{eq.get('name', '')}'}})-[r]-(n) RETURN eq, r, n"
                    )

        # 3. 소재로 관련 노드 조회
        if material:
            result = session.run(
                """
                MATCH (mat:Material)
                WHERE mat.name CONTAINS $mat_name OR mat.key CONTAINS $mat_name
                OPTIONAL MATCH (mat)<-[:REQUIRES_MATERIAL]-(ps:ProcessStep)
                RETURN mat,
                       collect(DISTINCT ps.name) as dependent_steps
                LIMIT 1
                """,
                mat_name=material,
            )

            for record in result:
                m = record["mat"]
                if m:
                    mat_exists = any(n["name"] == m.get("name", "") for n in nodes)
                    if not mat_exists:
                        nodes.append({
                            "id": m.element_id,
                            "label": "Material",
                            "name": m.get("name", ""),
                            "properties": dict(m),
                        })

                    for step_name in record["dependent_steps"]:
                        if step_name:
                            relationships.append({
                                "type": "REQUIRES_MATERIAL",
                                "from": step_name,
                                "to": m.get("name", ""),
                            })

    # 중복 노드 제거
    seen = set()
    unique_nodes = []
    for n in nodes:
        if n["name"] not in seen:
            seen.add(n["name"])
            unique_nodes.append(n)

    return {
        "nodes": unique_nodes,
        "relationships": relationships,
        "suggested_queries": suggested_queries,
    }
