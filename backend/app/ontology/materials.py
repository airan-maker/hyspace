"""
Semiconductor Materials Knowledge Base

반도체 제조에 사용되는 핵심 소재 및 화학물질 지식 체계

Sources:
- SEMI Standards
- ITRS/IRDS Materials Roadmap
- Industry supplier data
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class MaterialCategory(str, Enum):
    WAFER = "WAFER"                     # 기판
    PHOTORESIST = "PHOTORESIST"         # 감광액
    GAS = "PROCESS_GAS"                 # 공정 가스
    CHEMICAL = "WET_CHEMICAL"           # 습식 세정 화학물질
    METAL_TARGET = "METAL_TARGET"       # 금속 타겟 (PVD)
    PRECURSOR = "CVD_PRECURSOR"         # CVD 전구체
    CMP_SLURRY = "CMP_SLURRY"          # CMP 슬러리
    MASK = "PHOTOMASK"                  # 포토마스크
    DIELECTRIC = "DIELECTRIC"           # 절연재
    PACKAGING = "PACKAGING_MATERIAL"    # 패키징 소재


class CriticalityLevel(str, Enum):
    CRITICAL = "CRITICAL"       # 대체 불가, 단일 공급원
    HIGH = "HIGH"               # 대체 어려움, 소수 공급원
    MEDIUM = "MEDIUM"           # 대체 가능하나 인증 필요
    LOW = "LOW"                 # 범용 소재


class SupplyRiskLevel(str, Enum):
    VERY_HIGH = "VERY_HIGH"     # 지정학적 위험 + 소수 공급
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class MaterialSpec:
    """반도체 소재 사양"""
    name: str
    chemical_formula: Optional[str]
    category: MaterialCategory
    criticality: CriticalityLevel
    supply_risk: SupplyRiskLevel

    # 용도
    process_steps: list[str]                    # 사용되는 공정 단계
    typical_purity: Optional[str] = None        # 순도 (e.g., "99.9999%", "SEMI Grade 5")

    # 공급망
    major_suppliers: list[str] = field(default_factory=list)
    geographic_concentration: str = ""           # 주요 생산 지역
    lead_time_weeks: int = 4                    # 리드타임
    annual_consumption_per_fab: str = ""         # Fab당 연간 소비량 (대략)

    # 비용
    unit_cost_range: str = ""                   # 단가 범위
    cost_trend: str = ""                        # 가격 추세

    # 규제/환경
    hazard_class: Optional[str] = None          # 유해물질 분류
    pfas_related: bool = False                  # PFAS 규제 대상 여부
    export_controlled: bool = False             # 수출 통제 대상

    description: str = ""


# ============================================================
# Critical Materials Database
# ============================================================

MATERIALS: dict[str, MaterialSpec] = {
    # --- Photoresists ---
    "EUV_RESIST": MaterialSpec(
        name="EUV Photoresist",
        chemical_formula="CAR (Chemically Amplified Resist)",
        category=MaterialCategory.PHOTORESIST,
        criticality=CriticalityLevel.CRITICAL,
        supply_risk=SupplyRiskLevel.VERY_HIGH,
        process_steps=["EUV_LITHOGRAPHY"],
        typical_purity="Particle < 50 per mL (≥0.1µm)",
        major_suppliers=["JSR", "Tokyo Ohka Kogyo (TOK)", "Shin-Etsu Chemical", "Fujifilm"],
        geographic_concentration="일본 100% (JSR: 30%, TOK: 25%, Shin-Etsu: 20%)",
        lead_time_weeks=12,
        annual_consumption_per_fab="200-500 리터/월",
        unit_cost_range="$5,000-15,000/리터",
        cost_trend="연 10-15% 상승 (EUV 전환 가속)",
        export_controlled=True,
        description="EUV 노광용 감광액, 일본 4사 독점. 2024년 JSR → JIC 인수로 공급 재편"
    ),
    "ArF_RESIST": MaterialSpec(
        name="ArF Immersion Photoresist",
        chemical_formula="ArF CAR",
        category=MaterialCategory.PHOTORESIST,
        criticality=CriticalityLevel.HIGH,
        supply_risk=SupplyRiskLevel.HIGH,
        process_steps=["DUV_LITHOGRAPHY", "IMMERSION_LITHOGRAPHY"],
        typical_purity="Particle < 30 per mL (≥0.1µm)",
        major_suppliers=["JSR", "TOK", "Dow Chemical", "Merck (AZ)"],
        geographic_concentration="일본 70%, 미국 20%, 독일 10%",
        lead_time_weeks=8,
        annual_consumption_per_fab="500-1000 리터/월",
        unit_cost_range="$2,000-5,000/리터",
        cost_trend="안정 (성숙 기술)",
        description="ArF (193nm) DUV 노광용, EUV 비적용 레이어에 계속 사용"
    ),

    # --- Process Gases ---
    "NF3": MaterialSpec(
        name="Nitrogen Trifluoride",
        chemical_formula="NF₃",
        category=MaterialCategory.GAS,
        criticality=CriticalityLevel.HIGH,
        supply_risk=SupplyRiskLevel.MEDIUM,
        process_steps=["CVD_CHAMBER_CLEAN", "ETCH"],
        typical_purity="99.999% (5N)",
        major_suppliers=["SK Materials", "Kanto Denka", "Hyosung", "Linde"],
        geographic_concentration="한국 40%, 일본 30%, 미국 20%",
        lead_time_weeks=6,
        annual_consumption_per_fab="300-600 톤/년",
        unit_cost_range="$15-30/kg",
        cost_trend="안정",
        hazard_class="온실가스 (GWP: 17,200)",
        description="CVD 챔버 세정용 불소 가스, 온실가스로 사용량 절감 추세"
    ),
    "SILANE": MaterialSpec(
        name="Silane",
        chemical_formula="SiH₄",
        category=MaterialCategory.GAS,
        criticality=CriticalityLevel.HIGH,
        supply_risk=SupplyRiskLevel.MEDIUM,
        process_steps=["CVD", "PECVD", "EPITAXY"],
        typical_purity="99.9999% (6N)",
        major_suppliers=["REC Silicon", "Tokuyama", "SK Materials", "Shin-Etsu"],
        geographic_concentration="미국 30%, 일본 30%, 한국 25%",
        lead_time_weeks=8,
        annual_consumption_per_fab="100-300 톤/년",
        unit_cost_range="$50-150/kg",
        cost_trend="상승 (태양전지 수요 증가)",
        hazard_class="자연 발화성 가스 (pyrophoric)",
        description="실리콘 박막 증착용 핵심 가스, 태양전지 시장과 수요 경합"
    ),
    "WF6": MaterialSpec(
        name="Tungsten Hexafluoride",
        chemical_formula="WF₆",
        category=MaterialCategory.GAS,
        criticality=CriticalityLevel.CRITICAL,
        supply_risk=SupplyRiskLevel.HIGH,
        process_steps=["W_CVD", "CONTACT_FILL"],
        typical_purity="99.999% (5N)",
        major_suppliers=["Linde", "SK Materials", "Stella Chemifa"],
        geographic_concentration="미국 30%, 한국 30%, 일본 25%",
        lead_time_weeks=10,
        annual_consumption_per_fab="50-150 톤/년",
        unit_cost_range="$200-400/kg",
        cost_trend="상승 (텅스텐 원자재 가격 연동)",
        hazard_class="독성, 부식성",
        description="텅스텐 배선 증착용, 3D NAND 고단화로 수요 급증"
    ),

    # --- Wet Chemicals ---
    "HF": MaterialSpec(
        name="Hydrofluoric Acid",
        chemical_formula="HF",
        category=MaterialCategory.CHEMICAL,
        criticality=CriticalityLevel.HIGH,
        supply_risk=SupplyRiskLevel.HIGH,
        process_steps=["WET_ETCH", "CLEAN", "OXIDE_REMOVAL"],
        typical_purity="SEMI Grade 4 (UP-SSSS)",
        major_suppliers=["Stella Chemifa", "Morita Chemical", "Solvay", "Honeywell"],
        geographic_concentration="일본 50% (형석 원료: 중국 60%)",
        lead_time_weeks=8,
        annual_consumption_per_fab="200-500 톤/년",
        unit_cost_range="$500-2,000/톤",
        cost_trend="불안정 (형석 가격 변동)",
        hazard_class="맹독성, 부식성",
        export_controlled=True,
        description="실리콘 산화막 식각 핵심 화학물질, 일본 수출규제 대상 (2019)"
    ),
    "H2O2": MaterialSpec(
        name="Hydrogen Peroxide (EL Grade)",
        chemical_formula="H₂O₂",
        category=MaterialCategory.CHEMICAL,
        criticality=CriticalityLevel.MEDIUM,
        supply_risk=SupplyRiskLevel.LOW,
        process_steps=["SC1_CLEAN", "SC2_CLEAN", "SPM_CLEAN"],
        typical_purity="SEMI Grade 5",
        major_suppliers=["Evonik", "Mitsubishi Gas Chemical", "Solvay", "Arkema"],
        geographic_concentration="글로벌 분산",
        lead_time_weeks=4,
        annual_consumption_per_fab="500-1500 톤/년",
        unit_cost_range="$200-500/톤",
        description="RCA 세정 (SC1/SC2)의 핵심 성분"
    ),

    # --- CMP ---
    "CMP_OXIDE_SLURRY": MaterialSpec(
        name="CMP Oxide Slurry (Ceria-based)",
        chemical_formula="CeO₂ based",
        category=MaterialCategory.CMP_SLURRY,
        criticality=CriticalityLevel.CRITICAL,
        supply_risk=SupplyRiskLevel.VERY_HIGH,
        process_steps=["CMP_STI", "CMP_ILD", "CMP_OXIDE"],
        major_suppliers=["CMC Materials (Entegris)", "Fujimi", "Hitachi Chemical"],
        geographic_concentration="미국 40%, 일본 40%",
        lead_time_weeks=8,
        annual_consumption_per_fab="100-300 톤/년",
        unit_cost_range="$50-200/kg",
        cost_trend="상승 (세리아 희토류 가격 연동)",
        description="산화막 CMP 연마용, 세리아(CeO₂) 기반 슬러리. 희토류 의존"
    ),

    # --- Photomask ---
    "EUV_MASK_BLANK": MaterialSpec(
        name="EUV Mask Blank",
        chemical_formula="Mo/Si 다층막 on Quartz",
        category=MaterialCategory.MASK,
        criticality=CriticalityLevel.CRITICAL,
        supply_risk=SupplyRiskLevel.VERY_HIGH,
        process_steps=["EUV_LITHOGRAPHY"],
        major_suppliers=["AGC (Asahi Glass)", "Hoya"],
        geographic_concentration="일본 100% (AGC 70%, Hoya 30%)",
        lead_time_weeks=16,
        unit_cost_range="$300,000-500,000/장",
        cost_trend="안정 (독점 시장)",
        description="EUV 마스크 기판, Mo/Si 40쌍 다층 반사막. 전세계 2개사 독점"
    ),

    # --- Metal Targets ---
    "COBALT_TARGET": MaterialSpec(
        name="Cobalt Sputtering Target",
        chemical_formula="Co",
        category=MaterialCategory.METAL_TARGET,
        criticality=CriticalityLevel.HIGH,
        supply_risk=SupplyRiskLevel.HIGH,
        process_steps=["PVD_BARRIER", "CONTACT"],
        typical_purity="99.9999% (6N)",
        major_suppliers=["Tosoh", "JX Nippon Mining", "Praxair"],
        geographic_concentration="콩고민주공화국 원료 70%",
        lead_time_weeks=12,
        unit_cost_range="$5,000-15,000/타겟",
        cost_trend="불안정 (DRC 정치 리스크)",
        description="10nm 이하 배선 배리어/라이너, Cu→Co 전환 추세"
    ),
    "RUTHENIUM_TARGET": MaterialSpec(
        name="Ruthenium Sputtering Target",
        chemical_formula="Ru",
        category=MaterialCategory.METAL_TARGET,
        criticality=CriticalityLevel.CRITICAL,
        supply_risk=SupplyRiskLevel.VERY_HIGH,
        process_steps=["PVD_LINER", "EUV_PELLICLE"],
        typical_purity="99.999% (5N)",
        major_suppliers=["Heraeus", "Furuya Metal"],
        geographic_concentration="남아프리카공화국 원료 90%",
        lead_time_weeks=16,
        unit_cost_range="$10,000-50,000/타겟",
        cost_trend="급상승 (EUV 펠리클 수요)",
        description="차세대 배선 라이너 + EUV 펠리클 소재, 남아공 의존도 극대"
    ),
}


# ============================================================
# Lookup Interface
# ============================================================

class MaterialsKnowledgeBase:
    """소재 지식 베이스 인터페이스"""

    @staticmethod
    def get_all_materials() -> dict[str, MaterialSpec]:
        return MATERIALS

    @staticmethod
    def get_material(name: str) -> Optional[MaterialSpec]:
        return MATERIALS.get(name)

    @staticmethod
    def get_by_category(category: MaterialCategory) -> list[MaterialSpec]:
        return [m for m in MATERIALS.values() if m.category == category]

    @staticmethod
    def get_critical_materials() -> list[MaterialSpec]:
        return [m for m in MATERIALS.values()
                if m.criticality == CriticalityLevel.CRITICAL]

    @staticmethod
    def get_high_risk_materials() -> list[MaterialSpec]:
        return [m for m in MATERIALS.values()
                if m.supply_risk in (SupplyRiskLevel.VERY_HIGH, SupplyRiskLevel.HIGH)]

    @staticmethod
    def get_export_controlled() -> list[MaterialSpec]:
        return [m for m in MATERIALS.values() if m.export_controlled]

    @staticmethod
    def get_japan_dependent() -> list[MaterialSpec]:
        """일본 의존도가 높은 소재 (2019 수출규제 관련)"""
        return [m for m in MATERIALS.values()
                if "일본" in m.geographic_concentration
                and any(pct in m.geographic_concentration
                        for pct in ["100%", "70%", "80%", "90%", "50%"])]

    @staticmethod
    def get_materials_for_process(process_step: str) -> list[MaterialSpec]:
        return [m for m in MATERIALS.values()
                if process_step in m.process_steps]
