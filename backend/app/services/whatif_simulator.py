"""
What-If Simulator

시나리오 기반 공급망 영향 분석.
Neo4j 다중 홉 탐색으로 영향 노드를 추출하고, 심각도를 계산합니다.
"""

from ..neo4j_client import Neo4jClient
from ..schemas.whatif_schema import AffectedNode


SEVERITY_ORDER = {"VERY_HIGH": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2}


def _score_to_severity(score: float) -> str:
    if score >= 4:
        return "CRITICAL"
    if score >= 3:
        return "HIGH"
    if score >= 2:
        return "MEDIUM"
    return "LOW"


def simulate_equipment_delay(equipment_name: str, delay_months: int) -> dict:
    """장비 공급 지연 시나리오: 장비 → 공정 → 결함/소재 → 가속기 역추적"""

    # 1. 영향받는 공정 단계 + 결함 + 소재
    records = Neo4jClient.run_query(
        """
        MATCH (eq:Equipment)
        WHERE eq.name CONTAINS $name OR eq.key CONTAINS $name
        OPTIONAL MATCH (ps:ProcessStep)-[:REQUIRES_EQUIPMENT]->(eq)
        OPTIONAL MATCH (ps)-[cd:CAUSES_DEFECT]->(df:DefectType)
        OPTIONAL MATCH (ps)-[:REQUIRES_MATERIAL]->(mat:Material)
        OPTIONAL MATCH (ef:EquipmentFailure)-[:FAILURE_OF]->(eq)
        RETURN DISTINCT
            id(eq) AS eq_id, eq.name AS eq_name, labels(eq)[0] AS eq_label,
            id(ps) AS ps_id, ps.name AS ps_name, ps.yield_impact AS yield_impact,
            id(df) AS df_id, df.name AS df_name, df.severity AS df_severity,
            id(mat) AS mat_id, mat.name AS mat_name, mat.supply_risk AS mat_risk,
            id(ef) AS ef_id, ef.name_kr AS ef_name
        """,
        {"name": equipment_name},
    )

    # 2. 영향받는 가속기 역추적
    accel_records = Neo4jClient.run_query(
        """
        MATCH (eq:Equipment)
        WHERE eq.name CONTAINS $name OR eq.key CONTAINS $name
        MATCH (ps:ProcessStep)-[:REQUIRES_EQUIPMENT]->(eq)
        MATCH (a:AIAccelerator)-[:MANUFACTURED_ON]->(pn:ProcessNode)
        RETURN DISTINCT id(a) AS a_id, a.name AS a_name
        """,
        {"name": equipment_name},
    )

    # 노드 수집 (중복 제거)
    affected: dict[int, AffectedNode] = {}
    equipment_ids = set()

    for r in records:
        # 장비 자체
        if r.get("eq_id") is not None:
            eid = r["eq_id"]
            equipment_ids.add(eid)
            if eid not in affected:
                affected[eid] = AffectedNode(
                    id=eid, label="Equipment", name=r["eq_name"],
                    severity="CRITICAL",
                    impact_reason=f"직접 영향 대상 장비 ({delay_months}개월 지연)"
                )

        # 공정 단계
        if r.get("ps_id") is not None:
            pid = r["ps_id"]
            yi = r.get("yield_impact", "MEDIUM")
            score = SEVERITY_ORDER.get(yi, 2) + (1 if delay_months >= 3 else 0)
            if pid not in affected or SEVERITY_ORDER.get(affected[pid].severity, 0) < score:
                affected[pid] = AffectedNode(
                    id=pid, label="ProcessStep", name=r["ps_name"],
                    severity=_score_to_severity(score),
                    impact_reason=f"장비 의존 공정 (yield_impact: {yi})"
                )

        # 결함
        if r.get("df_id") is not None:
            did = r["df_id"]
            ds = r.get("df_severity", "MEDIUM")
            score = SEVERITY_ORDER.get(ds, 2)
            if did not in affected:
                affected[did] = AffectedNode(
                    id=did, label="DefectType", name=r["df_name"],
                    severity=_score_to_severity(score),
                    impact_reason=f"장비 지연으로 인한 결함 리스크 증가 ({ds})"
                )

        # 소재
        if r.get("mat_id") is not None:
            mid = r["mat_id"]
            mr = r.get("mat_risk", "MEDIUM")
            score = SEVERITY_ORDER.get(mr, 2)
            if mid not in affected:
                affected[mid] = AffectedNode(
                    id=mid, label="Material", name=r["mat_name"],
                    severity=_score_to_severity(score),
                    impact_reason=f"관련 공정의 필수 소재 (supply_risk: {mr})"
                )

        # 장비 고장 모드
        if r.get("ef_id") is not None:
            efid = r["ef_id"]
            if efid not in affected:
                affected[efid] = AffectedNode(
                    id=efid, label="EquipmentFailure", name=r.get("ef_name", "Unknown"),
                    severity="HIGH",
                    impact_reason="장비 지연 시 유지보수 일정 영향"
                )

    # 가속기
    for r in accel_records:
        aid = r["a_id"]
        if aid not in affected:
            affected[aid] = AffectedNode(
                id=aid, label="AIAccelerator", name=r["a_name"],
                severity="HIGH",
                impact_reason=f"공정 지연으로 인한 생산 일정 영향 ({delay_months}개월)"
            )

    affected_list = sorted(
        affected.values(),
        key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x.severity, 4)
    )

    return {
        "affected_nodes": affected_list,
        "affected_node_ids": [n.id for n in affected_list],
        "total_affected": len(affected_list),
    }


