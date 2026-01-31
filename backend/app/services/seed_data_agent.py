"""
Ontology-Powered Seed Data Agent

도메인 온톨로지 기반 시드 데이터 자동 생성 에이전트.
사용자가 시나리오를 선택하면, 온톨로지의 실제 산업 데이터를 기반으로
현실적인 시드 데이터를 자동 생성합니다.

시나리오 예시:
- "3nm 파운드리 Fab 운영" → TSMC N3E 공정 기반 장비/재료/WIP 생성
- "AI 가속기 HBM 패키징" → CoWoS/HBM3 기반 공급망/수율 데이터 생성
- "7nm 레거시 팹 최적화" → 성숙 공정 기반 수율/장비 데이터 생성
"""

import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from app.ontology import (
    SemiconductorOntology,
    AIIndustryOntology,
    MaterialsKnowledgeBase,
    EquipmentKnowledgeBase,
    ProcessFlowOntology,
    FailureModeOntology,
)


# ============================================================
# Scenario Templates
# ============================================================

@dataclass
class FabScenario:
    """Fab 시나리오 정의"""
    scenario_id: str
    name: str
    name_kr: str
    description: str
    process_node: str              # 온톨로지 노드 키 (e.g., "TSMC_N3E")
    target_product: str            # 생산 제품 유형
    wspm: int                      # Wafer Starts Per Month
    equipment_count: int           # 주요 장비 수
    wip_lots: int                  # WIP Lot 수
    supply_chain_tiers: int        # 공급망 깊이
    history_days: int              # 생성할 이력 기간 (일)
    tags: list[str] = field(default_factory=list)


SCENARIOS = {
    "advanced_3nm_foundry": FabScenario(
        scenario_id="advanced_3nm_foundry",
        name="Advanced 3nm Foundry",
        name_kr="첨단 3nm 파운드리",
        description="TSMC N3E 기반 최첨단 파운드리 운영 시나리오. "
                    "EUV 리소그래피, HBM3 패키징, AI 가속기 생산.",
        process_node="TSMC_N3E",
        target_product="AI_ACCELERATOR",
        wspm=50000,
        equipment_count=20,
        wip_lots=30,
        supply_chain_tiers=3,
        history_days=30,
        tags=["EUV", "AI", "HBM3", "CoWoS"],
    ),
    "ai_chip_packaging": FabScenario(
        scenario_id="ai_chip_packaging",
        name="AI Chip Advanced Packaging",
        name_kr="AI 칩 어드밴스드 패키징",
        description="CoWoS-L 기반 AI 가속기 패키징 시나리오. "
                    "HBM3E 스택, 인터포저, 2.5D 패키징 공정.",
        process_node="TSMC_N3P",
        target_product="AI_ACCELERATOR_PACKAGE",
        wspm=20000,
        equipment_count=15,
        wip_lots=20,
        supply_chain_tiers=3,
        history_days=30,
        tags=["CoWoS", "HBM3E", "2.5D", "Interposer"],
    ),
    "mature_7nm_optimization": FabScenario(
        scenario_id="mature_7nm_optimization",
        name="Mature 7nm Fab Optimization",
        name_kr="성숙 7nm 팹 최적화",
        description="TSMC N7 기반 성숙 공정 팹 수율 최적화 시나리오. "
                    "DUV 리소그래피, 높은 수율 목표, 비용 절감 중심.",
        process_node="TSMC_N7",
        target_product="MOBILE_SOC",
        wspm=80000,
        equipment_count=25,
        wip_lots=50,
        supply_chain_tiers=2,
        history_days=60,
        tags=["DUV", "Mobile", "Cost Optimization"],
    ),
    "samsung_gaafet_rampup": FabScenario(
        scenario_id="samsung_gaafet_rampup",
        name="Samsung GAA-FET Ramp-up",
        name_kr="삼성 GAA-FET 램프업",
        description="Samsung SF3 GAA-FET 공정 양산 램프업 시나리오. "
                    "새 공정 도입에 따른 수율 개선 과정 시뮬레이션.",
        process_node="Samsung_SF3",
        target_product="HPC_CHIP",
        wspm=30000,
        equipment_count=18,
        wip_lots=25,
        supply_chain_tiers=3,
        history_days=45,
        tags=["GAA", "Ramp-up", "Yield Learning"],
    ),
    "intel_18a_development": FabScenario(
        scenario_id="intel_18a_development",
        name="Intel 18A Development Fab",
        name_kr="인텔 18A 개발팹",
        description="Intel 18A RibbonFET + PowerVia 개발 단계 시나리오. "
                    "R&D 중심, 낮은 초기 수율, 공정 안정화.",
        process_node="Intel_18A",
        target_product="SERVER_CPU",
        wspm=10000,
        equipment_count=12,
        wip_lots=15,
        supply_chain_tiers=2,
        history_days=30,
        tags=["RibbonFET", "PowerVia", "R&D"],
    ),
}


# ============================================================
# Seed Data Generator
# ============================================================

