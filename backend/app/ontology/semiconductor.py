"""
Semiconductor Industry Ontology

반도체 공정, 노드, 물리적 특성에 대한 도메인 지식 체계

Sources:
- IRDS (International Roadmap for Devices and Systems) 2024
- SEMI Standards
- Published foundry data (TSMC, Samsung, Intel)
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ============================================================
# Process Node Definitions
# ============================================================

class FoundryVendor(str, Enum):
    TSMC = "TSMC"
    SAMSUNG = "Samsung Foundry"
    INTEL = "Intel Foundry"
    GLOBALFOUNDRIES = "GlobalFoundries"
    SMIC = "SMIC"
    UMC = "UMC"


@dataclass
class ProcessNodeSpec:
    """공정 노드 사양 - IRDS 및 공개 데이터 기반"""
    name: str                           # 마케팅 이름 (e.g., "N3E")
    node_nm: int                        # 공칭 노드 (nm)
    actual_gate_length_nm: float        # 실제 게이트 길이
    metal_pitch_nm: float               # 최소 금속 배선 간격
    fin_pitch_nm: Optional[float]       # 핀 간격 (FinFET)
    gate_pitch_nm: float                # 게이트 간격 (CPP)
    vendor: FoundryVendor
    transistor_type: str                # FinFET, GAA (GAAFET/Nanosheet)

    # Density & Performance
    logic_density_mtr_per_mm2: float    # 백만 트랜지스터/mm²
    sram_cell_size_um2: float           # 6T SRAM 셀 크기 (µm²)

    # Power/Performance vs previous node
    speed_improvement_pct: float        # 동일 전력 대비 속도 향상 (%)
    power_reduction_pct: float          # 동일 속도 대비 전력 감소 (%)
    density_improvement_pct: float      # 이전 노드 대비 밀도 향상 (%)

    # Manufacturing
    euv_layers: int                     # EUV 리소그래피 레이어 수
    total_mask_layers: int              # 총 마스크 레이어 수
    wafer_cost_usd: int                 # 300mm 웨이퍼 가공 비용
    nre_cost_million_usd: int           # 마스크 세트 비용 (NRE)
    defect_density_per_cm2: float       # 성숙 공정 결함 밀도
    typical_yield_pct: float            # 성숙 공정 수율 (중형 다이)

    # Availability
    risk_production_year: int
    volume_production_year: int
    is_available: bool = True

    description: str = ""


# TSMC Process Nodes (2024-2026 공개 데이터 기반)
TSMC_NODES: dict[str, ProcessNodeSpec] = {
    "N3E": ProcessNodeSpec(
        name="N3E",
        node_nm=3,
        actual_gate_length_nm=12,
        metal_pitch_nm=21,
        fin_pitch_nm=25,
        gate_pitch_nm=48,
        vendor=FoundryVendor.TSMC,
        transistor_type="FinFET",
        logic_density_mtr_per_mm2=291,
        sram_cell_size_um2=0.0199,
        speed_improvement_pct=18,
        power_reduction_pct=32,
        density_improvement_pct=60,
        euv_layers=19,
        total_mask_layers=80,
        wafer_cost_usd=20000,
        nre_cost_million_usd=300,
        defect_density_per_cm2=0.09,
        typical_yield_pct=80,
        risk_production_year=2022,
        volume_production_year=2023,
        description="TSMC 3nm Enhanced - Apple A17 Pro, M3 시리즈 양산 노드"
    ),
    "N3P": ProcessNodeSpec(
        name="N3P",
        node_nm=3,
        actual_gate_length_nm=12,
        metal_pitch_nm=21,
        fin_pitch_nm=25,
        gate_pitch_nm=48,
        vendor=FoundryVendor.TSMC,
        transistor_type="FinFET",
        logic_density_mtr_per_mm2=291,
        sram_cell_size_um2=0.0199,
        speed_improvement_pct=5,
        power_reduction_pct=5,
        density_improvement_pct=0,
        euv_layers=19,
        total_mask_layers=80,
        wafer_cost_usd=20000,
        nre_cost_million_usd=300,
        defect_density_per_cm2=0.08,
        typical_yield_pct=82,
        risk_production_year=2023,
        volume_production_year=2024,
        description="N3E 대비 5% 성능/전력 개선, N3E와 동일 설계 규칙"
    ),
    "N2": ProcessNodeSpec(
        name="N2",
        node_nm=2,
        actual_gate_length_nm=10,
        metal_pitch_nm=18,
        fin_pitch_nm=None,
        gate_pitch_nm=44,
        vendor=FoundryVendor.TSMC,
        transistor_type="GAA (Nanosheet)",
        logic_density_mtr_per_mm2=400,
        sram_cell_size_um2=0.015,
        speed_improvement_pct=15,
        power_reduction_pct=30,
        density_improvement_pct=37,
        euv_layers=25,
        total_mask_layers=90,
        wafer_cost_usd=28000,
        nre_cost_million_usd=500,
        defect_density_per_cm2=0.12,
        typical_yield_pct=70,
        risk_production_year=2024,
        volume_production_year=2025,
        description="TSMC 최초 GAA (나노시트) 트랜지스터, 백사이드 파워 딜리버리"
    ),
    "A16": ProcessNodeSpec(
        name="A16",
        node_nm=1.6,
        actual_gate_length_nm=8,
        metal_pitch_nm=16,
        fin_pitch_nm=None,
        gate_pitch_nm=40,
        vendor=FoundryVendor.TSMC,
        transistor_type="GAA (Nanosheet) + BSPDN",
        logic_density_mtr_per_mm2=480,
        sram_cell_size_um2=0.012,
        speed_improvement_pct=10,
        power_reduction_pct=25,
        density_improvement_pct=20,
        euv_layers=30,
        total_mask_layers=95,
        wafer_cost_usd=35000,
        nre_cost_million_usd=600,
        defect_density_per_cm2=0.15,
        typical_yield_pct=60,
        risk_production_year=2025,
        volume_production_year=2026,
        description="Super Power Rail (BSPDN) 적용, HPC 최적화"
    ),
    "N5": ProcessNodeSpec(
        name="N5",
        node_nm=5,
        actual_gate_length_nm=16,
        metal_pitch_nm=28,
        fin_pitch_nm=25,
        gate_pitch_nm=48,
        vendor=FoundryVendor.TSMC,
        transistor_type="FinFET",
        logic_density_mtr_per_mm2=173,
        sram_cell_size_um2=0.025,
        speed_improvement_pct=15,
        power_reduction_pct=30,
        density_improvement_pct=84,
        euv_layers=14,
        total_mask_layers=75,
        wafer_cost_usd=16000,
        nre_cost_million_usd=200,
        defect_density_per_cm2=0.06,
        typical_yield_pct=88,
        risk_production_year=2019,
        volume_production_year=2020,
        description="가장 성숙한 EUV 노드 - Apple A14/M1, AMD Zen4"
    ),
    "N4P": ProcessNodeSpec(
        name="N4P",
        node_nm=4,
        actual_gate_length_nm=14,
        metal_pitch_nm=26,
        fin_pitch_nm=25,
        gate_pitch_nm=48,
        vendor=FoundryVendor.TSMC,
        transistor_type="FinFET",
        logic_density_mtr_per_mm2=200,
        sram_cell_size_um2=0.022,
        speed_improvement_pct=6,
        power_reduction_pct=10,
        density_improvement_pct=15,
        euv_layers=17,
        total_mask_layers=78,
        wafer_cost_usd=17000,
        nre_cost_million_usd=220,
        defect_density_per_cm2=0.06,
        typical_yield_pct=87,
        risk_production_year=2022,
        volume_production_year=2023,
        description="N5 최적화 - NVIDIA H100/H200, Qualcomm Snapdragon 8 Gen3"
    ),
    "N7": ProcessNodeSpec(
        name="N7",
        node_nm=7,
        actual_gate_length_nm=20,
        metal_pitch_nm=36,
        fin_pitch_nm=30,
        gate_pitch_nm=54,
        vendor=FoundryVendor.TSMC,
        transistor_type="FinFET",
        logic_density_mtr_per_mm2=96,
        sram_cell_size_um2=0.027,
        speed_improvement_pct=20,
        power_reduction_pct=40,
        density_improvement_pct=60,
        euv_layers=0,
        total_mask_layers=60,
        wafer_cost_usd=10000,
        nre_cost_million_usd=100,
        defect_density_per_cm2=0.04,
        typical_yield_pct=92,
        risk_production_year=2017,
        volume_production_year=2018,
        description="DUV 기반 성숙 노드 - AMD Zen2, Apple A12"
    ),
}


# Samsung Process Nodes
SAMSUNG_NODES: dict[str, ProcessNodeSpec] = {
    "SF3": ProcessNodeSpec(
        name="SF3 (3GAE)",
        node_nm=3,
        actual_gate_length_nm=12,
        metal_pitch_nm=20,
        fin_pitch_nm=None,
        gate_pitch_nm=45,
        vendor=FoundryVendor.SAMSUNG,
        transistor_type="GAA (MBCFET)",
        logic_density_mtr_per_mm2=230,
        sram_cell_size_um2=0.020,
        speed_improvement_pct=16,
        power_reduction_pct=33,
        density_improvement_pct=50,
        euv_layers=21,
        total_mask_layers=82,
        wafer_cost_usd=19000,
        nre_cost_million_usd=280,
        defect_density_per_cm2=0.13,
        typical_yield_pct=65,
        risk_production_year=2023,
        volume_production_year=2024,
        description="Samsung 최초 GAA (MBCFET), Exynos 2400"
    ),
    "SF2": ProcessNodeSpec(
        name="SF2",
        node_nm=2,
        actual_gate_length_nm=10,
        metal_pitch_nm=17,
        fin_pitch_nm=None,
        gate_pitch_nm=42,
        vendor=FoundryVendor.SAMSUNG,
        transistor_type="GAA (MBCFET) + BSPDN",
        logic_density_mtr_per_mm2=370,
        sram_cell_size_um2=0.016,
        speed_improvement_pct=12,
        power_reduction_pct=25,
        density_improvement_pct=45,
        euv_layers=28,
        total_mask_layers=90,
        wafer_cost_usd=27000,
        nre_cost_million_usd=450,
        defect_density_per_cm2=0.15,
        typical_yield_pct=55,
        risk_production_year=2025,
        volume_production_year=2026,
        description="Samsung 2세대 GAA + 백사이드 파워, HBM 연계 최적화"
    ),
}


# Intel Process Nodes
INTEL_NODES: dict[str, ProcessNodeSpec] = {
    "Intel_18A": ProcessNodeSpec(
        name="Intel 18A",
        node_nm=1.8,
        actual_gate_length_nm=10,
        metal_pitch_nm=18,
        fin_pitch_nm=None,
        gate_pitch_nm=42,
        vendor=FoundryVendor.INTEL,
        transistor_type="GAA (RibbonFET) + PowerVia",
        logic_density_mtr_per_mm2=350,
        sram_cell_size_um2=0.017,
        speed_improvement_pct=10,
        power_reduction_pct=20,
        density_improvement_pct=40,
        euv_layers=22,
        total_mask_layers=85,
        wafer_cost_usd=25000,
        nre_cost_million_usd=400,
        defect_density_per_cm2=0.14,
        typical_yield_pct=60,
        risk_production_year=2024,
        volume_production_year=2025,
        description="Intel 최초 파운드리 외부 고객 노드, RibbonFET + PowerVia"
    ),
    "Intel_20A": ProcessNodeSpec(
        name="Intel 20A",
        node_nm=2,
        actual_gate_length_nm=12,
        metal_pitch_nm=20,
        fin_pitch_nm=None,
        gate_pitch_nm=44,
        vendor=FoundryVendor.INTEL,
        transistor_type="GAA (RibbonFET) + PowerVia",
        logic_density_mtr_per_mm2=280,
        sram_cell_size_um2=0.019,
        speed_improvement_pct=15,
        power_reduction_pct=30,
        density_improvement_pct=50,
        euv_layers=18,
        total_mask_layers=80,
        wafer_cost_usd=22000,
        nre_cost_million_usd=350,
        defect_density_per_cm2=0.13,
        typical_yield_pct=65,
        risk_production_year=2024,
        volume_production_year=2025,
        description="Intel 최초 RibbonFET (GAA) 노드, Arrow Lake"
    ),
}


# ============================================================
# Wafer Specifications
# ============================================================

@dataclass
class WaferSpec:
    """웨이퍼 사양"""
    diameter_mm: int
    thickness_um: float
    material: str
    crystal_orientation: str
    resistivity_ohm_cm: tuple[float, float]
    edge_exclusion_mm: float
    usable_area_mm2: float


WAFER_SPECS = {
    "300mm": WaferSpec(
        diameter_mm=300,
        thickness_um=775,
        material="CZ Silicon",
        crystal_orientation="<100>",
        resistivity_ohm_cm=(1.0, 100.0),
        edge_exclusion_mm=3.0,
        usable_area_mm2=68_000  # 약 680 cm²
    ),
    "200mm": WaferSpec(
        diameter_mm=200,
        thickness_um=725,
        material="CZ Silicon",
        crystal_orientation="<100>",
        resistivity_ohm_cm=(1.0, 100.0),
        edge_exclusion_mm=3.0,
        usable_area_mm2=29_000
    ),
}


# ============================================================
# Packaging Technologies
# ============================================================

@dataclass
class PackagingTech:
    """패키징 기술 사양"""
    name: str
    full_name: str
    vendor: str
    max_hbm_stacks: int
    max_chiplets: int
    interconnect_bandwidth_tbps: float
    typical_power_delivery_w: int
    die_size_limit_mm2: int
    cost_premium_vs_organic_pct: float
    typical_applications: list[str]
    description: str


PACKAGING_TECHNOLOGIES = {
    "CoWoS-S": PackagingTech(
        name="CoWoS-S",
        full_name="Chip-on-Wafer-on-Substrate (Silicon Interposer)",
        vendor="TSMC",
        max_hbm_stacks=12,
        max_chiplets=6,
        interconnect_bandwidth_tbps=12.8,
        typical_power_delivery_w=700,
        die_size_limit_mm2=3300,
        cost_premium_vs_organic_pct=200,
        typical_applications=["HPC/AI (H100, MI300X)", "HBM 통합"],
        description="실리콘 인터포저 기반 2.5D 패키징, HBM 최대 12스택 지원"
    ),
    "CoWoS-L": PackagingTech(
        name="CoWoS-L",
        full_name="CoWoS with Local Silicon Interconnect",
        vendor="TSMC",
        max_hbm_stacks=16,
        max_chiplets=12,
        interconnect_bandwidth_tbps=16.0,
        typical_power_delivery_w=1000,
        die_size_limit_mm2=5000,
        cost_premium_vs_organic_pct=250,
        typical_applications=["차세대 AI 가속기 (B100/B200)", "초대형 다이"],
        description="CoWoS-S 진화형, LSI (Local Silicon Interconnect)로 대면적 지원"
    ),
    "InFO": PackagingTech(
        name="InFO",
        full_name="Integrated Fan-Out",
        vendor="TSMC",
        max_hbm_stacks=0,
        max_chiplets=4,
        interconnect_bandwidth_tbps=2.0,
        typical_power_delivery_w=15,
        die_size_limit_mm2=400,
        cost_premium_vs_organic_pct=30,
        typical_applications=["모바일 AP (Apple A-series)", "IoT"],
        description="팬아웃 웨이퍼 레벨 패키징, 모바일 최적화"
    ),
    "EMIB": PackagingTech(
        name="EMIB",
        full_name="Embedded Multi-die Interconnect Bridge",
        vendor="Intel",
        max_hbm_stacks=4,
        max_chiplets=8,
        interconnect_bandwidth_tbps=8.0,
        typical_power_delivery_w=500,
        die_size_limit_mm2=2500,
        cost_premium_vs_organic_pct=150,
        typical_applications=["Intel Ponte Vecchio", "멀티칩 서버"],
        description="유기 기판에 실리콘 브릿지 임베딩, 선택적 고밀도 연결"
    ),
    "Foveros": PackagingTech(
        name="Foveros",
        full_name="Foveros 3D Stacking",
        vendor="Intel",
        max_hbm_stacks=0,
        max_chiplets=4,
        interconnect_bandwidth_tbps=4.0,
        typical_power_delivery_w=300,
        die_size_limit_mm2=800,
        cost_premium_vs_organic_pct=300,
        typical_applications=["Intel Lakefield", "3D 적층 로직"],
        description="로직-온-로직 3D 적층, 다이 간 직접 본딩"
    ),
    "I-Cube4": PackagingTech(
        name="I-Cube4",
        full_name="I-Cube 4-High HBM",
        vendor="Samsung",
        max_hbm_stacks=4,
        max_chiplets=4,
        interconnect_bandwidth_tbps=4.8,
        typical_power_delivery_w=400,
        die_size_limit_mm2=2000,
        cost_premium_vs_organic_pct=180,
        typical_applications=["HBM 통합 HPC"],
        description="Samsung 2.5D 실리콘 인터포저, HBM4 4스택"
    ),
}


# ============================================================
# Key Industry Metrics & Standards
# ============================================================

@dataclass
class YieldModelParams:
    """수율 모델 파라미터"""
    model_name: str
    formula_description: str
    typical_defect_density_range: tuple[float, float]  # defects/cm²
    die_area_sensitivity: str


YIELD_MODELS = {
    "murphy": YieldModelParams(
        model_name="Murphy's Model",
        formula_description="Y = ((1 - exp(-A*D)) / (A*D))²",
        typical_defect_density_range=(0.01, 0.5),
        die_area_sensitivity="대형 다이에 적합 (>100mm²)"
    ),
    "poisson": YieldModelParams(
        model_name="Poisson Model",
        formula_description="Y = exp(-A*D)",
        typical_defect_density_range=(0.01, 0.5),
        die_area_sensitivity="소형 다이에 적합 (<50mm²)"
    ),
    "negative_binomial": YieldModelParams(
        model_name="Negative Binomial",
        formula_description="Y = (1 + A*D/alpha)^(-alpha)",
        typical_defect_density_range=(0.01, 0.5),
        die_area_sensitivity="클러스터링 결함 모델, 가장 현실적"
    ),
}


# OEE (Overall Equipment Effectiveness) - SEMI E10 표준
@dataclass
class OEEDefinition:
    """장비 종합 효율 정의 - SEMI E10"""
    metric: str
    formula: str
    world_class_target_pct: float
    typical_range_pct: tuple[float, float]
    description: str


OEE_STANDARDS = {
    "availability": OEEDefinition(
        metric="Availability",
        formula="(Scheduled Time - Downtime) / Scheduled Time",
        world_class_target_pct=90,
        typical_range_pct=(80, 95),
        description="장비 가동 가능 시간 비율, PM/고장 제외"
    ),
    "performance": OEEDefinition(
        metric="Performance",
        formula="(Ideal Cycle Time × Total Count) / Run Time",
        world_class_target_pct=95,
        typical_range_pct=(85, 98),
        description="이론적 최대 속도 대비 실제 처리 속도"
    ),
    "quality": OEEDefinition(
        metric="Quality",
        formula="Good Count / Total Count",
        world_class_target_pct=99,
        typical_range_pct=(95, 99.5),
        description="전체 생산 중 양품 비율"
    ),
    "oee": OEEDefinition(
        metric="OEE",
        formula="Availability × Performance × Quality",
        world_class_target_pct=85,
        typical_range_pct=(60, 90),
        description="종합 장비 효율, World-Class = 85%+"
    ),
}


# ============================================================
# Lookup Interface
# ============================================================

class SemiconductorOntology:
    """반도체 도메인 온톨로지 통합 인터페이스"""

    @staticmethod
    def get_all_nodes() -> dict[str, ProcessNodeSpec]:
        """모든 공정 노드 조회"""
        all_nodes = {}
        all_nodes.update(TSMC_NODES)
        all_nodes.update(SAMSUNG_NODES)
        all_nodes.update(INTEL_NODES)
        return all_nodes

    @staticmethod
    def get_nodes_by_vendor(vendor: FoundryVendor) -> dict[str, ProcessNodeSpec]:
        vendor_map = {
            FoundryVendor.TSMC: TSMC_NODES,
            FoundryVendor.SAMSUNG: SAMSUNG_NODES,
            FoundryVendor.INTEL: INTEL_NODES,
        }
        return vendor_map.get(vendor, {})

    @staticmethod
    def get_node(name: str) -> Optional[ProcessNodeSpec]:
        all_nodes = SemiconductorOntology.get_all_nodes()
        return all_nodes.get(name)

    @staticmethod
    def get_nodes_by_nm(node_nm: int) -> list[ProcessNodeSpec]:
        return [n for n in SemiconductorOntology.get_all_nodes().values()
                if n.node_nm == node_nm]

    @staticmethod
    def get_packaging(name: str) -> Optional[PackagingTech]:
        return PACKAGING_TECHNOLOGIES.get(name)

    @staticmethod
    def get_all_packaging() -> dict[str, PackagingTech]:
        return PACKAGING_TECHNOLOGIES

    @staticmethod
    def get_wafer_spec(diameter: str = "300mm") -> WaferSpec:
        return WAFER_SPECS.get(diameter, WAFER_SPECS["300mm"])

    @staticmethod
    def get_yield_model(name: str) -> Optional[YieldModelParams]:
        return YIELD_MODELS.get(name)

    @staticmethod
    def get_oee_standards() -> dict[str, OEEDefinition]:
        return OEE_STANDARDS

    @staticmethod
    def calculate_gross_die_per_wafer(
        die_width_mm: float,
        die_height_mm: float,
        wafer_diameter_mm: int = 300,
        scribe_lane_mm: float = 0.1,
        edge_exclusion_mm: float = 3.0
    ) -> int:
        """
        웨이퍼당 총 다이 수 계산 (업계 표준 공식)

        Gross Die = π * (d/2 - e)² / (W * H) - π * (d/2 - e) / √(W² + H²)
        """
        import math
        r = (wafer_diameter_mm / 2) - edge_exclusion_mm
        w = die_width_mm + scribe_lane_mm
        h = die_height_mm + scribe_lane_mm

        # 표준 근사 공식
        usable_area = math.pi * r * r
        die_area = w * h
        edge_loss = math.pi * r / math.sqrt(w * w + h * h)

        gross_die = int(usable_area / die_area - edge_loss)
        return max(0, gross_die)
