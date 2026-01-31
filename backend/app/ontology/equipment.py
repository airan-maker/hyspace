"""
Semiconductor Equipment Knowledge Base

장비 제조사, 사양, MTBF, 유지보수 주기 지식 체계

Sources:
- SEMI Equipment Market Data
- Published vendor specifications
- Industry benchmarks
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class EquipCategory(str, Enum):
    LITHOGRAPHY = "LITHOGRAPHY"
    ETCH = "ETCH"
    DEPOSITION = "DEPOSITION"  # CVD, PVD, ALD, EPI
    CMP = "CMP"
    ION_IMPLANT = "ION_IMPLANT"
    CLEAN = "CLEAN"
    METROLOGY = "METROLOGY"
    INSPECTION = "INSPECTION"
    THERMAL = "THERMAL"         # Furnace, RTP
    TEST = "TEST"


class VendorRegion(str, Enum):
    NETHERLANDS = "Netherlands"
    JAPAN = "Japan"
    USA = "USA"
    SOUTH_KOREA = "South Korea"


@dataclass
class EquipmentVendorInfo:
    """장비 제조사 정보"""
    name: str
    headquarter: VendorRegion
    market_share_pct: Optional[float]  # 해당 카테고리 내 점유율
    export_controlled: bool = False


@dataclass
class MaintenanceProfile:
    """유지보수 프로파일"""
    pm_interval_hours: int              # 예방 정비 주기 (시간)
    pm_duration_hours: float            # PM 소요 시간
    annual_pm_count: int                # 연간 PM 횟수
    consumables_per_pm: list[str]       # PM 시 교체 부품
    major_overhaul_interval_months: int # 대정비 주기 (월)
    major_overhaul_duration_days: int   # 대정비 소요 일수


@dataclass
class EquipmentSpec:
    """장비 사양"""
    name: str
    model: str
    vendor: EquipmentVendorInfo
    category: EquipCategory

    # Performance
    throughput_wph: int                         # Wafers per Hour
    process_capability: list[str]               # 처리 가능 공정
    min_node_nm: int                            # 최소 지원 노드

    # Physical
    footprint_m2: float                         # 설치 면적
    weight_tons: float
    power_consumption_kw: float
    cleanroom_class: str                        # ISO Class 1-5

    # Reliability
    mtbf_hours: int                             # Mean Time Between Failures
    mttr_hours: float                           # Mean Time To Repair
    annual_uptime_pct: float                    # 연간 가동률
    maintenance: MaintenanceProfile

    # Cost
    purchase_price_million_usd: float
    annual_maintenance_cost_usd: int            # 연간 유지비
    consumables_annual_cost_usd: int

    # Supply
    lead_time_months: int                       # 발주~설치 리드타임
    annual_production_units: Optional[int]       # 연간 생산량 (해당 모델)

    description: str = ""


# ============================================================
# Equipment Database
# ============================================================

EQUIPMENT_DB: dict[str, EquipmentSpec] = {
    # === LITHOGRAPHY ===
    "ASML_NXE3800E": EquipmentSpec(
        name="ASML NXE:3800E",
        model="NXE:3800E",
        vendor=EquipmentVendorInfo("ASML", VendorRegion.NETHERLANDS, 100.0, True),
        category=EquipCategory.LITHOGRAPHY,
        throughput_wph=220,
        process_capability=["EUV_SINGLE_EXPOSURE", "EUV_MULTI_PATTERNING"],
        min_node_nm=3,
        footprint_m2=120,
        weight_tons=180,
        power_consumption_kw=1200,
        cleanroom_class="ISO Class 4",
        mtbf_hours=500,
        mttr_hours=8,
        annual_uptime_pct=85,
        maintenance=MaintenanceProfile(
            pm_interval_hours=500,
            pm_duration_hours=8,
            annual_pm_count=17,
            consumables_per_pm=["Tin droplet generator", "Collector mirror", "Pellicle"],
            major_overhaul_interval_months=12,
            major_overhaul_duration_days=14
        ),
        purchase_price_million_usd=380,
        annual_maintenance_cost_usd=30_000_000,
        consumables_annual_cost_usd=15_000_000,
        lead_time_months=24,
        annual_production_units=50,
        description="최신 EUV 리소그래피, NA=0.33, 220 WPH. 전세계 유일 EUV 공급사"
    ),
    "ASML_EXE5000": EquipmentSpec(
        name="ASML EXE:5000 (High-NA EUV)",
        model="EXE:5000",
        vendor=EquipmentVendorInfo("ASML", VendorRegion.NETHERLANDS, 100.0, True),
        category=EquipCategory.LITHOGRAPHY,
        throughput_wph=185,
        process_capability=["HIGH_NA_EUV", "SINGLE_EXPOSURE_2NM"],
        min_node_nm=2,
        footprint_m2=150,
        weight_tons=250,
        power_consumption_kw=1500,
        cleanroom_class="ISO Class 4",
        mtbf_hours=400,
        mttr_hours=12,
        annual_uptime_pct=80,
        maintenance=MaintenanceProfile(
            pm_interval_hours=400,
            pm_duration_hours=12,
            annual_pm_count=20,
            consumables_per_pm=["Tin droplet generator", "Collector mirror", "High-NA optics"],
            major_overhaul_interval_months=6,
            major_overhaul_duration_days=21
        ),
        purchase_price_million_usd=400,
        annual_maintenance_cost_usd=40_000_000,
        consumables_annual_cost_usd=20_000_000,
        lead_time_months=36,
        annual_production_units=20,
        description="High-NA EUV (NA=0.55), 2nm 이하 싱글 패터닝. 2025 초도 출하"
    ),

    # === ETCH ===
    "LAM_KIYO_FX": EquipmentSpec(
        name="Lam Research Kiyo FX",
        model="Kiyo FX",
        vendor=EquipmentVendorInfo("Lam Research", VendorRegion.USA, 45.0),
        category=EquipCategory.ETCH,
        throughput_wph=120,
        process_capability=["CONDUCTOR_ETCH", "DIELECTRIC_ETCH", "ALE"],
        min_node_nm=3,
        footprint_m2=25,
        weight_tons=8,
        power_consumption_kw=80,
        cleanroom_class="ISO Class 5",
        mtbf_hours=2000,
        mttr_hours=4,
        annual_uptime_pct=92,
        maintenance=MaintenanceProfile(
            pm_interval_hours=2000,
            pm_duration_hours=4,
            annual_pm_count=4,
            consumables_per_pm=["ESC (Electrostatic Chuck)", "Edge ring", "Gas distribution plate"],
            major_overhaul_interval_months=18,
            major_overhaul_duration_days=5
        ),
        purchase_price_million_usd=8,
        annual_maintenance_cost_usd=1_200_000,
        consumables_annual_cost_usd=800_000,
        lead_time_months=9,
        annual_production_units=500,
        description="첨단 로직/메모리 도체 식각 장비, ALE (Atomic Layer Etch) 지원"
    ),
    "TEL_TACTRAS": EquipmentSpec(
        name="Tokyo Electron Tactras",
        model="Tactras",
        vendor=EquipmentVendorInfo("Tokyo Electron (TEL)", VendorRegion.JAPAN, 30.0),
        category=EquipCategory.ETCH,
        throughput_wph=100,
        process_capability=["CONDUCTOR_ETCH", "HAR_ETCH"],
        min_node_nm=5,
        footprint_m2=22,
        weight_tons=7,
        power_consumption_kw=70,
        cleanroom_class="ISO Class 5",
        mtbf_hours=2500,
        mttr_hours=3,
        annual_uptime_pct=93,
        maintenance=MaintenanceProfile(
            pm_interval_hours=2500,
            pm_duration_hours=3,
            annual_pm_count=3,
            consumables_per_pm=["Focus ring", "Upper electrode", "O-ring kit"],
            major_overhaul_interval_months=18,
            major_overhaul_duration_days=5
        ),
        purchase_price_million_usd=7,
        annual_maintenance_cost_usd=1_000_000,
        consumables_annual_cost_usd=600_000,
        lead_time_months=8,
        annual_production_units=400,
        description="고종횡비(HAR) 식각 전문, 3D NAND 핵심 장비"
    ),

    # === DEPOSITION (CVD) ===
    "AMAT_PRODUCER_GT": EquipmentSpec(
        name="Applied Materials Producer GT",
        model="Producer GT",
        vendor=EquipmentVendorInfo("Applied Materials", VendorRegion.USA, 35.0),
        category=EquipCategory.DEPOSITION,
        throughput_wph=80,
        process_capability=["PECVD", "SACVD", "FCVD", "LOW_K_CVD"],
        min_node_nm=3,
        footprint_m2=30,
        weight_tons=10,
        power_consumption_kw=100,
        cleanroom_class="ISO Class 5",
        mtbf_hours=3000,
        mttr_hours=3,
        annual_uptime_pct=94,
        maintenance=MaintenanceProfile(
            pm_interval_hours=3000,
            pm_duration_hours=3,
            annual_pm_count=3,
            consumables_per_pm=["Showerhead", "Heater", "Gas line kit"],
            major_overhaul_interval_months=24,
            major_overhaul_duration_days=7
        ),
        purchase_price_million_usd=6,
        annual_maintenance_cost_usd=900_000,
        consumables_annual_cost_usd=500_000,
        lead_time_months=6,
        annual_production_units=800,
        description="범용 CVD 증착, Low-k 절연막 증착 포함"
    ),

    # === CMP ===
    "AMAT_REFLEXION_LK": EquipmentSpec(
        name="Applied Materials Reflexion LK Prime",
        model="Reflexion LK Prime",
        vendor=EquipmentVendorInfo("Applied Materials", VendorRegion.USA, 60.0),
        category=EquipCategory.CMP,
        throughput_wph=60,
        process_capability=["OXIDE_CMP", "METAL_CMP", "STI_CMP", "BARRIER_CMP"],
        min_node_nm=3,
        footprint_m2=35,
        weight_tons=12,
        power_consumption_kw=60,
        cleanroom_class="ISO Class 5",
        mtbf_hours=2500,
        mttr_hours=2,
        annual_uptime_pct=93,
        maintenance=MaintenanceProfile(
            pm_interval_hours=2500,
            pm_duration_hours=2,
            annual_pm_count=3,
            consumables_per_pm=["Polishing pad", "Slurry supply line", "Conditioning disk"],
            major_overhaul_interval_months=12,
            major_overhaul_duration_days=3
        ),
        purchase_price_million_usd=5,
        annual_maintenance_cost_usd=800_000,
        consumables_annual_cost_usd=2_000_000,
        lead_time_months=6,
        annual_production_units=600,
        description="다중 헤드 CMP, 연마 패드·슬러리 소모품 비용이 주요 운영비"
    ),

    # === METROLOGY ===
    "KLA_8935": EquipmentSpec(
        name="KLA 8935 Patterned Wafer Inspection",
        model="8935",
        vendor=EquipmentVendorInfo("KLA", VendorRegion.USA, 55.0),
        category=EquipCategory.INSPECTION,
        throughput_wph=40,
        process_capability=["BRIGHTFIELD_INSPECTION", "DEFECT_DETECTION", "PATTERN_INSPECTION"],
        min_node_nm=3,
        footprint_m2=15,
        weight_tons=5,
        power_consumption_kw=30,
        cleanroom_class="ISO Class 5",
        mtbf_hours=4000,
        mttr_hours=2,
        annual_uptime_pct=96,
        maintenance=MaintenanceProfile(
            pm_interval_hours=4000,
            pm_duration_hours=2,
            annual_pm_count=2,
            consumables_per_pm=["Light source", "Optical calibration kit"],
            major_overhaul_interval_months=24,
            major_overhaul_duration_days=3
        ),
        purchase_price_million_usd=15,
        annual_maintenance_cost_usd=2_000_000,
        consumables_annual_cost_usd=500_000,
        lead_time_months=6,
        annual_production_units=200,
        description="Broadband plasma 광원 웨이퍼 검사, 3nm 결함 감지 지원"
    ),
}


# ============================================================
# Vendor Market Share Summary
# ============================================================

VENDOR_MARKET_SHARE = {
    EquipCategory.LITHOGRAPHY: {
        "ASML": {"share_pct": 90, "products": ["EUV", "DUV (ArFi, KrF)"]},
        "Nikon": {"share_pct": 7, "products": ["DUV (ArFi)"]},
        "Canon": {"share_pct": 3, "products": ["DUV (KrF, i-line)"]},
    },
    EquipCategory.ETCH: {
        "Lam Research": {"share_pct": 45, "products": ["Conductor/Dielectric Etch"]},
        "Tokyo Electron": {"share_pct": 30, "products": ["HAR Etch"]},
        "Applied Materials": {"share_pct": 20, "products": ["Etch"]},
    },
    EquipCategory.DEPOSITION: {
        "Applied Materials": {"share_pct": 35, "products": ["CVD, PVD, EPI"]},
        "Lam Research": {"share_pct": 25, "products": ["ALD, CVD"]},
        "Tokyo Electron": {"share_pct": 20, "products": ["CVD, ALD"]},
        "ASM International": {"share_pct": 15, "products": ["ALD specialist"]},
    },
    EquipCategory.CMP: {
        "Applied Materials": {"share_pct": 60, "products": ["Reflexion series"]},
        "Ebara": {"share_pct": 25, "products": ["FREX series"]},
        "KCTECH": {"share_pct": 10, "products": ["CMP"]},
    },
    EquipCategory.INSPECTION: {
        "KLA": {"share_pct": 55, "products": ["Broadband, E-beam"]},
        "Applied Materials": {"share_pct": 20, "products": ["E-beam review"]},
        "Hitachi High-Tech": {"share_pct": 15, "products": ["CD-SEM"]},
    },
}


# ============================================================
# Lookup Interface
# ============================================================

class EquipmentKnowledgeBase:
    """장비 지식 베이스 인터페이스"""

    @staticmethod
    def get_all_equipment() -> dict[str, EquipmentSpec]:
        return EQUIPMENT_DB

    @staticmethod
    def get_equipment(model_key: str) -> Optional[EquipmentSpec]:
        return EQUIPMENT_DB.get(model_key)

    @staticmethod
    def get_by_category(category: EquipCategory) -> list[EquipmentSpec]:
        return [e for e in EQUIPMENT_DB.values() if e.category == category]

    @staticmethod
    def get_vendor_market_share(category: EquipCategory) -> dict:
        return VENDOR_MARKET_SHARE.get(category, {})

    @staticmethod
    def estimate_fab_equipment_cost(
        node_nm: int,
        wafer_starts_per_month: int = 50000
    ) -> dict:
        """
        Fab 장비 투자비 추정

        Industry benchmark:
        - 5nm fab (50K WSPM): ~$15-20B
        - 3nm fab (50K WSPM): ~$20-25B
        - 2nm fab (50K WSPM): ~$28-35B
        """
        base_costs = {
            2: 30_000, 3: 22_000, 5: 17_000,
            7: 12_000, 10: 8_000, 14: 5_000
        }
        base_million = base_costs.get(node_nm, 10_000)
        scale_factor = wafer_starts_per_month / 50000

        litho_pct = 0.35 if node_nm <= 5 else 0.25
        etch_dep_pct = 0.30
        other_pct = 1.0 - litho_pct - etch_dep_pct

        total = base_million * scale_factor

        return {
            "node_nm": node_nm,
            "wspm": wafer_starts_per_month,
            "total_capex_million_usd": round(total),
            "breakdown": {
                "lithography_million_usd": round(total * litho_pct),
                "etch_deposition_million_usd": round(total * etch_dep_pct),
                "metrology_inspection_million_usd": round(total * 0.10),
                "other_million_usd": round(total * (other_pct - 0.10)),
            },
            "note": f"{node_nm}nm, {wafer_starts_per_month:,} WSPM 기준 추정"
        }
