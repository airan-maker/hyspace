"""
Ontology → Neo4j Graph Migrator

인메모리 Python 온톨로지를 Neo4j 그래프 데이터베이스로 마이그레이션
노드 생성 + 크로스 도메인 관계(엣지) 생성
"""

from dataclasses import fields, asdict
from ..neo4j_client import Neo4jClient
from ..ontology import (
    SemiconductorOntology,
    AIIndustryOntology,
    MaterialsKnowledgeBase,
    EquipmentKnowledgeBase,
    ProcessFlowOntology,
    FailureModeOntology,
)


class GraphMigrator:
    """온톨로지 데이터를 Neo4j 그래프로 마이그레이션"""

    def migrate_all(self) -> dict:
        """전체 온톨로지 마이그레이션 실행"""
        if not Neo4jClient.is_available():
            return {"error": "Neo4j is not available"}

        stats = {}
        self.clear_graph()

        stats["process_nodes"] = self.migrate_process_nodes()
        stats["packaging"] = self.migrate_packaging()
        stats["hbm"] = self.migrate_hbm()
        stats["accelerators"] = self.migrate_accelerators()
        stats["ai_models"] = self.migrate_ai_models()
        stats["materials"] = self.migrate_materials()
        stats["equipment"] = self.migrate_equipment()
        stats["process_steps"] = self.migrate_process_flow()
        stats["defect_types"] = self.migrate_defect_types()
        stats["failure_modes"] = self.migrate_failure_modes()
        stats["cross_domain_edges"] = self.create_cross_domain_edges()

        return stats

    def clear_graph(self):
        """그래프 전체 삭제"""
        Neo4jClient.run_write("MATCH (n) DETACH DELETE n")

    # ─────────────────────────────────────────────────────
    # 노드 마이그레이션
    # ─────────────────────────────────────────────────────

    def migrate_process_nodes(self) -> int:
        """ProcessNode 노드 생성 (11개)"""
        nodes = SemiconductorOntology.get_all_nodes()
        count = 0
        for key, node in nodes.items():
            Neo4jClient.run_write(
                """
                CREATE (n:ProcessNode {
                    key: $key,
                    name: $name,
                    node_nm: $node_nm,
                    vendor: $vendor,
                    transistor_type: $transistor_type,
                    logic_density_mtr_per_mm2: $logic_density,
                    sram_cell_size_um2: $sram_cell,
                    speed_improvement_pct: $speed,
                    power_reduction_pct: $power,
                    density_improvement_pct: $density,
                    euv_layers: $euv_layers,
                    total_mask_layers: $mask_layers,
                    wafer_cost_usd: $wafer_cost,
                    nre_cost_million_usd: $nre_cost,
                    defect_density_per_cm2: $defect_density,
                    typical_yield_pct: $yield_pct,
                    volume_production_year: $volume_year,
                    is_available: $is_available,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "name": node.name,
                    "node_nm": node.node_nm,
                    "vendor": node.vendor.value,
                    "transistor_type": node.transistor_type,
                    "logic_density": node.logic_density_mtr_per_mm2,
                    "sram_cell": node.sram_cell_size_um2,
                    "speed": node.speed_improvement_pct,
                    "power": node.power_reduction_pct,
                    "density": node.density_improvement_pct,
                    "euv_layers": node.euv_layers,
                    "mask_layers": node.total_mask_layers,
                    "wafer_cost": node.wafer_cost_usd,
                    "nre_cost": node.nre_cost_million_usd,
                    "defect_density": node.defect_density_per_cm2,
                    "yield_pct": node.typical_yield_pct,
                    "volume_year": node.volume_production_year,
                    "is_available": node.is_available,
                    "description": node.description,
                },
            )
            count += 1

        # SUCCESSOR_OF 관계: 같은 벤더의 노드 간 세대 순서
        Neo4jClient.run_write(
            """
            MATCH (a:ProcessNode), (b:ProcessNode)
            WHERE a.vendor = b.vendor
              AND a.volume_production_year < b.volume_production_year
              AND a.node_nm > b.node_nm
            WITH a, b ORDER BY b.volume_production_year
            WITH a, collect(b)[0] AS successor
            WHERE successor IS NOT NULL
            CREATE (successor)-[:SUCCESSOR_OF]->(a)
            """
        )

        return count

    def migrate_packaging(self) -> int:
        """PackagingTech 노드 생성 (6개)"""
        pkgs = SemiconductorOntology.get_all_packaging()
        count = 0
        for key, pkg in pkgs.items():
            Neo4jClient.run_write(
                """
                CREATE (n:PackagingTech {
                    key: $key,
                    name: $name,
                    full_name: $full_name,
                    vendor: $vendor,
                    max_hbm_stacks: $max_hbm,
                    max_chiplets: $max_chiplets,
                    interconnect_bandwidth_tbps: $bandwidth,
                    typical_power_delivery_w: $power,
                    die_size_limit_mm2: $die_limit,
                    cost_premium_vs_organic_pct: $cost_premium,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "name": pkg.name,
                    "full_name": pkg.full_name,
                    "vendor": pkg.vendor,
                    "max_hbm": pkg.max_hbm_stacks,
                    "max_chiplets": pkg.max_chiplets,
                    "bandwidth": pkg.interconnect_bandwidth_tbps,
                    "power": pkg.typical_power_delivery_w,
                    "die_limit": pkg.die_size_limit_mm2,
                    "cost_premium": pkg.cost_premium_vs_organic_pct,
                    "description": pkg.description,
                },
            )
            count += 1
        return count

    def migrate_hbm(self) -> int:
        """HBMGeneration 노드 생성 (4개)"""
        hbms = AIIndustryOntology.get_all_hbm()
        count = 0
        for key, hbm in hbms.items():
            Neo4jClient.run_write(
                """
                CREATE (n:HBMGeneration {
                    key: $key,
                    generation: $generation,
                    jedec_standard: $jedec,
                    bandwidth_per_stack_gbps: $bandwidth,
                    max_capacity_per_stack_gb: $capacity,
                    pin_speed_gbps: $pin_speed,
                    io_width_bits: $io_width,
                    stack_height: $stack_height,
                    vendors: $vendors,
                    power_per_stack_w: $power,
                    volume_production_year: $volume_year,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "generation": hbm.generation,
                    "jedec": hbm.jedec_standard,
                    "bandwidth": hbm.bandwidth_per_stack_gbps,
                    "capacity": hbm.max_capacity_per_stack_gb,
                    "pin_speed": hbm.pin_speed_gbps,
                    "io_width": hbm.io_width_bits,
                    "stack_height": hbm.stack_height,
                    "vendors": hbm.vendors,
                    "power": hbm.power_per_stack_w,
                    "volume_year": hbm.volume_production_year,
                    "description": hbm.description,
                },
            )
            count += 1
        return count

    def migrate_accelerators(self) -> int:
        """AIAccelerator 노드 생성 (7개)"""
        accs = AIIndustryOntology.get_all_accelerators()
        count = 0
        for key, acc in accs.items():
            Neo4jClient.run_write(
                """
                CREATE (n:AIAccelerator {
                    key: $key,
                    name: $name,
                    codename: $codename,
                    vendor: $vendor,
                    category: $category,
                    process_node: $process_node,
                    transistor_count_billion: $transistors,
                    die_size_mm2: $die_size,
                    num_dies: $num_dies,
                    packaging: $packaging,
                    tdp_watts: $tdp,
                    msrp_usd: $msrp,
                    launch_year: $launch_year,
                    interconnect: $interconnect,
                    pcie_gen: $pcie_gen,
                    fp64_tflops: $fp64,
                    bf16_tflops: $bf16,
                    fp8_tflops: $fp8,
                    int8_tops: $int8,
                    memory_type: $mem_type,
                    memory_capacity_gb: $mem_capacity,
                    memory_bandwidth_tbps: $mem_bandwidth,
                    memory_stack_count: $mem_stacks,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "name": acc.name,
                    "codename": acc.codename,
                    "vendor": acc.vendor.value,
                    "category": acc.category.value,
                    "process_node": acc.process_node,
                    "transistors": acc.transistor_count_billion,
                    "die_size": acc.die_size_mm2,
                    "num_dies": acc.num_dies,
                    "packaging": acc.packaging,
                    "tdp": acc.tdp_watts,
                    "msrp": acc.msrp_usd,
                    "launch_year": acc.launch_year,
                    "interconnect": acc.interconnect,
                    "pcie_gen": acc.pcie_gen,
                    "fp64": acc.compute.fp64_tflops,
                    "bf16": acc.compute.bf16_tflops,
                    "fp8": acc.compute.fp8_tflops,
                    "int8": acc.compute.int8_tops,
                    "mem_type": acc.memory.type,
                    "mem_capacity": acc.memory.capacity_gb,
                    "mem_bandwidth": acc.memory.bandwidth_tbps,
                    "mem_stacks": acc.memory.stack_count,
                    "description": acc.description,
                },
            )
            count += 1
        return count

    def migrate_ai_models(self) -> int:
        """AIModel 노드 생성 (5개)"""
        models = AIIndustryOntology.get_all_models()
        count = 0
        for key, model in models.items():
            Neo4jClient.run_write(
                """
                CREATE (n:AIModel {
                    key: $key,
                    name: $name,
                    family: $family,
                    vendor: $vendor,
                    parameter_count_billion: $params,
                    architecture: $arch,
                    context_length: $ctx,
                    inference_memory_fp16_gb: $mem_fp16,
                    inference_memory_int8_gb: $mem_int8,
                    inference_memory_int4_gb: $mem_int4,
                    release_year: $release_year,
                    license_type: $license,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "name": model.name,
                    "family": model.family,
                    "vendor": model.vendor,
                    "params": model.parameter_count_billion,
                    "arch": model.architecture,
                    "ctx": model.context_length,
                    "mem_fp16": model.inference_memory_fp16_gb,
                    "mem_int8": model.inference_memory_int8_gb,
                    "mem_int4": model.inference_memory_int4_gb,
                    "release_year": model.release_year,
                    "license": model.license_type,
                    "description": model.description,
                },
            )
            count += 1
        return count

    def migrate_materials(self) -> int:
        """Material 노드 생성 (11개)"""
        mats = MaterialsKnowledgeBase.get_all_materials()
        count = 0
        for key, mat in mats.items():
            Neo4jClient.run_write(
                """
                CREATE (n:Material {
                    key: $key,
                    name: $name,
                    chemical_formula: $formula,
                    category: $category,
                    criticality: $criticality,
                    supply_risk: $supply_risk,
                    process_steps: $process_steps,
                    typical_purity: $purity,
                    major_suppliers: $suppliers,
                    geographic_concentration: $geo,
                    lead_time_weeks: $lead_time,
                    unit_cost_range: $cost_range,
                    export_controlled: $export_ctrl,
                    pfas_related: $pfas,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "name": mat.name,
                    "formula": mat.chemical_formula,
                    "category": mat.category.value,
                    "criticality": mat.criticality.value,
                    "supply_risk": mat.supply_risk.value,
                    "process_steps": mat.process_steps,
                    "purity": mat.typical_purity,
                    "suppliers": mat.major_suppliers,
                    "geo": mat.geographic_concentration,
                    "lead_time": mat.lead_time_weeks,
                    "cost_range": mat.unit_cost_range,
                    "export_ctrl": mat.export_controlled,
                    "pfas": mat.pfas_related,
                    "description": mat.description,
                },
            )
            count += 1
        return count

    def migrate_equipment(self) -> int:
        """Equipment 노드 생성 (7개)"""
        equips = EquipmentKnowledgeBase.get_all_equipment()
        count = 0
        for key, eq in equips.items():
            Neo4jClient.run_write(
                """
                CREATE (n:Equipment {
                    key: $key,
                    name: $name,
                    model: $model,
                    vendor: $vendor,
                    category: $category,
                    throughput_wph: $throughput,
                    min_node_nm: $min_node,
                    mtbf_hours: $mtbf,
                    mttr_hours: $mttr,
                    annual_uptime_pct: $uptime,
                    purchase_price_million_usd: $price,
                    lead_time_months: $lead_time,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "name": eq.name,
                    "model": eq.model,
                    "vendor": eq.vendor.name,
                    "category": eq.category.value,
                    "throughput": eq.throughput_wph,
                    "min_node": eq.min_node_nm,
                    "mtbf": eq.mtbf_hours,
                    "mttr": eq.mttr_hours,
                    "uptime": eq.annual_uptime_pct,
                    "price": eq.purchase_price_million_usd,
                    "lead_time": eq.lead_time_months,
                    "description": eq.description,
                },
            )
            count += 1
        return count

    def migrate_process_flow(self) -> int:
        """ProcessStep 노드 + NEXT_STEP 관계 생성 (13개)"""
        steps = ProcessFlowOntology.get_full_flow()
        count = 0
        for key, step in steps.items():
            Neo4jClient.run_write(
                """
                CREATE (n:ProcessStep {
                    key: $key,
                    step_id: $step_id,
                    name: $name,
                    module: $module,
                    step_order: $order,
                    equipment_type: $equip_type,
                    typical_duration_minutes: $duration,
                    yield_impact: $yield_impact,
                    defect_types: $defect_types,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "step_id": step.step_id,
                    "name": step.name,
                    "module": step.module.value,
                    "order": step.order,
                    "equip_type": step.equipment_type,
                    "duration": step.typical_duration_minutes,
                    "yield_impact": step.yield_impact,
                    "defect_types": step.defect_types,
                    "description": step.description,
                },
            )
            count += 1

        # NEXT_STEP 관계
        for key, step in steps.items():
            for next_key in step.next_steps:
                Neo4jClient.run_write(
                    """
                    MATCH (a:ProcessStep {key: $from_key})
                    MATCH (b:ProcessStep {key: $to_key})
                    CREATE (a)-[:NEXT_STEP]->(b)
                    """,
                    {"from_key": key, "to_key": next_key},
                )

        return count

    def migrate_defect_types(self) -> int:
        """DefectType 노드 생성 (6개)"""
        defects = FailureModeOntology.get_all_defect_types()
        count = 0
        for key, defect in defects.items():
            Neo4jClient.run_write(
                """
                CREATE (n:DefectType {
                    key: $key,
                    defect_id: $defect_id,
                    name: $name,
                    name_kr: $name_kr,
                    category: $category,
                    severity: $severity,
                    detection_method: $detection,
                    kill_ratio_pct: $kill_ratio,
                    yield_impact_min_pct: $yi_min,
                    yield_impact_max_pct: $yi_max,
                    common_causes: $causes,
                    affected_process_steps: $affected_steps,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "defect_id": defect.defect_id,
                    "name": defect.name,
                    "name_kr": defect.name_kr,
                    "category": defect.category,
                    "severity": defect.severity.value,
                    "detection": defect.detection_method,
                    "kill_ratio": defect.kill_ratio_pct,
                    "yi_min": defect.yield_impact_pct[0],
                    "yi_max": defect.yield_impact_pct[1],
                    "causes": defect.common_causes,
                    "affected_steps": defect.affected_process_steps,
                    "description": defect.description,
                },
            )
            count += 1
        return count

    def migrate_failure_modes(self) -> int:
        """EquipmentFailure 노드 생성 (4개)"""
        modes = FailureModeOntology.get_all_failure_modes()
        count = 0
        for key, fm in modes.items():
            Neo4jClient.run_write(
                """
                CREATE (n:EquipmentFailure {
                    key: $key,
                    mode_id: $mode_id,
                    name: $name,
                    name_kr: $name_kr,
                    equipment_type: $equip_type,
                    failure_rate_per_1000h: $failure_rate,
                    mtbf_hours: $mtbf,
                    mttr_hours: $mttr,
                    early_warning_signs: $warnings,
                    detection_sensors: $sensors,
                    production_impact: $prod_impact,
                    wafer_risk: $wafer_risk,
                    preventive_measure: $prevention,
                    description: $description
                })
                """,
                {
                    "key": key,
                    "mode_id": fm.mode_id,
                    "name": fm.name,
                    "name_kr": fm.name_kr,
                    "equip_type": fm.equipment_type,
                    "failure_rate": fm.failure_rate_per_1000h,
                    "mtbf": fm.mtbf_hours,
                    "mttr": fm.mttr_hours,
                    "warnings": fm.early_warning_signs,
                    "sensors": fm.detection_sensors,
                    "prod_impact": fm.production_impact,
                    "wafer_risk": fm.wafer_risk,
                    "prevention": fm.preventive_measure,
                    "description": fm.description,
                },
            )
            count += 1
        return count

    # ─────────────────────────────────────────────────────
    # 크로스 도메인 관계 생성 (핵심)
    # ─────────────────────────────────────────────────────

    def create_cross_domain_edges(self) -> dict:
        """
        현재 암묵적 문자열 참조를 명시적 Neo4j 관계로 변환

        이것이 그래프 DB의 진정한 가치 — 다중 홉 질의가 가능해짐
        """
        edge_counts = {}

        # 1. AIAccelerator → ProcessNode (MANUFACTURED_ON)
        edge_counts["MANUFACTURED_ON"] = self._create_accelerator_process_edges()

        # 2. AIAccelerator → PackagingTech (USES_PACKAGING)
        edge_counts["USES_PACKAGING"] = self._create_accelerator_packaging_edges()

        # 3. AIAccelerator → HBMGeneration (USES_MEMORY)
        edge_counts["USES_MEMORY"] = self._create_accelerator_memory_edges()

        # 4. AIAccelerator → AIModel (CAN_RUN)
        edge_counts["CAN_RUN"] = self._create_accelerator_model_edges()

        # 5. AIAccelerator → AIAccelerator (COMPETES_WITH)
        edge_counts["COMPETES_WITH"] = self._create_competition_edges()

        # 6. ProcessStep → Equipment (REQUIRES_EQUIPMENT)
        edge_counts["REQUIRES_EQUIPMENT"] = self._create_step_equipment_edges()

        # 7. ProcessStep → Material (REQUIRES_MATERIAL)
        edge_counts["REQUIRES_MATERIAL"] = self._create_step_material_edges()

        # 8. ProcessStep → DefectType (CAUSES_DEFECT)
        edge_counts["CAUSES_DEFECT"] = self._create_step_defect_edges()

        # 9. EquipmentFailure → Equipment (FAILURE_OF)
        edge_counts["FAILURE_OF"] = self._create_failure_equipment_edges()

        # 10. ProcessNode → ProcessStep (HAS_PROCESS_STEP)
        edge_counts["HAS_PROCESS_STEP"] = self._create_process_node_step_edges()

        return edge_counts

    def _create_process_node_step_edges(self) -> int:
        """
        모든 선단 공정 ProcessNode를 ProcessStep에 연결합니다.
        반도체 공정 단계(FEOL/MOL/BEOL)는 선단 공정 노드에 공통으로 적용됩니다.
        """
        result = Neo4jClient.run_query(
            """
            MATCH (pn:ProcessNode), (ps:ProcessStep)
            WHERE pn.node_nm IS NOT NULL AND pn.node_nm <= 7
            MERGE (pn)-[:HAS_PROCESS_STEP]->(ps)
            RETURN count(*) as count
            """
        )
        return result[0]["count"] if result else 0

    def _create_accelerator_process_edges(self) -> int:
        """
        acc.process_node 문자열 → MANUFACTURED_ON 관계

        매핑 예: "TSMC N4P" → ProcessNode(key=N4P)
        """
        accs = AIIndustryOntology.get_all_accelerators()
        nodes = SemiconductorOntology.get_all_nodes()
        count = 0

        # Build mapping from process_node string → node key
        node_name_to_key = {}
        for key, node in nodes.items():
            # Full qualified: "TSMC N4P" → match against "N4P"
            node_name_to_key[node.name] = key
            # Also match vendor prefix patterns
            vendor_prefix = node.vendor.value.split()[0]  # "TSMC", "Samsung", "Intel"
            node_name_to_key[f"{vendor_prefix} {node.name}"] = key

        for acc_key, acc in accs.items():
            process_str = acc.process_node
            # Try exact match first, then partial matching
            matched_key = node_name_to_key.get(process_str)
            if not matched_key:
                # Try partial: "TSMC N5 + N6" → take first part "TSMC N5"
                first_part = process_str.split("+")[0].strip().split("(")[0].strip()
                matched_key = node_name_to_key.get(first_part)
            if not matched_key:
                # Try just the node name part: "TSMC N4P" → "N4P"
                parts = process_str.split()
                for part in parts:
                    if part in nodes:
                        matched_key = part
                        break

            if matched_key:
                result = Neo4jClient.run_write(
                    """
                    MATCH (a:AIAccelerator {key: $acc_key})
                    MATCH (p:ProcessNode {key: $node_key})
                    CREATE (a)-[:MANUFACTURED_ON]->(p)
                    """,
                    {"acc_key": acc_key, "node_key": matched_key},
                )
                if result:
                    count += result.get("relationships_created", 0)

        return count

    def _create_accelerator_packaging_edges(self) -> int:
        """acc.packaging 문자열 → USES_PACKAGING 관계"""
        accs = AIIndustryOntology.get_all_accelerators()
        pkgs = SemiconductorOntology.get_all_packaging()
        count = 0

        for acc_key, acc in accs.items():
            pkg_str = acc.packaging
            # Try exact match
            matched_key = None
            if pkg_str in pkgs:
                matched_key = pkg_str
            else:
                # Partial match: "CoWoS-equivalent" → "CoWoS-S"
                for pk in pkgs:
                    if pk.lower() in pkg_str.lower() or pkg_str.lower() in pk.lower():
                        matched_key = pk
                        break

            if matched_key:
                result = Neo4jClient.run_write(
                    """
                    MATCH (a:AIAccelerator {key: $acc_key})
                    MATCH (p:PackagingTech {key: $pkg_key})
                    CREATE (a)-[:USES_PACKAGING]->(p)
                    """,
                    {"acc_key": acc_key, "pkg_key": matched_key},
                )
                if result:
                    count += result.get("relationships_created", 0)

        return count

    def _create_accelerator_memory_edges(self) -> int:
        """acc.memory.type → USES_MEMORY 관계"""
        accs = AIIndustryOntology.get_all_accelerators()
        hbms = AIIndustryOntology.get_all_hbm()
        count = 0

        for acc_key, acc in accs.items():
            mem_type = acc.memory.type  # "HBM3", "HBM3E", "HBM2E"
            if mem_type in hbms:
                result = Neo4jClient.run_write(
                    """
                    MATCH (a:AIAccelerator {key: $acc_key})
                    MATCH (h:HBMGeneration {key: $hbm_key})
                    CREATE (a)-[:USES_MEMORY {
                        stack_count: $stacks,
                        total_capacity_gb: $capacity
                    }]->(h)
                    """,
                    {
                        "acc_key": acc_key,
                        "hbm_key": mem_type,
                        "stacks": acc.memory.stack_count or 0,
                        "capacity": acc.memory.capacity_gb,
                    },
                )
                if result:
                    count += result.get("relationships_created", 0)

        return count

    def _create_accelerator_model_edges(self) -> int:
        """
        가속기가 실행 가능한 AI 모델 관계 (메모리 용량 기반)
        acc.memory.capacity_gb >= model.inference_memory_int8_gb → CAN_RUN
        """
        accs = AIIndustryOntology.get_all_accelerators()
        models = AIIndustryOntology.get_all_models()
        count = 0

        for acc_key, acc in accs.items():
            for model_key, model in models.items():
                if acc.memory.capacity_gb >= model.inference_memory_int8_gb:
                    result = Neo4jClient.run_write(
                        """
                        MATCH (a:AIAccelerator {key: $acc_key})
                        MATCH (m:AIModel {key: $model_key})
                        CREATE (a)-[:CAN_RUN {
                            precision: 'INT8',
                            memory_utilization_pct: $util
                        }]->(m)
                        """,
                        {
                            "acc_key": acc_key,
                            "model_key": model_key,
                            "util": round(
                                model.inference_memory_int8_gb
                                / acc.memory.capacity_gb
                                * 100,
                                1,
                            ),
                        },
                    )
                    if result:
                        count += result.get("relationships_created", 0)

        return count

    def _create_competition_edges(self) -> int:
        """같은 카테고리의 가속기 간 COMPETES_WITH 관계 (양방향)"""
        result = Neo4jClient.run_write(
            """
            MATCH (a:AIAccelerator), (b:AIAccelerator)
            WHERE a.key < b.key
              AND a.category = b.category
            CREATE (a)-[:COMPETES_WITH]->(b)
            CREATE (b)-[:COMPETES_WITH]->(a)
            """
        )
        return result.get("relationships_created", 0) if result else 0

    def _create_step_equipment_edges(self) -> int:
        """
        ProcessStep.equipment_type → Equipment 관계

        매핑: step.equipment_type 문자열에 포함된 카테고리와
              Equipment.category 매칭
        """
        equips = EquipmentKnowledgeBase.get_all_equipment()
        count = 0

        # equipment_type 문자열 → category 매핑
        type_mapping = {
            "LITHOGRAPHY": "LITHOGRAPHY",
            "ETCH": "ETCH",
            "CVD": "DEPOSITION",
            "PECVD": "DEPOSITION",
            "ALD": "DEPOSITION",
            "PVD": "DEPOSITION",
            "EPITAXY": "DEPOSITION",
            "CMP": "CMP",
            "ION_IMPLANT": "ION_IMPLANT",
            "THERMAL": "THERMAL",
            "TEST": "TEST",
            "ECD": "DEPOSITION",
        }

        steps = ProcessFlowOntology.get_full_flow()
        for step_key, step in steps.items():
            # Parse compound equipment types: "ETCH + CVD + CMP"
            equip_types = [t.strip() for t in step.equipment_type.split("+")]
            categories_needed = set()
            for et in equip_types:
                cat = type_mapping.get(et)
                if cat:
                    categories_needed.add(cat)

            for eq_key, eq in equips.items():
                if eq.category.value in categories_needed:
                    result = Neo4jClient.run_write(
                        """
                        MATCH (s:ProcessStep {key: $step_key})
                        MATCH (e:Equipment {key: $eq_key})
                        CREATE (s)-[:REQUIRES_EQUIPMENT]->(e)
                        """,
                        {"step_key": step_key, "eq_key": eq_key},
                    )
                    if result:
                        count += result.get("relationships_created", 0)

        return count

    def _create_step_material_edges(self) -> int:
        """
        Material.process_steps → ProcessStep 관계 (역방향으로 생성)

        매핑: mat.process_steps = ["EUV_LITHOGRAPHY"] →
              ProcessStep에서 equipment_type에 LITHOGRAPHY 포함 + EUV 관련 step
        """
        mats = MaterialsKnowledgeBase.get_all_materials()
        steps = ProcessFlowOntology.get_full_flow()
        count = 0

        # Material process_steps → ProcessStep key 매핑
        material_step_mapping = {
            "EUV_LITHOGRAPHY": ["GATE_OXIDE", "GATE_METAL", "CONTACT", "M0", "M1"],
            "DUV_LITHOGRAPHY": ["STI", "WELL_IMPLANT", "SPACER", "UPPER_METALS"],
            "IMMERSION_LITHOGRAPHY": ["STI", "SPACER", "UPPER_METALS"],
            "CVD": ["SPACER", "CONTACT", "M0", "M1", "UPPER_METALS", "PASSIVATION"],
            "CVD_CHAMBER_CLEAN": ["SPACER", "CONTACT", "PASSIVATION"],
            "ETCH": ["STI", "GATE_METAL", "SPACER", "CONTACT", "M0", "M1"],
            "PECVD": ["PASSIVATION"],
            "EPITAXY": ["SD_EPI"],
            "W_CVD": ["CONTACT"],
            "CONTACT_FILL": ["CONTACT"],
            "WET_ETCH": ["STI", "GATE_OXIDE"],
            "CLEAN": ["STI", "GATE_OXIDE", "GATE_METAL", "CONTACT"],
            "OXIDE_REMOVAL": ["GATE_OXIDE"],
            "SC1_CLEAN": ["STI", "GATE_OXIDE"],
            "SC2_CLEAN": ["STI", "GATE_OXIDE"],
            "SPM_CLEAN": ["STI"],
            "CMP_STI": ["STI"],
            "CMP_ILD": ["CONTACT", "M0"],
            "CMP_OXIDE": ["CONTACT", "M0", "M1"],
            "PVD_BARRIER": ["CONTACT", "M0"],
            "PVD_LINER": ["CONTACT", "M0", "M1"],
            "CONTACT": ["CONTACT"],
            "EUV_PELLICLE": [],
        }

        for mat_key, mat in mats.items():
            target_steps = set()
            for proc_step_name in mat.process_steps:
                mapped = material_step_mapping.get(proc_step_name, [])
                target_steps.update(mapped)

            for step_key in target_steps:
                if step_key in steps:
                    result = Neo4jClient.run_write(
                        """
                        MATCH (s:ProcessStep {key: $step_key})
                        MATCH (m:Material {key: $mat_key})
                        CREATE (s)-[:REQUIRES_MATERIAL]->(m)
                        """,
                        {"step_key": step_key, "mat_key": mat_key},
                    )
                    if result:
                        count += result.get("relationships_created", 0)

        return count

    def _create_step_defect_edges(self) -> int:
        """
        DefectType.affected_process_steps → ProcessStep 관계

        매핑: defect.affected_process_steps = ["CVD", "PVD", "ETCH"] →
              해당 equipment_type을 사용하는 ProcessStep과 연결
        """
        defects = FailureModeOntology.get_all_defect_types()
        steps = ProcessFlowOntology.get_full_flow()
        count = 0

        # affected_process_step 키워드 → ProcessStep key 매핑
        defect_step_mapping = {
            "CVD": ["SPACER", "CONTACT", "M0", "M1", "PASSIVATION"],
            "PVD": ["GATE_METAL", "SILICIDE", "CONTACT", "M0"],
            "ETCH": ["STI", "GATE_METAL", "SPACER", "CONTACT", "M0", "M1"],
            "LITHOGRAPHY": ["GATE_METAL", "CONTACT", "M0", "M1"],
            "CMP": ["STI", "CONTACT", "M0", "M1"],
            "CONTACT": ["CONTACT"],
            "VIA_ETCH": ["M0", "M1", "UPPER_METALS"],
            "W_CVD": ["CONTACT"],
            "ALD": ["GATE_OXIDE"],
        }

        for defect_key, defect in defects.items():
            target_steps = set()
            for proc_name in defect.affected_process_steps:
                mapped = defect_step_mapping.get(proc_name, [])
                target_steps.update(mapped)

            for step_key in target_steps:
                if step_key in steps:
                    result = Neo4jClient.run_write(
                        """
                        MATCH (s:ProcessStep {key: $step_key})
                        MATCH (d:DefectType {key: $defect_key})
                        CREATE (s)-[:CAUSES_DEFECT {
                            kill_ratio_pct: $kill_ratio
                        }]->(d)
                        """,
                        {
                            "step_key": step_key,
                            "defect_key": defect_key,
                            "kill_ratio": defect.kill_ratio_pct,
                        },
                    )
                    if result:
                        count += result.get("relationships_created", 0)

        return count

    def _create_failure_equipment_edges(self) -> int:
        """
        EquipmentFailure.equipment_type → Equipment 관계

        매핑: fm.equipment_type = "LITHOGRAPHY" → category=LITHOGRAPHY인 장비
        """
        modes = FailureModeOntology.get_all_failure_modes()
        equips = EquipmentKnowledgeBase.get_all_equipment()
        count = 0

        for fm_key, fm in modes.items():
            for eq_key, eq in equips.items():
                if eq.category.value == fm.equipment_type:
                    result = Neo4jClient.run_write(
                        """
                        MATCH (f:EquipmentFailure {key: $fm_key})
                        MATCH (e:Equipment {key: $eq_key})
                        CREATE (f)-[:FAILURE_OF]->(e)
                        """,
                        {"fm_key": fm_key, "eq_key": eq_key},
                    )
                    if result:
                        count += result.get("relationships_created", 0)

        return count
