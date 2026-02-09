"""
Research Agent Configuration

리서치 토픽 정의, Tier별 수집 대상, 소스 URL 관리
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Tier(str, Enum):
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"


class TopicStatus(str, Enum):
    PENDING = "pending"
    COLLECTING = "collecting"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ResearchSource:
    """리서치 데이터 소스"""
    name: str
    url: str
    source_type: str  # "wikichip", "wikipedia", "press_release", "spec_doc", "news"
    description: str
    priority: int = 1  # 1=highest
    reliability: float = 0.7  # 0.0~1.0 소스 신뢰도


@dataclass
class ResearchTopic:
    """리서치 토픽 정의"""
    topic_id: str
    name: str
    name_kr: str
    tier: Tier
    node_labels: list[str]
    relationship_types: list[str]
    description: str
    sources: list[ResearchSource] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    status: TopicStatus = TopicStatus.PENDING


# ============================================================
# Tier 1 Topics — 기존 스키마와 직접 연결
# ============================================================

TIER1_TOPICS = {
    "foundry_fabsite": ResearchTopic(
        topic_id="foundry_fabsite",
        name="Foundry & Fab Sites",
        name_kr="파운드리 및 팹 사이트",
        tier=Tier.TIER1,
        node_labels=["Foundry", "FabSite"],
        relationship_types=["OPERATES_FAB", "PRODUCES_ON"],
        description="주요 파운드리 기업 정보 및 전세계 팹 위치/캐파",
        sources=[
            ResearchSource("Wikipedia - TSMC", "https://en.wikipedia.org/wiki/TSMC", "wikipedia", "TSMC 파운드리 정보", reliability=0.85),
            ResearchSource("Wikipedia - Samsung", "https://en.wikipedia.org/wiki/Samsung_Electronics", "wikipedia", "Samsung 반도체 정보", reliability=0.85),
            ResearchSource("Wikipedia - Intel", "https://en.wikipedia.org/wiki/Intel", "wikipedia", "Intel 파운드리 정보", reliability=0.85),
            ResearchSource("Wikipedia - GlobalFoundries", "https://en.wikipedia.org/wiki/GlobalFoundries", "wikipedia", "GlobalFoundries 정보", reliability=0.85),
            ResearchSource("Wikipedia - SMIC", "https://en.wikipedia.org/wiki/Semiconductor_Manufacturing_International_Corporation", "wikipedia", "SMIC 정보", reliability=0.85),
            ResearchSource("Wikipedia - UMC", "https://en.wikipedia.org/wiki/United_Microelectronics_Corporation", "wikipedia", "UMC 정보", reliability=0.85),
            ResearchSource("WikiChip - TSMC", "https://en.wikichip.org/wiki/tsmc", "wikichip", "TSMC 상세 스펙", reliability=0.80),
            ResearchSource("WikiChip - Intel", "https://en.wikichip.org/wiki/intel", "wikichip", "Intel 상세 스펙", reliability=0.80),
            ResearchSource("TSMC Technology", "https://www.tsmc.com/english/dedicatedFoundry/technology/logic", "corporate_tech", "TSMC 공식 기술 페이지", reliability=0.90),
        ],
        search_queries=[
            "TSMC fab locations capacity 2025 2026",
            "Samsung foundry fab sites worldwide capacity 2026",
            "Intel foundry fabs Oregon Arizona Ohio Ireland 2026",
            "GlobalFoundries SMIC UMC foundry market share 2026",
            "semiconductor foundry market share revenue 2026",
            "TSMC Arizona fab production timeline 2026",
            "Samsung Taylor Texas fab construction update 2026",
            "Intel Ohio mega fab progress 2026",
        ],
    ),
    "process_generation": ResearchTopic(
        topic_id="process_generation",
        name="Process Technology Generations",
        name_kr="공정 기술 세대",
        tier=Tier.TIER1,
        node_labels=["ProcessGeneration"],
        relationship_types=["GENERATION_OF"],
        description="FinFET→GAA→CFET 트랜지스터 세대별 특성, IRDS 로드맵",
        sources=[
            ResearchSource("Wikipedia - FinFET", "https://en.wikipedia.org/wiki/Fin_field-effect_transistor", "wikipedia", "FinFET 트랜지스터", reliability=0.85),
            ResearchSource("Wikipedia - Multigate (GAA)", "https://en.wikipedia.org/wiki/Multigate_device", "wikipedia", "GAA/나노시트 트랜지스터", reliability=0.85),
            ResearchSource("Wikipedia - EUV Lithography", "https://en.wikipedia.org/wiki/Extreme_ultraviolet_lithography", "wikipedia", "EUV 리소그래피", reliability=0.85),
            ResearchSource("WikiChip - 2nm", "https://en.wikichip.org/wiki/2_nm_lithography_process", "wikichip", "2nm 공정 상세", reliability=0.80),
            ResearchSource("WikiChip - 3nm", "https://en.wikichip.org/wiki/3_nm_lithography_process", "wikichip", "3nm 공정 상세", reliability=0.80),
        ],
        search_queries=[
            "IRDS semiconductor roadmap 2025 2026 transistor density",
            "FinFET vs GAA nanosheet vs CFET comparison",
            "TSMC N2 A16 N1.4 process technology specs 2026",
            "Samsung SF2 SF1.4 process node roadmap 2026",
            "Intel 18A 14A process technology features 2026",
            "backside power delivery BSPDN technology 2026",
            "High-NA EUV lithography ASML EXE:5000 adoption 2026",
            "CFET complementary FET research progress 2026",
        ],
    ),
    "memory_standard": ResearchTopic(
        topic_id="memory_standard",
        name="Memory Standards & Specifications",
        name_kr="메모리 규격 상세",
        tier=Tier.TIER1,
        node_labels=["MemoryStandard"],
        relationship_types=["IMPLEMENTS", "USES_MEMORY_STANDARD"],
        description="JEDEC DDR/LPDDR/GDDR/HBM 규격, CXL 메모리 확장",
        sources=[
            ResearchSource("Wikipedia - HBM", "https://en.wikipedia.org/wiki/High_Bandwidth_Memory", "wikipedia", "HBM 세대별 스펙", reliability=0.85),
            ResearchSource("Wikipedia - DDR5", "https://en.wikipedia.org/wiki/DDR5_SDRAM", "wikipedia", "DDR5 표준", reliability=0.85),
            ResearchSource("Wikipedia - GDDR7", "https://en.wikipedia.org/wiki/GDDR7_SDRAM", "wikipedia", "GDDR7 표준", reliability=0.85),
            ResearchSource("Wikipedia - LPDDR", "https://en.wikipedia.org/wiki/LPDDR", "wikipedia", "LPDDR 시리즈", reliability=0.85),
            ResearchSource("JEDEC Standards", "https://www.jedec.org/standards-documents", "standards_org", "JEDEC 표준 문서 목록", reliability=0.90),
        ],
        search_queries=[
            "JEDEC HBM4 specification 2025 2026",
            "DDR5 LPDDR5X GDDR7 specification comparison 2026",
            "HBM3E 12Hi 16Hi SK Hynix Samsung Micron specs 2026",
            "CXL 3.0 3.1 memory expansion specification",
            "JEDEC memory standards roadmap 2026",
            "HBM4 bandwidth capacity stacking technology 2026",
            "LPDDR6 specification draft JEDEC 2026",
        ],
    ),
    "interconnect_standard": ResearchTopic(
        topic_id="interconnect_standard",
        name="Interconnect Standards",
        name_kr="인터커넥트 규격",
        tier=Tier.TIER1,
        node_labels=["InterconnectStandard"],
        relationship_types=["USES_INTERCONNECT"],
        description="PCIe, CXL, UCIe, NVLink 등 칩간 인터커넥트 표준",
        sources=[
            ResearchSource("Wikipedia - PCIe", "https://en.wikipedia.org/wiki/PCI_Express", "wikipedia", "PCI Express 세대별", reliability=0.85),
            ResearchSource("Wikipedia - CXL", "https://en.wikipedia.org/wiki/Compute_Express_Link", "wikipedia", "CXL 표준", reliability=0.85),
            ResearchSource("Wikipedia - NVLink", "https://en.wikipedia.org/wiki/NVLink", "wikipedia", "NVIDIA NVLink", reliability=0.85),
            ResearchSource("Wikipedia - UCIe", "https://en.wikipedia.org/wiki/Universal_Chiplet_Interconnect_Express", "wikipedia", "UCIe 칩렛 인터커넥트", reliability=0.85),
        ],
        search_queries=[
            "PCIe 6.0 7.0 specification bandwidth 2026",
            "CXL 3.0 3.1 specification features adoption 2026",
            "UCIe 2.0 Universal Chiplet Interconnect Express 2026",
            "NVLink 5.0 6.0 NVIDIA specification bandwidth 2026",
            "UALink Ultra Accelerator Link specification 2026",
            "PCIe 7.0 specification timeline 2026",
        ],
    ),
    "packaging_detail": ResearchTopic(
        topic_id="packaging_detail",
        name="Advanced Packaging Deep Dive",
        name_kr="어드밴스드 패키징 상세",
        tier=Tier.TIER1,
        node_labels=["SubstrateType"],
        relationship_types=["USES_SUBSTRATE", "CONNECTS_VIA"],
        description="CoWoS/EMIB/Foveros 상세, 하이브리드 본딩, 기판 기술",
        sources=[
            ResearchSource("Wikipedia - 3D IC", "https://en.wikipedia.org/wiki/Three-dimensional_integrated_circuit", "wikipedia", "3D IC/패키징 기술", reliability=0.85),
            ResearchSource("Wikipedia - Chiplet", "https://en.wikipedia.org/wiki/Chiplet", "wikipedia", "칩렛 기술", reliability=0.85),
            ResearchSource("Wikipedia - SiP", "https://en.wikipedia.org/wiki/System_in_a_package", "wikipedia", "SiP 패키징", reliability=0.85),
        ],
        search_queries=[
            "TSMC CoWoS-L CoWoS-R advanced packaging 2026 capacity",
            "TSMC SoIC 3D stacking technology 2026",
            "Intel Foveros Direct EMIB packaging 2026",
            "hybrid bonding Cu-Cu semiconductor packaging 2026",
            "advanced packaging substrate ABF FC-BGA glass core 2026",
            "chiplet packaging UCIe integration 2026",
            "glass core substrate semiconductor packaging 2026",
        ],
    ),
}


# ============================================================
# Tier 2 Topics — 산업 생태계 확장
# ============================================================

TIER2_TOPICS = {
    "equipment_ecosystem": ResearchTopic(
        topic_id="equipment_ecosystem",
        name="Equipment Vendors & Models",
        name_kr="장비 벤더 및 모델",
        tier=Tier.TIER2,
        node_labels=["EquipmentVendor", "EquipmentModel"],
        relationship_types=["MANUFACTURES_EQUIP", "INSTANCE_OF"],
        description="ASML, LAM, TEL, AMAT, KLA 상세 장비 모델별 스펙",
        sources=[
            ResearchSource("Wikipedia - ASML", "https://en.wikipedia.org/wiki/ASML_Holding", "wikipedia", "ASML EUV 장비", reliability=0.85),
            ResearchSource("Wikipedia - Applied Materials", "https://en.wikipedia.org/wiki/Applied_Materials", "wikipedia", "AMAT 장비", reliability=0.85),
            ResearchSource("Wikipedia - Lam Research", "https://en.wikipedia.org/wiki/Lam_Research", "wikipedia", "Lam 식각 장비", reliability=0.85),
            ResearchSource("Wikipedia - Tokyo Electron", "https://en.wikipedia.org/wiki/Tokyo_Electron", "wikipedia", "TEL 장비", reliability=0.85),
            ResearchSource("Wikipedia - KLA", "https://en.wikipedia.org/wiki/KLA_Corporation", "wikipedia", "KLA 검사 장비", reliability=0.85),
            ResearchSource("Wikipedia - EUV", "https://en.wikipedia.org/wiki/Extreme_ultraviolet_lithography", "wikipedia", "EUV 리소그래피", reliability=0.85),
            ResearchSource("ASML News", "https://www.asml.com/en/news", "corporate_news", "ASML 최신 뉴스", reliability=0.80),
        ],
        search_queries=[
            "ASML EUV High-NA equipment models 2026 NXE NXT EXE",
            "Lam Research etch deposition equipment models 2026",
            "Tokyo Electron TEL semiconductor equipment lineup 2026",
            "Applied Materials AMAT equipment product portfolio 2026",
            "KLA inspection metrology equipment models 2026",
            "semiconductor equipment market share by vendor 2026",
            "ASML EXE:5200 High-NA EUV production 2026",
        ],
    ),
    "material_suppliers": ResearchTopic(
        topic_id="material_suppliers",
        name="Material Suppliers",
        name_kr="소재 공급업체",
        tier=Tier.TIER2,
        node_labels=["MaterialSupplier"],
        relationship_types=["SUPPLIES"],
        description="포토레지스트, 가스, CMP 슬러리 등 소재 공급사",
        sources=[
            ResearchSource("Wikipedia - Photoresist", "https://en.wikipedia.org/wiki/Photoresist", "wikipedia", "포토레지스트"),
            ResearchSource("Wikipedia - CMP", "https://en.wikipedia.org/wiki/Chemical-mechanical_polishing", "wikipedia", "CMP 공정"),
            ResearchSource("Wikipedia - Silicon Wafer", "https://en.wikipedia.org/wiki/Wafer_(electronics)", "wikipedia", "실리콘 웨이퍼"),
            ResearchSource("Wikipedia - CVD", "https://en.wikipedia.org/wiki/Chemical_vapor_deposition", "wikipedia", "CVD 소재"),
        ],
        search_queries=[
            "semiconductor photoresist suppliers JSR TOK Shin-Etsu market share 2026",
            "electronic specialty gas suppliers Air Liquide Linde 2026",
            "CMP slurry suppliers Fujimi Cabot Microelectronics 2026",
            "semiconductor materials supply chain market 2026",
            "silicon wafer suppliers Shin-Etsu SUMCO Siltronic SK Siltron 2026",
            "EUV photoresist market trends 2026",
        ],
    ),
    "design_ip": ResearchTopic(
        topic_id="design_ip",
        name="Design IP & EDA",
        name_kr="설계 IP 및 EDA",
        tier=Tier.TIER2,
        node_labels=["DesignIP"],
        relationship_types=["USES_IP"],
        description="ARM/RISC-V 코어 IP, Synopsys/Cadence EDA",
        sources=[
            ResearchSource("Wikipedia - ARM", "https://en.wikipedia.org/wiki/Arm_Holdings", "wikipedia", "ARM 아키텍처"),
            ResearchSource("Wikipedia - RISC-V", "https://en.wikipedia.org/wiki/RISC-V", "wikipedia", "RISC-V 오픈 ISA"),
            ResearchSource("Wikipedia - Synopsys", "https://en.wikipedia.org/wiki/Synopsys", "wikipedia", "Synopsys EDA"),
            ResearchSource("Wikipedia - Cadence", "https://en.wikipedia.org/wiki/Cadence_Design_Systems", "wikipedia", "Cadence EDA"),
            ResearchSource("Wikipedia - EDA", "https://en.wikipedia.org/wiki/Electronic_design_automation", "wikipedia", "EDA 산업 개요"),
        ],
        search_queries=[
            "ARM Cortex-X5 X6 CPU core IP 2026",
            "RISC-V processor IP SiFive Andes Ventana 2026",
            "Synopsys Cadence EDA tools market share 2026",
            "GPU IP Imagination ARM Mali 2026",
            "NPU IP Cadence Tensilica Synopsys ARC 2026",
            "SerDes PHY IP 224G Synopsys Cadence Alphawave 2026",
        ],
    ),
    "company_landscape": ResearchTopic(
        topic_id="company_landscape",
        name="Semiconductor Company Landscape",
        name_kr="반도체 기업 생태계",
        tier=Tier.TIER2,
        node_labels=["Company"],
        relationship_types=["DESIGNS", "OPERATES"],
        description="팹리스/IDM/파운드리/OSAT 기업 분류 및 시장 구조",
        sources=[
            ResearchSource("Wikipedia - Semiconductor Industry", "https://en.wikipedia.org/wiki/Semiconductor_industry", "wikipedia", "반도체 산업 구조"),
            ResearchSource("Wikipedia - Fabless", "https://en.wikipedia.org/wiki/Fabless_manufacturing", "wikipedia", "팹리스 모델"),
            ResearchSource("Wikipedia - OSAT", "https://en.wikipedia.org/wiki/Outsourced_semiconductor_assembly_and_test", "wikipedia", "OSAT 산업"),
            ResearchSource("Wikipedia - NVIDIA", "https://en.wikipedia.org/wiki/Nvidia", "wikipedia", "NVIDIA 기업"),
            ResearchSource("Wikipedia - AMD", "https://en.wikipedia.org/wiki/Advanced_Micro_Devices", "wikipedia", "AMD 기업"),
        ],
        search_queries=[
            "top semiconductor companies revenue 2026 ranking",
            "fabless semiconductor companies NVIDIA AMD Qualcomm Broadcom 2026",
            "IDM semiconductor companies Intel Samsung TI 2026",
            "OSAT semiconductor packaging companies ASE Amkor JCET 2026",
            "semiconductor industry market structure 2026",
            "AI chip companies market share 2026",
        ],
    ),
    "benchmark_performance": ResearchTopic(
        topic_id="benchmark_performance",
        name="Benchmarks & Performance Metrics",
        name_kr="벤치마크 및 성능 지표",
        tier=Tier.TIER2,
        node_labels=["Benchmark"],
        relationship_types=["SCORES_ON"],
        description="MLPerf, SPEC, 전력효율 벤치마크 데이터",
        sources=[
            ResearchSource("Wikipedia - MLPerf", "https://en.wikipedia.org/wiki/MLPerf", "wikipedia", "MLPerf AI 벤치마크"),
        ],
        search_queries=[
            "MLPerf training inference results 2026",
            "AI accelerator benchmark comparison TOPS per watt 2026",
            "NVIDIA B200 B300 GB300 benchmark performance 2026",
            "AMD MI350 MI400 benchmark vs NVIDIA 2026",
            "data center AI chip performance comparison 2026",
            "MLPerf latest round results 2026",
        ],
    ),
}


# ============================================================
# Tier 3 Topics — 심화 도메인
# ============================================================

TIER3_TOPICS = {
    "reliability_testing": ResearchTopic(
        topic_id="reliability_testing",
        name="Reliability Testing Standards",
        name_kr="신뢰성 시험 규격",
        tier=Tier.TIER3,
        node_labels=["ReliabilityTest"],
        relationship_types=["TESTED_BY", "FAILURE_MECHANISM"],
        description="JEDEC/MIL 신뢰성 시험 규격 (HTOL, ESD, EM, TDDB)",
        sources=[
            ResearchSource("Wikipedia - Electromigration", "https://en.wikipedia.org/wiki/Electromigration", "wikipedia", "EM 고장 메커니즘"),
            ResearchSource("Wikipedia - ESD", "https://en.wikipedia.org/wiki/Electrostatic_discharge", "wikipedia", "ESD 보호"),
            ResearchSource("Wikipedia - TDDB", "https://en.wikipedia.org/wiki/Time-dependent_dielectric_breakdown", "wikipedia", "TDDB 고장"),
            ResearchSource("JEDEC Standards", "https://www.jedec.org/standards-documents", "standards_org", "JEDEC 신뢰성 표준"),
        ],
        search_queries=[
            "JEDEC reliability test standards HTOL HAST TC 2026",
            "semiconductor reliability testing methods ESD HBM CDM",
            "electromigration TDDB reliability failure mechanisms advanced node",
            "automotive semiconductor qualification AEC-Q100 2026",
            "GAA nanosheet reliability challenges 2026",
        ],
    ),
    "industry_standards": ResearchTopic(
        topic_id="industry_standards",
        name="Industry Standards & Specifications",
        name_kr="산업 표준/규격",
        tier=Tier.TIER3,
        node_labels=["Standard"],
        relationship_types=["COMPLIES_WITH"],
        description="JEDEC, IEEE, SEMI, IRTC 표준 및 규격",
        sources=[
            ResearchSource("JEDEC", "https://www.jedec.org/standards-documents", "standards_org", "JEDEC 표준"),
            ResearchSource("SEMI Standards", "https://www.semi.org/en/products-services/standards", "standards_org", "SEMI 표준"),
        ],
        search_queries=[
            "SEMI standards semiconductor manufacturing E10 E79 2026",
            "JEDEC standards memory HBM DDR 2026",
            "IEEE semiconductor design standards 2026",
            "semiconductor industry standards update 2026",
        ],
    ),
    "application_segments": ResearchTopic(
        topic_id="application_segments",
        name="Application Segments & Workloads",
        name_kr="응용 분야 및 워크로드",
        tier=Tier.TIER3,
        node_labels=["Application"],
        relationship_types=["OPTIMIZED_FOR", "DEPLOYED_IN"],
        description="데이터센터, 엣지, 자동차, 모바일 응용별 요구사항",
        sources=[
            ResearchSource("Wikipedia - Data Center", "https://en.wikipedia.org/wiki/Data_center", "wikipedia", "데이터센터 인프라"),
            ResearchSource("Wikipedia - Edge Computing", "https://en.wikipedia.org/wiki/Edge_computing", "wikipedia", "엣지 컴퓨팅"),
            ResearchSource("Wikipedia - ADAS", "https://en.wikipedia.org/wiki/Advanced_driver-assistance_system", "wikipedia", "자동차 ADAS"),
        ],
        search_queries=[
            "AI data center chip requirements 2026",
            "edge AI inference chip requirements 2026",
            "automotive semiconductor ADAS self-driving requirements 2026",
            "mobile AI chip requirements on-device LLM 2026",
            "AI inference accelerator market segmentation 2026",
        ],
    ),
    "thermal_power": ResearchTopic(
        topic_id="thermal_power",
        name="Thermal & Power Management",
        name_kr="전력/열 관리",
        tier=Tier.TIER3,
        node_labels=["ThermalSolution"],
        relationship_types=["COOLED_BY", "POWER_BUDGET"],
        description="TDP, 액냉, 전력 분배 네트워크(PDN)",
        sources=[
            ResearchSource("Wikipedia - Immersion Cooling", "https://en.wikipedia.org/wiki/Immersion_cooling", "wikipedia", "침수 냉각"),
            ResearchSource("Wikipedia - Computer Cooling", "https://en.wikipedia.org/wiki/Computer_cooling", "wikipedia", "컴퓨터 냉각"),
            ResearchSource("Wikipedia - TDP", "https://en.wikipedia.org/wiki/Thermal_design_power", "wikipedia", "TDP 개념"),
        ],
        search_queries=[
            "data center liquid cooling AI GPU 2026",
            "immersion cooling semiconductor 2026",
            "power delivery network PDN advanced packaging 2026",
            "1000W+ AI chip cooling solutions 2026",
            "direct liquid cooling data center adoption 2026",
        ],
    ),
    "regulation_geopolitics": ResearchTopic(
        topic_id="regulation_geopolitics",
        name="Regulations & Geopolitics",
        name_kr="규제/지정학",
        tier=Tier.TIER3,
        node_labels=["Regulation"],
        relationship_types=["RESTRICTED_BY", "SUBJECT_TO"],
        description="미국 수출 규제, CHIPS Act, EU Chips Act",
        sources=[
            ResearchSource("Wikipedia - CHIPS Act", "https://en.wikipedia.org/wiki/CHIPS_and_Science_Act", "wikipedia", "미국 CHIPS법"),
            ResearchSource("Wikipedia - EU Chips Act", "https://en.wikipedia.org/wiki/European_Chips_Act", "wikipedia", "EU 반도체법"),
            ResearchSource("Wikipedia - US-China Sanctions", "https://en.wikipedia.org/wiki/United_States_sanctions_against_China", "wikipedia", "미중 반도체 규제"),
        ],
        search_queries=[
            "US semiconductor export controls China 2026",
            "CHIPS Act funding progress 2026",
            "EU Chips Act semiconductor subsidy 2026",
            "Japan semiconductor export controls 2026",
            "semiconductor supply chain geopolitics 2026",
            "China semiconductor self-sufficiency progress 2026",
        ],
    ),
    "inspection_metrology": ResearchTopic(
        topic_id="inspection_metrology",
        name="Inspection & Metrology",
        name_kr="검사/계측",
        tier=Tier.TIER3,
        node_labels=["InspectionMethod"],
        relationship_types=["INSPECTED_BY", "AFFECTS_YIELD"],
        description="인라인 계측, 웨이퍼 검사, 결함 분석 기법",
        sources=[
            ResearchSource("Wikipedia - KLA", "https://en.wikipedia.org/wiki/KLA_Corporation", "wikipedia", "KLA 계측 장비"),
            ResearchSource("Wikipedia - SEM", "https://en.wikipedia.org/wiki/Scanning_electron_microscope", "wikipedia", "SEM 검사"),
            ResearchSource("Wikipedia - Photolithography", "https://en.wikipedia.org/wiki/Photolithography", "wikipedia", "리소그래피 공정"),
        ],
        search_queries=[
            "semiconductor inline inspection methods KLA 2026",
            "wafer metrology CD-SEM OCD scatterometry 2026",
            "defect review classification semiconductor 2026",
            "AI-powered semiconductor defect inspection 2026",
        ],
    ),
}


# ============================================================
# All Topics Registry
# ============================================================

ALL_TOPICS: dict[str, ResearchTopic] = {
    **TIER1_TOPICS,
    **TIER2_TOPICS,
    **TIER3_TOPICS,
}


def get_topics_by_tier(tier: Tier) -> dict[str, ResearchTopic]:
    """Tier별 토픽 조회"""
    tier_map = {
        Tier.TIER1: TIER1_TOPICS,
        Tier.TIER2: TIER2_TOPICS,
        Tier.TIER3: TIER3_TOPICS,
    }
    return tier_map.get(tier, {})


def get_topic(topic_id: str) -> Optional[ResearchTopic]:
    """토픽 ID로 조회"""
    return ALL_TOPICS.get(topic_id)