def simulate_material_shortage(material_name: str, delay_months: int) -> dict:
    """소재 공급 중단 시나리오: 소재 → 공정 → 장비 → 결함 → 가속기"""

    records = Neo4jClient.run_query(
        """
        MATCH (mat:Material)
        WHERE mat.name CONTAINS $name OR mat.key CONTAINS $name
        OPTIONAL MATCH (ps:ProcessStep)-[:REQUIRES_MATERIAL]->(mat)
        OPTIONAL MATCH (ps)-[:REQUIRES_EQUIPMENT]->(eq:Equipment)
        OPTIONAL MATCH (ps)-[cd:CAUSES_DEFECT]->(df:DefectType)
        RETURN DISTINCT
            id(mat) AS mat_id, mat.name AS mat_name, mat.supply_risk AS mat_risk,
            mat.geographic_concentration AS geo, mat.major_suppliers AS suppliers,
            id(ps) AS ps_id, ps.name AS ps_name, ps.yield_impact AS yield_impact,
            id(eq) AS eq_id, eq.name AS eq_name,
            id(df) AS df_id, df.name AS df_name, df.severity AS df_severity
        """,
        {"name": material_name},
    )

    accel_records = Neo4jClient.run_query(
        """
        MATCH (mat:Material)
        WHERE mat.name CONTAINS $name OR mat.key CONTAINS $name
        MATCH (ps:ProcessStep)-[:REQUIRES_MATERIAL]->(mat)
        MATCH (a:AIAccelerator)-[:MANUFACTURED_ON]->(pn:ProcessNode)
        RETURN DISTINCT id(a) AS a_id, a.name AS a_name
        """,
        {"name": material_name},
    )

    affected: dict[int, AffectedNode] = {}
    alternatives = []

    for r in records:
        if r.get("mat_id") is not None:
            mid = r["mat_id"]
            if mid not in affected:
                geo = r.get("geo", "")
                suppliers = r.get("suppliers", "")
                affected[mid] = AffectedNode(
                    id=mid, label="Material", name=r["mat_name"],
                    severity="CRITICAL",
                    impact_reason=f"직접 영향 대상 소재 (risk: {r.get('mat_risk', 'N/A')}, 집중도: {geo})"
                )
                if suppliers:
                    alternatives.append({
                        "type": "alternative_suppliers",
                        "material": r["mat_name"],
                        "current_suppliers": suppliers,
                        "geographic_concentration": geo,
                    })

        if r.get("ps_id") is not None:
            pid = r["ps_id"]
            yi = r.get("yield_impact", "MEDIUM")
            score = SEVERITY_ORDER.get(yi, 2) + 1
            if pid not in affected:
                affected[pid] = AffectedNode(
                    id=pid, label="ProcessStep", name=r["ps_name"],
                    severity=_score_to_severity(score),
                    impact_reason=f"소재 의존 공정 (yield_impact: {yi})"
                )

        if r.get("eq_id") is not None:
            eid = r["eq_id"]
            if eid not in affected:
                affected[eid] = AffectedNode(
                    id=eid, label="Equipment", name=r["eq_name"],
                    severity="MEDIUM",
                    impact_reason="관련 공정의 필수 장비 (소재 중단 시 유휴)"
                )

        if r.get("df_id") is not None:
            did = r["df_id"]
            if did not in affected:
                affected[did] = AffectedNode(
                    id=did, label="DefectType", name=r["df_name"],
                    severity="MEDIUM",
                    impact_reason="소재 변경/부족 시 결함 발생 리스크"
                )

    for r in accel_records:
        aid = r["a_id"]
        if aid not in affected:
            affected[aid] = AffectedNode(
                id=aid, label="AIAccelerator", name=r["a_name"],
                severity="HIGH",
                impact_reason=f"소재 공급 중단으로 생산 영향 ({delay_months}개월)"
            )

    affected_list = sorted(
        affected.values(),
        key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x.severity, 4)
    )

    return {
        "affected_nodes": affected_list,
        "affected_node_ids": [n.id for n in affected_list],
        "total_affected": len(affected_list),
        "alternatives": alternatives,
    }


