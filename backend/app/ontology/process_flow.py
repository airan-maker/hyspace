"""
Semiconductor Process Flow Ontology

표준 반도체 제조 공정 흐름 및 단계별 지식

Sources:
- SEMI Standards (SEMI E10, E79)
- Published process flow references
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ProcessModule(str, Enum):
    FEOL = "FEOL"       # Front-End of Line (트랜지스터 형성)
    MOL = "MOL"         # Middle of Line (콘택)
    BEOL = "BEOL"       # Back-End of Line (배선)


@dataclass
class ProcessStep:
    """공정 단계 정의"""
    step_id: str
    name: str
    module: ProcessModule
    order: int
    equipment_type: str
    typical_duration_minutes: float
    critical_parameters: list[dict]
    yield_impact: str           # HIGH, MEDIUM, LOW
    defect_types: list[str]
    next_steps: list[str]
    description: str


# ============================================================
# Standard Logic Fab Process Flow (Advanced Node)
# ============================================================

LOGIC_PROCESS_FLOW: dict[str, ProcessStep] = {
    # === FEOL: Front-End of Line ===
    "STI": ProcessStep(
        step_id="STI",
        name="Shallow Trench Isolation",
        module=ProcessModule.FEOL,
        order=1,
        equipment_type="ETCH + CVD + CMP",
        typical_duration_minutes=180,
        critical_parameters=[
            {"name": "trench_depth_nm", "target": 250, "tolerance": 5, "unit": "nm"},
            {"name": "oxide_fill_void", "target": 0, "tolerance": 0, "unit": "%"},
            {"name": "cmp_uniformity", "target": 3, "tolerance": 1, "unit": "% (1-sigma)"},
        ],
        yield_impact="HIGH",
        defect_types=["STI_VOID", "CMP_SCRATCH", "OXIDE_THINNING"],
        next_steps=["WELL_IMPLANT"],
        description="소자 간 격리를 위한 트렌치 형성 → 산화막 충진 → CMP 평탄화"
    ),
    "WELL_IMPLANT": ProcessStep(
        step_id="WELL_IMPLANT",
        name="Well Implantation",
        module=ProcessModule.FEOL,
        order=2,
        equipment_type="ION_IMPLANT",
        typical_duration_minutes=30,
        critical_parameters=[
            {"name": "dose", "target": 1e13, "tolerance": 5, "unit": "ions/cm²"},
            {"name": "energy", "target": 300, "tolerance": 2, "unit": "keV"},
            {"name": "tilt_angle", "target": 7, "tolerance": 0.5, "unit": "degree"},
        ],
        yield_impact="MEDIUM",
        defect_types=["DOSE_VARIATION", "CHANNELING"],
        next_steps=["GATE_OXIDE"],
        description="NMOS/PMOS 웰 영역 이온 주입 (P-well: Boron, N-well: Phosphorus)"
    ),
    "GATE_OXIDE": ProcessStep(
        step_id="GATE_OXIDE",
        name="High-k Gate Dielectric",
        module=ProcessModule.FEOL,
        order=3,
        equipment_type="ALD",
        typical_duration_minutes=45,
        critical_parameters=[
            {"name": "thickness_angstrom", "target": 15, "tolerance": 0.5, "unit": "A"},
            {"name": "k_value", "target": 25, "tolerance": 2, "unit": ""},
            {"name": "interface_trap_density", "target": 1e10, "tolerance": None, "unit": "cm⁻²eV⁻¹"},
        ],
        yield_impact="HIGH",
        defect_types=["THICKNESS_VARIATION", "INTERFACE_DEFECT", "PARTICLE"],
        next_steps=["GATE_METAL"],
        description="HfO₂ 기반 High-k 게이트 절연막 ALD 증착 (EOT < 1nm)"
    ),
    "GATE_METAL": ProcessStep(
        step_id="GATE_METAL",
        name="Metal Gate Formation",
        module=ProcessModule.FEOL,
        order=4,
        equipment_type="PVD + ALD + CMP",
        typical_duration_minutes=120,
        critical_parameters=[
            {"name": "work_function_ev", "target": 4.6, "tolerance": 0.1, "unit": "eV (NMOS)"},
            {"name": "gate_height_nm", "target": 40, "tolerance": 2, "unit": "nm"},
            {"name": "gate_cd_nm", "target": 12, "tolerance": 0.5, "unit": "nm"},
        ],
        yield_impact="HIGH",
        defect_types=["CD_VARIATION", "VOID", "WORK_FUNCTION_SHIFT"],
        next_steps=["SPACER"],
        description="HKMG (High-k Metal Gate) - TiN/TiAl/TaN 다층 금속 게이트"
    ),
    "SPACER": ProcessStep(
        step_id="SPACER",
        name="Spacer Formation",
        module=ProcessModule.FEOL,
        order=5,
        equipment_type="CVD + ETCH",
        typical_duration_minutes=60,
        critical_parameters=[
            {"name": "spacer_width_nm", "target": 5, "tolerance": 0.3, "unit": "nm"},
            {"name": "spacer_uniformity", "target": 2, "tolerance": 1, "unit": "% (1-sigma)"},
        ],
        yield_impact="MEDIUM",
        defect_types=["SPACER_ASYMMETRY", "UNDERETCH", "OVERETCH"],
        next_steps=["SD_EPI"],
        description="SiN/SiCO 스페이서 - 게이트와 S/D 분리, LDD 정의"
    ),
    "SD_EPI": ProcessStep(
        step_id="SD_EPI",
        name="Source/Drain Epitaxy",
        module=ProcessModule.FEOL,
        order=6,
        equipment_type="EPITAXY",
        typical_duration_minutes=90,
        critical_parameters=[
            {"name": "sige_ge_content", "target": 35, "tolerance": 2, "unit": "% (PMOS)"},
            {"name": "sic_c_content", "target": 1.5, "tolerance": 0.2, "unit": "% (NMOS)"},
            {"name": "epi_thickness_nm", "target": 30, "tolerance": 2, "unit": "nm"},
        ],
        yield_impact="HIGH",
        defect_types=["FACETING", "STACKING_FAULT", "LOADING_EFFECT"],
        next_steps=["SILICIDE"],
        description="PMOS: SiGe S/D (압축 스트레인), NMOS: SiC 또는 Si:P (인장 스트레인)"
    ),
    "SILICIDE": ProcessStep(
        step_id="SILICIDE",
        name="Silicide Formation",
        module=ProcessModule.FEOL,
        order=7,
        equipment_type="PVD + THERMAL",
        typical_duration_minutes=40,
        critical_parameters=[
            {"name": "contact_resistance", "target": 1e-9, "tolerance": None, "unit": "ohm·cm²"},
            {"name": "silicide_thickness_nm", "target": 8, "tolerance": 1, "unit": "nm"},
        ],
        yield_impact="MEDIUM",
        defect_types=["AGGLOMERATION", "NON_UNIFORM_FORMATION"],
        next_steps=["CONTACT"],
        description="TiSi₂ 또는 NiSi 실리사이드로 접촉 저항 감소"
    ),

    # === MOL: Middle of Line ===
    "CONTACT": ProcessStep(
        step_id="CONTACT",
        name="Contact Formation",
        module=ProcessModule.MOL,
        order=8,
        equipment_type="ETCH + PVD + CVD + CMP",
        typical_duration_minutes=150,
        critical_parameters=[
            {"name": "contact_cd_nm", "target": 18, "tolerance": 1, "unit": "nm"},
            {"name": "aspect_ratio", "target": 10, "tolerance": None, "unit": ""},
            {"name": "contact_resistance_ohm", "target": 50, "tolerance": 10, "unit": "ohm"},
        ],
        yield_impact="HIGH",
        defect_types=["CONTACT_OPEN", "CONTACT_SHORT", "HIGH_RESISTANCE", "VOID"],
        next_steps=["M0"],
        description="게이트/S/D→메탈 연결, W 또는 Co 충진, 고종횡비(HAR) 식각 핵심"
    ),

    # === BEOL: Back-End of Line ===
    "M0": ProcessStep(
        step_id="M0",
        name="Metal 0 (Local Interconnect)",
        module=ProcessModule.BEOL,
        order=9,
        equipment_type="ETCH + PVD + CVD + CMP",
        typical_duration_minutes=120,
        critical_parameters=[
            {"name": "line_width_nm", "target": 21, "tolerance": 1, "unit": "nm"},
            {"name": "line_resistance_ohm_per_um", "target": 300, "tolerance": 30, "unit": "ohm/µm"},
            {"name": "via_resistance_ohm", "target": 100, "tolerance": 20, "unit": "ohm"},
        ],
        yield_impact="HIGH",
        defect_types=["LINE_OPEN", "LINE_SHORT", "VIA_VOID", "ELECTROMIGRATION"],
        next_steps=["M1"],
        description="첫 번째 금속 배선층, 최소 피치 적용, Cu 또는 Ru 사용"
    ),
    "M1": ProcessStep(
        step_id="M1",
        name="Metal 1",
        module=ProcessModule.BEOL,
        order=10,
        equipment_type="ETCH + PVD + ECD + CMP",
        typical_duration_minutes=120,
        critical_parameters=[
            {"name": "line_width_nm", "target": 28, "tolerance": 1.5, "unit": "nm"},
            {"name": "imd_k_value", "target": 2.5, "tolerance": 0.2, "unit": ""},
        ],
        yield_impact="HIGH",
        defect_types=["LINE_OPEN", "LINE_SHORT", "TIME_DEPENDENT_DIELECTRIC_BREAKDOWN"],
        next_steps=["UPPER_METALS"],
        description="Dual-damascene Cu 배선, Low-k (k<2.5) IMD"
    ),
    "UPPER_METALS": ProcessStep(
        step_id="UPPER_METALS",
        name="Upper Metal Layers (M2-Mn)",
        module=ProcessModule.BEOL,
        order=11,
        equipment_type="ETCH + PVD + ECD + CMP",
        typical_duration_minutes=600,
        critical_parameters=[
            {"name": "total_metal_layers", "target": 15, "tolerance": None, "unit": "layers"},
            {"name": "imd_capacitance", "target": None, "tolerance": None, "unit": "fF/µm"},
        ],
        yield_impact="MEDIUM",
        defect_types=["CU_VOID", "HILLOCK", "STRESS_MIGRATION"],
        next_steps=["PASSIVATION"],
        description="3nm 노드: 약 13-15층 금속 배선, 상위층일수록 피치 증가"
    ),
    "PASSIVATION": ProcessStep(
        step_id="PASSIVATION",
        name="Passivation & Pad Formation",
        module=ProcessModule.BEOL,
        order=12,
        equipment_type="CVD + ETCH",
        typical_duration_minutes=90,
        critical_parameters=[
            {"name": "passivation_thickness_um", "target": 2, "tolerance": 0.2, "unit": "µm"},
            {"name": "pad_size_um", "target": 45, "tolerance": 2, "unit": "µm"},
        ],
        yield_impact="LOW",
        defect_types=["CRACK", "MOISTURE_INGRESS"],
        next_steps=["WAFER_TEST"],
        description="SiN/SiO₂ 보호막 + Al 패드 형성, 최종 보호"
    ),
    "WAFER_TEST": ProcessStep(
        step_id="WAFER_TEST",
        name="Wafer Probe Test",
        module=ProcessModule.BEOL,
        order=13,
        equipment_type="TEST",
        typical_duration_minutes=30,
        critical_parameters=[
            {"name": "test_coverage_pct", "target": 99, "tolerance": 1, "unit": "%"},
            {"name": "contact_resistance_mohm", "target": 200, "tolerance": 50, "unit": "mohm"},
        ],
        yield_impact="LOW",
        defect_types=["PROBE_MARK", "FALSE_FAIL"],
        next_steps=[],
        description="다이 단위 전기적 테스트 (DC, AC, Memory BIST)"
    ),
}


# ============================================================
# Process Step Count by Node
# ============================================================

NODE_COMPLEXITY = {
    "2nm":  {"total_steps": 400, "euv_steps": 25, "metal_layers": 15, "mask_count": 95},
    "3nm":  {"total_steps": 350, "euv_steps": 19, "metal_layers": 13, "mask_count": 80},
    "5nm":  {"total_steps": 300, "euv_steps": 14, "metal_layers": 12, "mask_count": 75},
    "7nm":  {"total_steps": 250, "euv_steps": 0,  "metal_layers": 11, "mask_count": 60},
    "10nm": {"total_steps": 200, "euv_steps": 0,  "metal_layers": 10, "mask_count": 55},
    "14nm": {"total_steps": 170, "euv_steps": 0,  "metal_layers": 8,  "mask_count": 50},
    "28nm": {"total_steps": 120, "euv_steps": 0,  "metal_layers": 7,  "mask_count": 40},
}


# ============================================================
# Lookup Interface
# ============================================================

class ProcessFlowOntology:
    """공정 흐름 온톨로지 인터페이스"""

    @staticmethod
    def get_full_flow() -> dict[str, ProcessStep]:
        return LOGIC_PROCESS_FLOW

    @staticmethod
    def get_step(step_id: str) -> Optional[ProcessStep]:
        return LOGIC_PROCESS_FLOW.get(step_id)

    @staticmethod
    def get_feol_steps() -> list[ProcessStep]:
        return [s for s in LOGIC_PROCESS_FLOW.values() if s.module == ProcessModule.FEOL]

    @staticmethod
    def get_mol_steps() -> list[ProcessStep]:
        return [s for s in LOGIC_PROCESS_FLOW.values() if s.module == ProcessModule.MOL]

    @staticmethod
    def get_beol_steps() -> list[ProcessStep]:
        return [s for s in LOGIC_PROCESS_FLOW.values() if s.module == ProcessModule.BEOL]

    @staticmethod
    def get_high_yield_impact_steps() -> list[ProcessStep]:
        return [s for s in LOGIC_PROCESS_FLOW.values() if s.yield_impact == "HIGH"]

    @staticmethod
    def get_node_complexity(node: str) -> Optional[dict]:
        return NODE_COMPLEXITY.get(node)

    @staticmethod
    def get_ordered_flow() -> list[ProcessStep]:
        return sorted(LOGIC_PROCESS_FLOW.values(), key=lambda s: s.order)
