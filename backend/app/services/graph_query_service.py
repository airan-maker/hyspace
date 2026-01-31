"""
Graph Query Service

Neo4j 그래프 DB에 대한 도메인 특화 질의 메서드 모음
다중 홉 관계 탐색, 영향 분석, 경로 탐색 등
"""

from ..neo4j_client import Neo4jClient


class GraphQueryService:
    """그래프 기반 도메인 질의 서비스"""

    # ─────────────────────────────────────────────────────
    # 1. AI 가속기 중심 질의
    # ─────────────────────────────────────────────────────

    @staticmethod
    def get_accelerator_full_context(name: str) -> dict:
        """
        가속기의 전체 컨텍스트: 공정, 메모리, 패키징, 실행 가능 모델

        1-hop: 직접 관계된 엔티티
        """
        records = Neo4jClient.run_query(
            """
            MATCH (a:AIAccelerator)
            WHERE a.name CONTAINS $name OR a.key CONTAINS $name
            OPTIONAL MATCH (a)-[:MANUFACTURED_ON]->(pn:ProcessNode)
            OPTIONAL MATCH (a)-[mem:USES_MEMORY]->(hbm:HBMGeneration)
            OPTIONAL MATCH (a)-[:USES_PACKAGING]->(pkg:PackagingTech)
            OPTIONAL MATCH (a)-[run:CAN_RUN]->(model:AIModel)
            OPTIONAL MATCH (a)-[:COMPETES_WITH]->(comp:AIAccelerator)
            RETURN a, pn, hbm, mem, pkg,
                   collect(DISTINCT {model: model.name, precision: run.precision, util: run.memory_utilization_pct}) as models,
                   collect(DISTINCT comp.name) as competitors
            """,
            {"name": name},
        )
        if not records:
            return {}

        r = records[0]
        return {
            "accelerator": r.get("a"),
            "process_node": r.get("pn"),
            "hbm": r.get("hbm"),
            "memory_relation": r.get("mem"),
            "packaging": r.get("pkg"),
            "compatible_models": r.get("models", []),
            "competitors": r.get("competitors", []),
        }

    @staticmethod
    def get_supply_chain_risks_for_accelerator(name: str) -> list[dict]:
        """
        가속기 → 공정노드 → 공정단계 → 소재 → 리스크 (다중 홉)

        "H100에 영향을 주는 모든 공급망 리스크는?"
        """
        return Neo4jClient.run_query(
            """
            MATCH (a:AIAccelerator)
            WHERE a.name CONTAINS $name OR a.key CONTAINS $name
            MATCH (a)-[:MANUFACTURED_ON]->(pn:ProcessNode)
            MATCH (ps:ProcessStep)-[:REQUIRES_MATERIAL]->(mat:Material)
            WHERE mat.supply_risk IN ['VERY_HIGH', 'HIGH']
            OPTIONAL MATCH (ps)-[:REQUIRES_EQUIPMENT]->(eq:Equipment)
            RETURN DISTINCT
                a.name AS accelerator,
                pn.name AS process_node,
                ps.name AS process_step,
                mat.name AS material,
                mat.supply_risk AS risk_level,
                mat.criticality AS criticality,
                mat.geographic_concentration AS geo_concentration,
                mat.major_suppliers AS suppliers,
                mat.lead_time_weeks AS lead_time,
                collect(DISTINCT eq.name) AS required_equipment
            ORDER BY mat.supply_risk DESC, mat.criticality DESC
            """,
            {"name": name},
        )

    @staticmethod
    def get_accelerator_comparison(names: list[str]) -> list[dict]:
        """여러 가속기 비교"""
        return Neo4jClient.run_query(
            """
            MATCH (a:AIAccelerator)
            WHERE a.key IN $names OR any(n IN $names WHERE a.name CONTAINS n)
            OPTIONAL MATCH (a)-[:MANUFACTURED_ON]->(pn:ProcessNode)
            OPTIONAL MATCH (a)-[:USES_MEMORY]->(hbm:HBMGeneration)
            RETURN a.name AS name,
                   a.vendor AS vendor,
                   a.int8_tops AS int8_tops,
                   a.bf16_tflops AS bf16_tflops,
                   a.tdp_watts AS tdp,
                   a.msrp_usd AS price,
                   a.memory_capacity_gb AS memory_gb,
                   a.memory_bandwidth_tbps AS bandwidth_tbps,
                   pn.name AS process_node,
                   hbm.generation AS hbm_gen,
                   CASE WHEN a.tdp_watts > 0 THEN round(toFloat(a.int8_tops) / a.tdp_watts, 1) ELSE null END AS tops_per_watt
            ORDER BY a.int8_tops DESC
            """,
            {"names": names},
        )

    # ─────────────────────────────────────────────────────
    # 2. 공정 & 수율 중심 질의
    # ─────────────────────────────────────────────────────

    @staticmethod
    def get_process_flow_with_risks() -> list[dict]:
        """공정 플로우 + 각 단계별 결함/장비/소재 리스크"""
        return Neo4jClient.run_query(
            """
            MATCH (ps:ProcessStep)
            OPTIONAL MATCH (ps)-[:NEXT_STEP]->(next:ProcessStep)
            OPTIONAL MATCH (ps)-[cd:CAUSES_DEFECT]->(d:DefectType)
            OPTIONAL MATCH (ps)-[:REQUIRES_EQUIPMENT]->(eq:Equipment)
            OPTIONAL MATCH (ps)-[:REQUIRES_MATERIAL]->(mat:Material)
            RETURN ps.name AS step_name,
                   ps.module AS module,
                   ps.step_order AS step_order,
                   ps.yield_impact AS yield_impact,
                   collect(DISTINCT next.name) AS next_steps,
                   collect(DISTINCT {defect: d.name, severity: d.severity, kill_ratio: cd.kill_ratio_pct}) AS defects,
                   collect(DISTINCT eq.name) AS equipment,
                   collect(DISTINCT {material: mat.name, risk: mat.supply_risk}) AS materials
            ORDER BY ps.step_order
            """
        )

    @staticmethod
    def get_high_risk_process_steps() -> list[dict]:
        """수율 영향이 HIGH인 공정 단계 + 관련 결함/장비"""
        return Neo4jClient.run_query(
            """
            MATCH (ps:ProcessStep)
            WHERE ps.yield_impact = 'HIGH'
            OPTIONAL MATCH (ps)-[cd:CAUSES_DEFECT]->(d:DefectType)
            WHERE d.severity IN ['CATASTROPHIC', 'MAJOR']
            OPTIONAL MATCH (ps)-[:REQUIRES_EQUIPMENT]->(eq:Equipment)
            OPTIONAL MATCH (ef:EquipmentFailure)-[:FAILURE_OF]->(eq)
            RETURN ps.name AS step,
                   ps.module AS module,
                   collect(DISTINCT {defect: d.name, kill_ratio: cd.kill_ratio_pct}) AS critical_defects,
                   collect(DISTINCT {equipment: eq.name, failure_mode: ef.name_kr, mtbf: ef.mtbf_hours}) AS equipment_risks
            ORDER BY ps.step_order
            """
        )

    # ─────────────────────────────────────────────────────
    # 3. 장비 영향 분석
    # ─────────────────────────────────────────────────────

    @staticmethod
    def get_equipment_impact_analysis(equipment_name: str) -> dict:
        """
        장비 고장 시 영향 분석:
        장비 → 고장모드, 관련 공정, 관련 결함, 영향받는 소재

        "ASML EUV 장비가 고장나면 어떤 영향이?"
        """
        records = Neo4jClient.run_query(
            """
            MATCH (eq:Equipment)
            WHERE eq.name CONTAINS $name OR eq.key CONTAINS $name
            OPTIONAL MATCH (ef:EquipmentFailure)-[:FAILURE_OF]->(eq)
            OPTIONAL MATCH (ps:ProcessStep)-[:REQUIRES_EQUIPMENT]->(eq)
            OPTIONAL MATCH (ps)-[cd:CAUSES_DEFECT]->(d:DefectType)
            OPTIONAL MATCH (ps)-[:REQUIRES_MATERIAL]->(mat:Material)
            RETURN eq.name AS equipment,
                   eq.vendor AS vendor,
                   eq.category AS category,
                   eq.mtbf_hours AS mtbf,
                   eq.purchase_price_million_usd AS price_m,
                   collect(DISTINCT {
                       mode: ef.name_kr,
                       mtbf: ef.mtbf_hours,
                       mttr: ef.mttr_hours,
                       warnings: ef.early_warning_signs,
                       wafer_risk: ef.wafer_risk
                   }) AS failure_modes,
                   collect(DISTINCT ps.name) AS affected_steps,
                   collect(DISTINCT {defect: d.name, severity: d.severity}) AS potential_defects,
                   collect(DISTINCT {material: mat.name, risk: mat.supply_risk}) AS related_materials
            """,
            {"name": equipment_name},
        )
        return records[0] if records else {}

    # ─────────────────────────────────────────────────────
    # 4. 소재 공급망 분석
    # ─────────────────────────────────────────────────────

    @staticmethod
    def get_material_dependency_chain(material_name: str) -> dict:
        """
        소재 → 공정단계 → 장비 → 고장모드 전체 체인

        "EUV 포토레지스트 공급이 중단되면?"
        """
        records = Neo4jClient.run_query(
            """
            MATCH (mat:Material)
            WHERE mat.name CONTAINS $name OR mat.key CONTAINS $name
            OPTIONAL MATCH (ps:ProcessStep)-[:REQUIRES_MATERIAL]->(mat)
            OPTIONAL MATCH (ps)-[:REQUIRES_EQUIPMENT]->(eq:Equipment)
            OPTIONAL MATCH (ps)-[cd:CAUSES_DEFECT]->(d:DefectType)
            RETURN mat.name AS material,
                   mat.criticality AS criticality,
                   mat.supply_risk AS supply_risk,
                   mat.geographic_concentration AS geo,
                   mat.major_suppliers AS suppliers,
                   mat.lead_time_weeks AS lead_time,
                   collect(DISTINCT {
                       step: ps.name,
                       module: ps.module,
                       yield_impact: ps.yield_impact
                   }) AS dependent_steps,
                   collect(DISTINCT eq.name) AS related_equipment,
                   collect(DISTINCT {defect: d.name, kill_ratio: cd.kill_ratio_pct}) AS associated_defects
            """,
            {"name": material_name},
        )
        return records[0] if records else {}

    @staticmethod
    def get_critical_supply_risks() -> list[dict]:
        """공급 리스크가 높은 소재 + 영향 범위 요약"""
        return Neo4jClient.run_query(
            """
            MATCH (mat:Material)
            WHERE mat.supply_risk IN ['VERY_HIGH', 'HIGH']
            OPTIONAL MATCH (ps:ProcessStep)-[:REQUIRES_MATERIAL]->(mat)
            RETURN mat.name AS material,
                   mat.category AS category,
                   mat.supply_risk AS risk_level,
                   mat.criticality AS criticality,
                   mat.geographic_concentration AS geo,
                   mat.lead_time_weeks AS lead_time,
                   count(DISTINCT ps) AS affected_step_count,
                   collect(DISTINCT ps.name) AS affected_steps
            ORDER BY mat.supply_risk DESC, mat.criticality DESC
            """
        )

    # ─────────────────────────────────────────────────────
    # 5. 경로 탐색
    # ─────────────────────────────────────────────────────

    @staticmethod
    def find_path_between(from_name: str, to_name: str, max_hops: int = 5) -> list[dict]:
        """두 엔티티 간 최단 경로 탐색"""
        return Neo4jClient.run_query(
            """
            MATCH (a), (b)
            WHERE (a.name CONTAINS $from_name OR a.key CONTAINS $from_name)
              AND (b.name CONTAINS $to_name OR b.key CONTAINS $to_name)
            MATCH p = shortestPath((a)-[*1..""" + str(max_hops) + """]->(b))
            RETURN [n IN nodes(p) | {label: labels(n)[0], name: coalesce(n.name, n.key)}] AS path_nodes,
                   [r IN relationships(p) | type(r)] AS path_relationships,
                   length(p) AS hops
            LIMIT 5
            """,
            {"from_name": from_name, "to_name": to_name},
        )

    # ─────────────────────────────────────────────────────
    # 6. 전체 그래프 요약
    # ─────────────────────────────────────────────────────

    @staticmethod
    def get_graph_overview() -> dict:
        """전체 그래프 노드/관계 요약"""
        return Neo4jClient.get_stats()

    @staticmethod
    def get_all_nodes_for_visualization() -> dict:
        """
        Frontend 시각화용: 모든 노드 + 관계를 JSON으로 반환
        force-graph 라이브러리 호환 포맷
        """
        nodes = Neo4jClient.run_query(
            """
            MATCH (n)
            RETURN id(n) AS id,
                   labels(n)[0] AS label,
                   coalesce(n.name, n.key) AS name,
                   n AS properties
            """
        )
        links = Neo4jClient.run_query(
            """
            MATCH (a)-[r]->(b)
            RETURN id(a) AS source,
                   id(b) AS target,
                   type(r) AS type
            """
        )
        return {"nodes": nodes, "links": links}

    @staticmethod
    def run_custom_cypher(cypher: str, params: dict = None) -> list[dict]:
        """개발/디버깅용 임의 Cypher 실행"""
        return Neo4jClient.run_query(cypher, params or {})