class SeedDataAgent:
    """
    온톨로지 기반 시드 데이터 생성 에이전트.

    도메인 지식을 기반으로 현실적인 시드 데이터를 생성합니다.
    사용자가 직접 값을 입력할 필요 없이, 시나리오를 선택하면
    산업 표준에 맞는 데이터가 자동으로 생성됩니다.
    """

    def __init__(self, scenario_id: str):
        if scenario_id not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_id}. "
                             f"Available: {list(SCENARIOS.keys())}")
        self.scenario = SCENARIOS[scenario_id]
        self.node_info = SemiconductorOntology.get_node(self.scenario.process_node)
        self._now = datetime.utcnow()

    @classmethod
    def list_scenarios(cls) -> list[dict]:
        """사용 가능한 시나리오 목록"""
        return [
            {
                "scenario_id": s.scenario_id,
                "name": s.name,
                "name_kr": s.name_kr,
                "description": s.description,
                "process_node": s.process_node,
                "target_product": s.target_product,
                "tags": s.tags,
            }
            for s in SCENARIOS.values()
        ]

    def generate_all(self) -> dict:
        """전체 시드 데이터 생성"""
        return {
            "scenario": {
                "id": self.scenario.scenario_id,
                "name": self.scenario.name,
                "process_node": self.scenario.process_node,
            },
            "process_nodes": self.generate_process_nodes(),
            "ip_blocks": self.generate_ip_blocks(),
            "fab_equipment": self.generate_fab_equipment(),
            "wip_items": self.generate_wip_items(),
            "materials": self.generate_materials(),
            "suppliers": self.generate_suppliers(),
            "wafer_records": self.generate_wafer_records(),
            "yield_events": self.generate_yield_events(),
            "summary": self._generate_summary(),
        }

    # ----------------------------------------------------------
    # Process Nodes
    # ----------------------------------------------------------
    def generate_process_nodes(self) -> list[dict]:
        """온톨로지 기반 공정 노드 시드 데이터"""
        nodes_data = []
        all_nodes = SemiconductorOntology.get_all_nodes()

        for key, node in all_nodes.items():
            # 공정별 area scaling factor 계산
            scaling_factor = node.node_nm / 3.0

            nodes_data.append({
                "name": f"{node.node_nm}nm ({node.vendor.value})",
                "node_nm": node.node_nm,
                "wafer_cost": node.wafer_cost_usd,
                "defect_density": round(0.08 + (node.node_nm - 3) * 0.005, 4),
                "base_core_area": round(0.5 * scaling_factor, 3),
                "cache_density": round(0.15 * scaling_factor, 3),
                "io_area_per_lane": round(0.08 * scaling_factor, 3),
                "scaling_factor": round(scaling_factor, 3),
                "power_density": round(120 / scaling_factor, 1),
                "max_frequency_ghz": node.max_frequency_ghz if hasattr(node, 'max_frequency_ghz') else round(4.0 / scaling_factor * 1.2, 1),
                "is_active": True,
                "_ontology_key": key,
                "_vendor": node.vendor.value,
            })

        return nodes_data

    # ----------------------------------------------------------
    # IP Blocks
    # ----------------------------------------------------------
    def generate_ip_blocks(self) -> list[dict]:
        """AI 산업 온톨로지 기반 IP 블록"""
        ip_blocks = []
        node_nm = self.node_info.node_nm if self.node_info else 3

        # CPU cores
        ip_blocks.extend([
            {
                "name": "Cortex-X4 Performance Core",
                "type": "CPU",
                "vendor": "Arm",
                "version": "v9.2",
                "area_mm2": round(0.8 * (node_nm / 3.0), 2),
                "power_mw": round(1200 * (node_nm / 3.0), 0),
                "performance_metric": round(4.0 / (node_nm / 3.0), 1),
                "performance_unit": "GHz",
                "silicon_proven": node_nm >= 4,
                "description": "High-performance Cortex-X4 core (Armv9.2-A)",
            },
            {
                "name": "Cortex-A720 Efficiency Core",
                "type": "CPU",
                "vendor": "Arm",
                "version": "v9.2",
                "area_mm2": round(0.3 * (node_nm / 3.0), 2),
                "power_mw": round(300 * (node_nm / 3.0), 0),
                "performance_metric": round(3.0 / (node_nm / 3.0), 1),
                "performance_unit": "GHz",
                "silicon_proven": True,
                "description": "Efficiency core (Armv9.2-A)",
            },
        ])

        # GPU
        ip_blocks.append({
            "name": "Immortalis-G720 GPU",
            "type": "GPU",
            "vendor": "Arm",
            "version": "5th Gen",
            "area_mm2": round(3.2 * (node_nm / 3.0), 2),
            "power_mw": round(3500 * (node_nm / 3.0), 0),
            "performance_metric": 2.8,
            "performance_unit": "TFLOPS",
            "silicon_proven": node_nm >= 4,
            "description": "Arm Immortalis-G720 GPU (ray tracing support)",
        })

        # NPU - AI 가속기 온톨로지 기반
        accelerators = AIIndustryOntology.get_all_accelerators()
        if "H100_SXM" in accelerators:
            h100 = accelerators["H100_SXM"]
            ip_blocks.append({
                "name": "Custom NPU (H100-class)",
                "type": "NPU",
                "vendor": "Custom",
                "version": "v2.0",
                "area_mm2": round(4.5 * (node_nm / 3.0), 2),
                "power_mw": round(2000 * (node_nm / 3.0), 0),
                "performance_metric": round(h100.compute.int8_tops / 8, 0),
                "performance_unit": "TOPS",
                "silicon_proven": False,
                "description": f"Custom NPU - INT8 {round(h100.compute.int8_tops / 8, 0)} TOPS "
                               f"(reference: {h100.name} @ {h100.compute.int8_tops} TOPS)",
            })

        # Memory Controller
        hbm_specs = AIIndustryOntology.get_all_hbm()
        hbm3_bw = 819.2  # default
        if "HBM3" in hbm_specs:
            hbm3_bw = hbm_specs["HBM3"].bandwidth_per_stack_gbps

        ip_blocks.append({
            "name": "HBM3 Memory Controller",
            "type": "MEMORY_CTRL",
            "vendor": "Custom",
            "version": "v1.0",
            "area_mm2": round(2.8 * (node_nm / 3.0), 2),
            "power_mw": round(800 * (node_nm / 3.0), 0),
            "performance_metric": hbm3_bw,
            "performance_unit": "GB/s",
            "silicon_proven": False,
            "description": f"HBM3 PHY + Controller ({hbm3_bw} GB/s per stack)",
        })

        # SERDES / PCIe
        ip_blocks.append({
            "name": "PCIe Gen5 x16 Controller",
            "type": "SERDES",
            "vendor": "Synopsys",
            "version": "5.0",
            "area_mm2": round(1.5 * (node_nm / 3.0), 2),
            "power_mw": round(500 * (node_nm / 3.0), 0),
            "performance_metric": 64.0,
            "performance_unit": "GT/s",
            "silicon_proven": True,
            "description": "PCIe Gen5 x16 (64 GT/s, 128 GB/s bidirectional)",
        })

        # CXL
        ip_blocks.append({
            "name": "CXL 3.0 Controller",
            "type": "SERDES",
            "vendor": "Synopsys",
            "version": "3.0",
            "area_mm2": round(1.2 * (node_nm / 3.0), 2),
            "power_mw": round(400 * (node_nm / 3.0), 0),
            "performance_metric": 64.0,
            "performance_unit": "GT/s",
            "silicon_proven": False,
            "description": "CXL 3.0 controller for memory expansion and coherent interconnect",
        })

        return ip_blocks

    # ----------------------------------------------------------
    # Fab Equipment
    # ----------------------------------------------------------
    def generate_fab_equipment(self) -> list[dict]:
        """장비 온톨로지 기반 Fab 장비 목록"""
        equipment_list = []
        equip_db = EquipmentKnowledgeBase.get_all_equipment()
        process_steps = ProcessFlowOntology.get_ordered_flow()
        node_nm = self.node_info.node_nm if self.node_info else 3

        # 장비 타입별 매핑
        type_to_equip = {
            "LITHOGRAPHY": [],
            "ETCHER": [],
            "CVD": [],
            "PVD": [],
            "CMP": [],
        }

        for key, eq in equip_db.items():
            cat = eq.category.value
            if cat in type_to_equip:
                type_to_equip[cat].append(eq)

        # Bay 할당 및 장비 인스턴스 생성
        bay_map = {
            "LITHOGRAPHY": "Bay-A (Photo)",
            "ETCHER": "Bay-B (Etch)",
            "CVD": "Bay-C (Deposition)",
            "PVD": "Bay-C (Deposition)",
            "CMP": "Bay-D (Planar)",
            "IMPLANT": "Bay-E (Implant)",
            "DIFFUSION": "Bay-F (Diffusion)",
            "METROLOGY": "Bay-G (Metrology)",
            "CLEAN": "Bay-H (Wet Clean)",
        }

        equip_counter = {}
        target_count = self.scenario.equipment_count

        # 장비 유형별 비율 (노드에 따라 리소 비중 조정)
        if node_nm <= 5:
            type_ratios = {
                "LITHOGRAPHY": 0.20, "ETCHER": 0.20, "CVD": 0.15,
                "PVD": 0.10, "CMP": 0.10, "IMPLANT": 0.05,
                "DIFFUSION": 0.05, "METROLOGY": 0.10, "CLEAN": 0.05,
            }
        else:
            type_ratios = {
                "LITHOGRAPHY": 0.15, "ETCHER": 0.20, "CVD": 0.15,
                "PVD": 0.10, "CMP": 0.10, "IMPLANT": 0.08,
                "DIFFUSION": 0.07, "METROLOGY": 0.08, "CLEAN": 0.07,
            }

        for eq_type, ratio in type_ratios.items():
            count = max(1, round(target_count * ratio))
            equip_counter[eq_type] = count

        idx = 0
        for eq_type, count in equip_counter.items():
            equips_for_type = type_to_equip.get(eq_type, [])
            ref_equip = equips_for_type[0] if equips_for_type else None

            for i in range(count):
                idx += 1
                eq_id = f"{eq_type[:4]}-{i + 1:02d}"
                base_oee = random.uniform(78, 95)

                # 온톨로지 참조 데이터
                if ref_equip:
                    wph = ref_equip.throughput_wph * random.uniform(0.9, 1.1)
                    mtbf = ref_equip.mtbf_hours * random.uniform(0.85, 1.15)
                    mttr = ref_equip.mttr_hours * random.uniform(0.9, 1.2)
                    name = f"{ref_equip.name} #{i + 1}"
                    specs = {
                        "model": ref_equip.name,
                        "vendor": ref_equip.vendor.name,
                        "generation": ref_equip.generation if hasattr(ref_equip, 'generation') else "Current",
                    }
                else:
                    wph = random.uniform(50, 200)
                    mtbf = random.uniform(500, 2000)
                    mttr = random.uniform(2, 12)
                    name = f"{eq_type} Unit #{i + 1}"
                    specs = {"model": "Generic", "vendor": "Various"}

                # 상태 분배 (대부분 RUNNING, 일부 IDLE/MAINTENANCE)
                status_roll = random.random()
                if status_roll < 0.6:
                    status = "RUNNING"
                elif status_roll < 0.85:
                    status = "IDLE"
                elif status_roll < 0.95:
                    status = "MAINTENANCE"
                else:
                    status = "DOWN"

                last_maint = self._now - timedelta(days=random.randint(1, 30))
                next_maint = self._now + timedelta(days=random.randint(7, 60))

                # 공정 능력 (노드 의존)
                process_capabilities = []
                for step in process_steps:
                    if step.equipment_type.upper() == eq_type:
                        process_capabilities.append({
                            "step_id": step.step_id,
                            "step_name": step.name,
                            "qualified": random.random() > 0.1,
                        })

                equipment_list.append({
                    "equipment_id": eq_id,
                    "name": name,
                    "equipment_type": eq_type,
                    "bay": bay_map.get(eq_type, "Bay-X (Other)"),
                    "capacity_wph": round(wph, 1),
                    "oee": round(base_oee, 1),
                    "availability": round(base_oee * random.uniform(0.98, 1.02), 1),
                    "performance": round(base_oee * random.uniform(0.95, 1.05), 1),
                    "quality": round(min(99.5, base_oee * random.uniform(1.0, 1.08)), 1),
                    "mtbf_hours": round(mtbf, 0),
                    "mttr_hours": round(mttr, 1),
                    "status": status,
                    "last_maintenance": last_maint.isoformat(),
                    "next_maintenance": next_maint.isoformat(),
                    "specs": specs,
                    "process_capabilities": process_capabilities,
                })

        return equipment_list

    # ----------------------------------------------------------
    # WIP Items
    # ----------------------------------------------------------
    def generate_wip_items(self) -> list[dict]:
        """WIP Lot 데이터"""
        wip_list = []
        process_steps = ProcessFlowOntology.get_ordered_flow()
        total_steps = len(process_steps)
        products = self._get_product_mix()

        for i in range(self.scenario.wip_lots):
            product = random.choice(products)
            current_step = random.randint(1, total_steps)
            current_op = process_steps[current_step - 1] if current_step <= total_steps else process_steps[-1]
            priority = random.choices([1, 3, 5, 7, 10], weights=[5, 10, 50, 25, 10])[0]

            days_in_fab = int(current_step / total_steps * 25)
            start_time = self._now - timedelta(days=days_in_fab, hours=random.randint(0, 23))
            remaining_days = int((total_steps - current_step) / total_steps * 25)
            estimated_completion = self._now + timedelta(days=remaining_days)

            # 공정 라우트 생성
            route = []
            for step in process_steps:
                eq_type = step.equipment_type.upper()
                route.append({
                    "step": step.order,
                    "operation": step.name,
                    "equipment_type": eq_type,
                    "target_bay": f"Bay-{chr(65 + (step.order % 8))}",
                })

            status_roll = random.random()
            if status_roll < 0.65:
                status = "QUEUED"
            elif status_roll < 0.90:
                status = "PROCESSING"
            elif status_roll < 0.97:
                status = "HOLD"
            else:
                status = "COMPLETE"

            wip_list.append({
                "lot_id": f"LOT-{product['code']}-{i + 1:04d}",
                "product_id": product["id"],
                "wafer_count": random.choice([25, 25, 25, 13]),
                "current_step": current_step,
                "total_steps": total_steps,
                "current_operation": current_op.name,
                "priority": priority,
                "due_date": (self._now + timedelta(days=random.randint(5, 30))).isoformat(),
                "estimated_completion": estimated_completion.isoformat(),
                "current_bay": f"Bay-{chr(65 + (current_step % 8))}",
                "status": status,
                "hold_reason": "Engineering Hold - Metrology Review" if status == "HOLD" else None,
                "start_time": start_time.isoformat(),
                "route": route,
            })

        return wip_list

    # ----------------------------------------------------------
    # Materials (Ontology-powered)
    # ----------------------------------------------------------
    def generate_materials(self) -> list[dict]:
        """소재 온톨로지 기반 자재 데이터"""
        materials_list = []
        ont_materials = MaterialsKnowledgeBase.get_all_materials()

        for key, mat in ont_materials.items():
            # 카테고리 매핑
            cat_map = {
                "PHOTORESIST": "CHEMICAL",
                "ETCH_GAS": "GAS",
                "DEPOSITION_GAS": "GAS",
                "ETCH_CHEMICAL": "CHEMICAL",
                "CMP_CONSUMABLE": "CHEMICAL",
                "EUV_MATERIAL": "EQUIPMENT",
                "DEPOSITION_TARGET": "SPARE_PART",
            }
            category = cat_map.get(mat.category.value, "CHEMICAL")

            # 리드타임 기반 적정 재고 산출
            lead_time = mat.lead_time_weeks * 7
            daily_consumption = round(random.uniform(0.5, 5.0), 2)
            safety_stock = round(daily_consumption * lead_time * 0.5, 1)
            reorder_point = round(daily_consumption * lead_time * 0.75, 1)
            max_stock = round(daily_consumption * lead_time * 2.0, 1)
            current_stock = round(random.uniform(reorder_point * 0.8, max_stock * 0.9), 1)

            # 단가 (online 대비 현실적 추정)
            unit_cost = round(random.uniform(50, 50000) * (1 if mat.criticality.value != "CRITICAL" else 3), 2)

            materials_list.append({
                "material_id": f"MAT-{key}",
                "name": mat.name,
                "category": category,
                "current_stock": current_stock,
                "unit": "EA" if category in ["EQUIPMENT", "SPARE_PART"] else "KG",
                "safety_stock": safety_stock,
                "reorder_point": reorder_point,
                "max_stock": max_stock,
                "unit_cost": unit_cost,
                "lead_time_days": lead_time,
                "lead_time_min": int(lead_time * 0.7),
                "lead_time_max": int(lead_time * 1.5),
                "criticality": mat.criticality.value,
                "substitute_available": False,
                "daily_consumption": daily_consumption,
                "monthly_consumption": round(daily_consumption * 30, 1),
                "specifications": {
                    "description": mat.description,
                    "purity": mat.typical_purity if hasattr(mat, 'typical_purity') else "N/A",
                    "supply_risk": mat.supply_risk.value,
                    "geographic_concentration": mat.geographic_concentration,
                    "major_suppliers": mat.major_suppliers,
                },
                "_ontology_key": key,
            })

        # 추가 필수 자재: Si 웨이퍼
        node_nm = self.node_info.node_nm if self.node_info else 3
        wafer_cost = self.node_info.wafer_cost_usd if self.node_info else 16000
        materials_list.append({
            "material_id": "MAT-SI_WAFER_300MM",
            "name": f"300mm Si Wafer ({node_nm}nm grade)",
            "category": "WAFER",
            "current_stock": round(self.scenario.wspm * 0.3),
            "unit": "EA",
            "safety_stock": round(self.scenario.wspm * 0.2),
            "reorder_point": round(self.scenario.wspm * 0.4),
            "max_stock": round(self.scenario.wspm * 1.5),
            "unit_cost": round(wafer_cost * 0.02, 2),  # bare wafer cost
            "lead_time_days": 56,
            "lead_time_min": 42,
            "lead_time_max": 84,
            "criticality": "CRITICAL",
            "substitute_available": False,
            "daily_consumption": round(self.scenario.wspm / 30, 1),
            "monthly_consumption": float(self.scenario.wspm),
        })

        return materials_list

    # ----------------------------------------------------------
    # Suppliers
    # ----------------------------------------------------------
    def generate_suppliers(self) -> list[dict]:
        """온톨로지 기반 공급업체"""
        suppliers = []
        equip_db = EquipmentKnowledgeBase.get_all_equipment()

        # Tier-1: 장비 공급업체
        vendor_set = set()
        for eq in equip_db.values():
            vendor_set.add(eq.vendor.name)

        for vendor_name in vendor_set:
            sid = f"SUP-{vendor_name.upper().replace(' ', '_')[:10]}"
            country_map = {
                "ASML": ("Netherlands", "Europe"),
                "LAM_RESEARCH": ("United States", "North America"),
                "TEL": ("Japan", "Asia"),
                "APPLIED_MATERIALS": ("United States", "North America"),
                "KLA": ("United States", "North America"),
            }
            country, region = country_map.get(
                vendor_name.upper().replace(" ", "_"),
                ("United States", "North America")
            )

            suppliers.append({
                "supplier_id": sid,
                "name": vendor_name.replace("_", " ").title(),
                "tier": "TIER_1",
                "country": country,
                "region": region,
                "lead_time_days": random.randint(60, 365),
                "on_time_delivery_rate": round(random.uniform(85, 98), 1),
                "quality_rating": round(random.uniform(88, 99), 1),
                "risk_score": round(random.uniform(10, 35), 1),
                "geopolitical_exposure": "LOW" if region == "North America" else "MEDIUM",
                "contract_status": "ACTIVE",
                "certifications": ["ISO 9001", "ISO 14001", "SEMI S2"],
            })

        # Tier-2: 소재 공급업체
        ont_materials = MaterialsKnowledgeBase.get_all_materials()
        material_suppliers_set = set()
        for mat in ont_materials.values():
            for sup in mat.major_suppliers[:2]:
                material_suppliers_set.add((sup, mat.geographic_concentration))

        for sup_name, geo in material_suppliers_set:
            sid = f"SUP-{sup_name.upper().replace(' ', '_')[:10]}"
            is_japan = "Japan" in geo
            is_korea = "Korea" in geo

            suppliers.append({
                "supplier_id": sid,
                "name": sup_name,
                "tier": "TIER_2",
                "country": "Japan" if is_japan else ("South Korea" if is_korea else "Various"),
                "region": "Asia",
                "lead_time_days": random.randint(14, 90),
                "on_time_delivery_rate": round(random.uniform(88, 97), 1),
                "quality_rating": round(random.uniform(90, 99), 1),
                "risk_score": round(random.uniform(15, 50), 1),
                "geopolitical_exposure": "HIGH" if is_japan else "MEDIUM",
                "contract_status": "ACTIVE",
                "certifications": ["ISO 9001"],
            })

        # Tier-3: 원자재 공급
        raw_material_suppliers = [
            ("Shin-Etsu Chemical", "Japan", "HIGH"),
            ("SUMCO", "Japan", "HIGH"),
            ("Siltronic", "Germany", "MEDIUM"),
            ("SK Siltron", "South Korea", "MEDIUM"),
            ("Air Liquide", "France", "LOW"),
            ("Linde", "Germany", "LOW"),
        ]

        for name, country, geo_risk in raw_material_suppliers:
            sid = f"SUP-{name.upper().replace(' ', '_').replace('-', '_')[:10]}"
            suppliers.append({
                "supplier_id": sid,
                "name": name,
                "tier": "TIER_3",
                "country": country,
                "region": "Asia" if country in ["Japan", "South Korea"] else "Europe",
                "lead_time_days": random.randint(30, 120),
                "on_time_delivery_rate": round(random.uniform(90, 98), 1),
                "quality_rating": round(random.uniform(92, 99), 1),
                "risk_score": round(random.uniform(20, 60), 1),
                "geopolitical_exposure": geo_risk,
                "contract_status": "ACTIVE",
                "certifications": ["ISO 9001", "ISO 14001"],
            })

        return suppliers

    # ----------------------------------------------------------
    # Wafer Records (Historical)
    # ----------------------------------------------------------
    def generate_wafer_records(self) -> list[dict]:
        """이력 웨이퍼 데이터 (온톨로지 기반 현실적 수율/센서 데이터)"""
        records = []
        process_steps = ProcessFlowOntology.get_ordered_flow()
        failure_modes = FailureModeOntology.get_all_defect_types()
        node_nm = self.node_info.node_nm if self.node_info else 3
        base_yield = self.node_info.typical_yield_pct if self.node_info else 80.0
        products = self._get_product_mix()

        # 수율 학습 곡선 시뮬레이션
        history_days = self.scenario.history_days

        # 일별 배치 생성 (축약: 일별 대표 웨이퍼 5장)
        total_records = min(history_days * 5, 500)

        for i in range(total_records):
            day_offset = int(i / 5)
            process_date = self._now - timedelta(days=history_days - day_offset)

            # 수율 학습 곡선: 초기 낮고 점진 개선
            learning_factor = min(1.0, 0.85 + 0.15 * (day_offset / max(history_days, 1)))
            daily_yield = base_yield * learning_factor + random.gauss(0, 1.5)
            daily_yield = max(50.0, min(99.0, daily_yield))

            product = random.choice(products)
            step = random.choice(process_steps)
            lot_num = (i // 25) + 1
            wafer_num = (i % 25) + 1

            # 다이 계산 (온톨로지 기반)
            die_area = product["die_area_mm2"]
            gross_die = SemiconductorOntology.calculate_gross_die_per_wafer(
                die_area ** 0.5, die_area ** 0.5
            )
            good_die = int(gross_die * daily_yield / 100)
            defect_count = max(0, int(random.gauss(3, 2)))

            # 센서 데이터 (공정 단계별)
            sensor_data = self._generate_sensor_data(step)
            metrology_data = self._generate_metrology_data(step, node_nm)

            # 결함 맵
            defect_map = []
            for _ in range(defect_count):
                defect_type = random.choice(list(failure_modes.values()))
                defect_map.append({
                    "x": round(random.uniform(-150, 150), 1),
                    "y": round(random.uniform(-150, 150), 1),
                    "type": defect_type.name,
                    "size_nm": round(random.uniform(10, 500), 0),
                    "kill_probability": defect_type.kill_ratio_pct / 100,
                })

            records.append({
                "wafer_id": f"W-{lot_num:04d}-{wafer_num:02d}",
                "lot_id": f"LOT-{product['code']}-{lot_num:04d}",
                "product_id": product["id"],
                "process_step": step.order,
                "equipment_id": f"{step.equipment_type.upper()[:4]}-{random.randint(1, 3):02d}",
                "yield_percent": round(daily_yield, 2),
                "die_count": gross_die,
                "good_die_count": good_die,
                "defect_count": defect_count,
                "sensor_data": sensor_data,
                "metrology_data": metrology_data,
                "defect_map": defect_map,
                "process_start": process_date.isoformat(),
                "process_end": (process_date + timedelta(hours=random.uniform(0.5, 4))).isoformat(),
            })

        return records

    # ----------------------------------------------------------
    # Yield Events
    # ----------------------------------------------------------
    def generate_yield_events(self) -> list[dict]:
        """온톨로지 기반 수율 이벤트"""
        events = []
        failure_modes = FailureModeOntology.get_all_defect_types()
        process_steps = ProcessFlowOntology.get_ordered_flow()

        # 시나리오에 따른 이벤트 수
        num_events = random.randint(3, 8)

        for i in range(num_events):
            days_ago = random.randint(1, self.scenario.history_days)
            detected_at = self._now - timedelta(days=days_ago)

            # 결함 유형 선택
            defect = random.choice(list(failure_modes.values()))
            step = random.choice(process_steps)

            # 근본 원인
            eq_type = step.equipment_type.upper()
            eq_failure_list = FailureModeOntology.get_failure_modes_for_equipment(eq_type)
            root_cause_type = random.choice(["EQUIPMENT", "MATERIAL", "PROCESS"])

            root_causes = [{
                "type": root_cause_type,
                "entity_id": f"{eq_type[:4]}-{random.randint(1, 3):02d}",
                "probability": round(random.uniform(0.5, 0.95), 2),
                "description": defect.common_causes[0] if defect.common_causes else "Unknown",
                "evidence": [
                    f"SPC chart shows {step.name} out-of-spec",
                    f"Defect type: {defect.name} ({defect.name_kr})",
                    f"Affected wafers share common equipment path",
                ],
            }]

            # 상태 (오래된 이벤트는 해결됨)
            if days_ago > 14:
                status = "RESOLVED"
            elif days_ago > 7:
                status = random.choice(["ROOT_CAUSE_IDENTIFIED", "RESOLVED"])
            else:
                status = random.choice(["OPEN", "INVESTIGATING"])

            severity_map = {
                "CRITICAL": (5.0, 15.0),
                "HIGH": (3.0, 7.0),
                "MEDIUM": (1.0, 4.0),
                "LOW": (0.5, 2.0),
            }
            sev = defect.severity.value
            drop_range = severity_map.get(sev, (1.0, 5.0))
            yield_drop = round(random.uniform(*drop_range), 1)

            recommendations = []
            if eq_failure_list:
                fm = eq_failure_list[0]
                recommendations = [
                    fm.corrective_action,
                    fm.preventive_measure,
                ]
            recommendations.append(f"Increase {step.name} monitoring frequency")

            events.append({
                "event_id": f"YE-{self._now.strftime('%Y%m')}-{i + 1:03d}",
                "title": f"{defect.name_kr} 발생 - {step.name} 공정",
                "description": (
                    f"{step.name} 공정에서 {defect.name} ({defect.name_kr}) 결함 발생. "
                    f"수율 {yield_drop}% 하락. 주요 원인: {defect.common_causes[0] if defect.common_causes else 'TBD'}"
                ),
                "status": status,
                "severity": sev,
                "yield_drop_percent": yield_drop,
                "affected_wafer_count": random.randint(25, 200),
                "process_step": step.order,
                "equipment_ids": [f"{eq_type[:4]}-{random.randint(1, 3):02d}"],
                "root_causes": root_causes,
                "analysis_summary": (
                    f"Root cause analysis: {defect.name} detected at {step.name} step. "
                    f"Primary suspect: {root_cause_type.lower()} related issue."
                ),
                "recommendations": recommendations,
                "detected_at": detected_at.isoformat(),
                "resolved_at": (detected_at + timedelta(days=random.randint(1, 7))).isoformat() if status == "RESOLVED" else None,
            })

        return events

    # ----------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------
    def _get_product_mix(self) -> list[dict]:
        """시나리오별 제품 믹스"""
        product_map = {
            "AI_ACCELERATOR": [
                {"id": "PROD-AI-ACC-001", "code": "AIA", "name": "AI Accelerator (Training)", "die_area_mm2": 800},
                {"id": "PROD-AI-ACC-002", "code": "AIB", "name": "AI Accelerator (Inference)", "die_area_mm2": 400},
            ],
            "AI_ACCELERATOR_PACKAGE": [
                {"id": "PROD-PKG-001", "code": "PKG", "name": "CoWoS Package (HBM3)", "die_area_mm2": 600},
                {"id": "PROD-PKG-002", "code": "IPZ", "name": "Interposer (2.5D)", "die_area_mm2": 1200},
            ],
            "MOBILE_SOC": [
                {"id": "PROD-MOB-001", "code": "SOC", "name": "Mobile AP (Flagship)", "die_area_mm2": 120},
                {"id": "PROD-MOB-002", "code": "MID", "name": "Mobile AP (Mid-range)", "die_area_mm2": 80},
                {"id": "PROD-MOB-003", "code": "MDM", "name": "5G Modem", "die_area_mm2": 50},
            ],
            "HPC_CHIP": [
                {"id": "PROD-HPC-001", "code": "HPC", "name": "HPC Processor", "die_area_mm2": 500},
                {"id": "PROD-HPC-002", "code": "NET", "name": "Network Switch ASIC", "die_area_mm2": 300},
            ],
            "SERVER_CPU": [
                {"id": "PROD-SRV-001", "code": "SRV", "name": "Server CPU (Xeon-class)", "die_area_mm2": 400},
                {"id": "PROD-SRV-002", "code": "IOD", "name": "I/O Die (chiplet)", "die_area_mm2": 100},
            ],
        }
        return product_map.get(self.scenario.target_product, product_map["AI_ACCELERATOR"])

    def _generate_sensor_data(self, step) -> dict:
        """공정별 센서 데이터"""
        base = {
            "temperature_c": round(random.gauss(25, 2), 1),
            "humidity_pct": round(random.gauss(45, 3), 1),
        }

        step_name = step.name.lower()
        if "litho" in step_name or "photo" in step_name or "euv" in step_name:
            base.update({
                "dose_mj_cm2": round(random.gauss(30, 1), 2),
                "focus_nm": round(random.gauss(0, 5), 1),
                "overlay_nm": round(random.gauss(0, 2), 2),
                "lens_aberration": round(random.gauss(0, 0.5), 3),
            })
        elif "etch" in step_name:
            base.update({
                "chamber_pressure_mtorr": round(random.gauss(20, 2), 1),
                "rf_power_w": round(random.gauss(500, 20), 0),
                "gas_flow_sccm": round(random.gauss(100, 5), 1),
                "etch_rate_nm_min": round(random.gauss(50, 3), 1),
            })
        elif "cvd" in step_name or "deposition" in step_name:
            base.update({
                "chamber_temp_c": round(random.gauss(400, 10), 0),
                "pressure_torr": round(random.gauss(1.0, 0.1), 2),
                "gas_flow_sccm": round(random.gauss(200, 10), 0),
                "deposition_rate_nm_min": round(random.gauss(10, 1), 2),
            })
        elif "cmp" in step_name or "planar" in step_name:
            base.update({
                "down_force_psi": round(random.gauss(3.0, 0.2), 2),
                "platen_speed_rpm": round(random.gauss(80, 5), 0),
                "slurry_flow_ml_min": round(random.gauss(200, 10), 0),
                "removal_rate_nm_min": round(random.gauss(200, 15), 0),
            })
        elif "implant" in step_name:
            base.update({
                "beam_energy_kev": round(random.gauss(50, 5), 0),
                "beam_current_ua": round(random.gauss(10, 1), 1),
                "dose_atoms_cm2": round(random.gauss(1e15, 1e14), 2),
                "tilt_deg": round(random.gauss(7, 0.5), 1),
            })

        return base

    def _generate_metrology_data(self, step, node_nm: int) -> dict:
        """공정별 계측 데이터"""
        cd_target = node_nm * 2  # rough target CD
        return {
            "cd_nm": round(random.gauss(cd_target, cd_target * 0.02), 1),
            "cd_uniformity_pct": round(random.gauss(2.0, 0.3), 2),
            "overlay_x_nm": round(random.gauss(0, 1.5), 2),
            "overlay_y_nm": round(random.gauss(0, 1.5), 2),
            "film_thickness_nm": round(random.gauss(50, 2), 1),
            "roughness_rms_nm": round(abs(random.gauss(0.3, 0.05)), 3),
        }

    def _generate_summary(self) -> dict:
        """생성 데이터 요약"""
        return {
            "scenario": self.scenario.name,
            "process_node": self.scenario.process_node,
            "generated_at": self._now.isoformat(),
            "data_counts": {
                "process_nodes": "All ontology nodes",
                "ip_blocks": "7 blocks",
                "fab_equipment": f"{self.scenario.equipment_count} units",
                "wip_items": f"{self.scenario.wip_lots} lots",
                "materials": "11 ontology + Si wafer",
                "suppliers": "~20 (Tier 1-3)",
                "wafer_records": f"Up to 500 records ({self.scenario.history_days} days)",
                "yield_events": "3-8 events",
            },
            "ontology_sources": [
                "SemiconductorOntology (IRDS-based process nodes)",
                "AIIndustryOntology (accelerator specs, HBM data)",
                "MaterialsKnowledgeBase (11 critical materials)",
                "EquipmentKnowledgeBase (ASML, LAM, TEL, AMAT, KLA)",
                "ProcessFlowOntology (13-step standard flow)",
                "FailureModeOntology (defect types + equipment failures)",
            ],
        }