def simulate_process_delay(process_name: str, delay_months: int) -> dict:
    """공정 지연 시나리오: 공정노드 → 가속기 → 경쟁사"""

    records = Neo4jClient.run_query(
        """
        MATCH (pn:ProcessNode)
        WHERE pn.name CONTAINS $name OR pn.key CONTAINS $name
        OPTIONAL MATCH (a:AIAccelerator)-[:MANUFACTURED_ON]->(pn)
        OPTIONAL MATCH (a)-[:COMPETES_WITH]->(comp:AIAccelerator)
        OPTIONAL MATCH (succ:ProcessNode)-[:SUCCESSOR_OF]->(pn)
        RETURN DISTINCT
            id(pn) AS pn_id, pn.name AS pn_name,
            id(a) AS a_id, a.name AS a_name,
            id(comp) AS comp_id, comp.name AS comp_name,
            id(succ) AS succ_id, succ.name AS succ_name
        """,
        {"name": process_name},
    )

    affected: dict[int, AffectedNode] = {}

    for r in records:
        if r.get("pn_id") is not None:
            pid = r["pn_id"]
            if pid not in affected:
                affected[pid] = AffectedNode(
                    id=pid, label="ProcessNode", name=r["pn_name"],
                    severity="CRITICAL",
                    impact_reason=f"직접 영향 대상 공정노드 ({delay_months}개월 지연)"
                )

        if r.get("a_id") is not None:
            aid = r["a_id"]
            if aid not in affected:
                affected[aid] = AffectedNode(
                    id=aid, label="AIAccelerator", name=r["a_name"],
                    severity="CRITICAL",
                    impact_reason="해당 공정에서 제조되는 가속기 — 생산 중단"
                )

        if r.get("comp_id") is not None:
            cid = r["comp_id"]
            if cid not in affected:
                affected[cid] = AffectedNode(
                    id=cid, label="AIAccelerator", name=r["comp_name"],
                    severity="LOW",
                    impact_reason="경쟁 가속기 — 대체 수요 증가 가능"
                )

        if r.get("succ_id") is not None:
            sid = r["succ_id"]
            if sid not in affected:
                affected[sid] = AffectedNode(
                    id=sid, label="ProcessNode", name=r["succ_name"],
                    severity="MEDIUM",
                    impact_reason="후속 공정노드 — 마이그레이션 지연 가능"
                )

    affected_list = sorted(
        affected.values(),
        key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x.severity, 4)
    )

    return {
        "affected_nodes": affected_list,
        "affected_node_ids": [n.id for n in affected_list],
        "total_affected": len(affected_list),
        "alternatives": [],
    }
