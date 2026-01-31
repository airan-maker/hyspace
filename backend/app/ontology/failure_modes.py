"""
Failure Mode Ontology

반도체 제조 장비 고장 모드 및 결함 유형 지식 체계

Sources:
- SEMI E10 (Equipment Reliability, Availability & Maintainability)
- Industry failure analysis databases
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class FailureSeverity(str, Enum):
    CATASTROPHIC = "CATASTROPHIC"   # 웨이퍼 폐기 수준
    MAJOR = "MAJOR"                 # 수율 5%+ 영향
    MINOR = "MINOR"                 # 수율 1-5% 영향
    COSMETIC = "COSMETIC"           # 외관 결함, 기능 무관


@dataclass
class DefectType:
    """결함 유형 정의"""
    defect_id: str
    name: str
    name_kr: str
    category: str               # PARTICLE, PATTERN, FILM, ELECTRICAL, MECHANICAL
    severity: FailureSeverity

    # Detection
    detection_method: str       # OPTICAL, SEM, ELECTRICAL, AFM
    typical_inspection_step: str

    # Root Cause
    common_causes: list[str]
    affected_process_steps: list[str]

    # Impact
    yield_impact_pct: tuple[float, float]   # (min, max) 수율 영향
    kill_ratio_pct: float                   # 해당 결함 발생 시 다이 불량률

    # Corrective Action
    corrective_actions: list[str]
    prevention_methods: list[str]

    description: str = ""


@dataclass
class EquipmentFailureMode:
    """장비 고장 모드 정의"""
    mode_id: str
    name: str
    name_kr: str
    equipment_type: str

    # Failure characteristics
    failure_rate_per_1000h: float    # 1000시간당 발생률
    mtbf_hours: int                 # 해당 고장 모드 MTBF
    mttr_hours: float               # 복구 시간

    # Detection
    early_warning_signs: list[str]  # 조기 경보 신호
    detection_sensors: list[str]    # 감지 센서

    # Impact
    production_impact: str          # 생산 중단 여부
    wafer_risk: str                # SCRAPPED, REWORKABLE, SAFE

    # Resolution
    repair_procedure: str
    required_parts: list[str]
    preventive_measure: str

    description: str = ""


# ============================================================
# Defect Types Database
# ============================================================

DEFECT_TYPES: dict[str, DefectType] = {
    # --- Particle Defects ---
    "PARTICLE_METAL": DefectType(
        defect_id="DEF-001",
        name="Metal Particle Contamination",
        name_kr="금속 입자 오염",
        category="PARTICLE",
        severity=FailureSeverity.MAJOR,
        detection_method="OPTICAL (Brightfield)",
        typical_inspection_step="POST_DEPOSITION",
        common_causes=[
            "챔버 내벽 파편 (flaking)",
            "가스 라인 오염",
            "로봇 암 마모",
            "웨이퍼 캐리어 오염"
        ],
        affected_process_steps=["CVD", "PVD", "ETCH"],
        yield_impact_pct=(2, 15),
        kill_ratio_pct=80,
        corrective_actions=[
            "챔버 세정 (in-situ clean 강화)",
            "파티클 소스 격리 및 교체",
            "가스 필터 교체"
        ],
        prevention_methods=[
            "정기 챔버 시즈닝 (seasoning)",
            "웨이퍼 수 기반 자동 세정 스케줄",
            "실시간 in-situ 파티클 모니터링"
        ],
        description="금속 입자가 웨이퍼 표면에 부착, 단락·누설 전류 원인"
    ),

    # --- Pattern Defects ---
    "CD_VARIATION": DefectType(
        defect_id="DEF-010",
        name="Critical Dimension Variation",
        name_kr="CD 변동",
        category="PATTERN",
        severity=FailureSeverity.MAJOR,
        detection_method="CD-SEM",
        typical_inspection_step="POST_LITHO, POST_ETCH",
        common_causes=[
            "노광 포커스/도즈 변동",
            "레지스트 두께 불균일",
            "마스크 CD 오차",
            "식각 프로파일 변화",
            "리소그래피 렌즈 수차"
        ],
        affected_process_steps=["LITHOGRAPHY", "ETCH"],
        yield_impact_pct=(5, 25),
        kill_ratio_pct=60,
        corrective_actions=[
            "노광 조건 재캘리브레이션",
            "레지스트 코팅 레시피 조정",
            "식각 EP (endpoint) 최적화"
        ],
        prevention_methods=[
            "APC (Advanced Process Control) 적용",
            "FDC (Fault Detection & Classification)",
            "Lot 단위 CD 모니터링"
        ],
        description="트랜지스터 게이트 또는 배선의 폭이 규격에서 벗어남"
    ),
    "OVERLAY_ERROR": DefectType(
        defect_id="DEF-011",
        name="Overlay Error",
        name_kr="오버레이 오차",
        category="PATTERN",
        severity=FailureSeverity.CATASTROPHIC,
        detection_method="OPTICAL (Overlay metrology)",
        typical_inspection_step="POST_LITHO",
        common_causes=[
            "스테이지 정밀도 저하",
            "열적 변형 (wafer/reticle)",
            "마크 인식 오류",
            "이전 레이어 변형"
        ],
        affected_process_steps=["LITHOGRAPHY"],
        yield_impact_pct=(10, 50),
        kill_ratio_pct=90,
        corrective_actions=[
            "스캐너 정렬 재캘리브레이션",
            "오버레이 보정 모델 업데이트",
            "리워크 (레지스트 제거 후 재노광)"
        ],
        prevention_methods=[
            "사전 오버레이 측정 (feedforward)",
            "Wafer-level 보정 (per-wafer overlay)",
            "정기 스캐너 매칭 검증"
        ],
        description="레이어 간 정렬 오차, 3nm 노드에서 허용 오차 < 2nm"
    ),

    # --- Film Defects ---
    "FILM_THICKNESS_VAR": DefectType(
        defect_id="DEF-020",
        name="Film Thickness Non-Uniformity",
        name_kr="막두께 불균일",
        category="FILM",
        severity=FailureSeverity.MINOR,
        detection_method="Ellipsometry / XRF",
        typical_inspection_step="POST_DEPOSITION",
        common_causes=[
            "가스 분배 불균일 (showerhead)",
            "히터 온도 불균일",
            "챔버 시즈닝 상태",
            "전구체 유량 변동"
        ],
        affected_process_steps=["CVD", "ALD", "PVD"],
        yield_impact_pct=(1, 8),
        kill_ratio_pct=30,
        corrective_actions=[
            "샤워헤드 교체/세정",
            "히터 존 캘리브레이션",
            "가스 유량 컨트롤러 교정"
        ],
        prevention_methods=[
            "정기 두께 모니터 웨이퍼 측정",
            "챔버 간 매칭 관리",
            "SPC 차트 모니터링"
        ],
        description="증착 막의 두께가 웨이퍼 면내에서 불균일"
    ),

    # --- Electrical Defects ---
    "CONTACT_OPEN": DefectType(
        defect_id="DEF-030",
        name="Contact/Via Open",
        name_kr="콘택/비아 오픈",
        category="ELECTRICAL",
        severity=FailureSeverity.CATASTROPHIC,
        detection_method="ELECTRICAL (E-beam / probe)",
        typical_inspection_step="POST_CMP, WAFER_TEST",
        common_causes=[
            "식각 불완전 (etch stop on barrier)",
            "금속 충진 보이드 (void)",
            "배리어 과도 증착",
            "CMP 과연마 (dishing)"
        ],
        affected_process_steps=["CONTACT", "VIA_ETCH", "W_CVD", "CMP"],
        yield_impact_pct=(5, 30),
        kill_ratio_pct=95,
        corrective_actions=[
            "식각 레시피 최적화 (over-etch 조건)",
            "CVD 핵생성 (nucleation) 단계 개선",
            "CMP 엔드포인트 조정"
        ],
        prevention_methods=[
            "E-beam 검사 정기 실행",
            "SPC 기반 저항 모니터링",
            "식각 EP 정밀 제어"
        ],
        description="콘택 또는 비아가 전기적으로 끊어짐, 고종횡비 구조에서 빈발"
    ),
    "BRIDGE_SHORT": DefectType(
        defect_id="DEF-031",
        name="Metal Line Bridge / Short",
        name_kr="배선 브릿지/단락",
        category="ELECTRICAL",
        severity=FailureSeverity.CATASTROPHIC,
        detection_method="OPTICAL + ELECTRICAL",
        typical_inspection_step="POST_CMP, WAFER_TEST",
        common_causes=[
            "파티클에 의한 식각 마스킹",
            "리소그래피 브릿지 (under-exposure)",
            "Cu 잔유물 (CMP 불완전)",
            "전기이동 (electromigration)"
        ],
        affected_process_steps=["LITHOGRAPHY", "ETCH", "CMP"],
        yield_impact_pct=(5, 20),
        kill_ratio_pct=95,
        corrective_actions=[
            "파티클 소스 제거",
            "리소그래피 도즈 조정",
            "CMP 과연마 시간 증가"
        ],
        prevention_methods=[
            "인라인 결함 검사 강화",
            "CMP 슬러리 교체 주기 관리",
            "설계 규칙 준수 검증 (DRC)"
        ],
        description="인접 배선 간 금속 잔유물로 인한 단락"
    ),
}


# ============================================================
# Equipment Failure Modes Database
# ============================================================

EQUIPMENT_FAILURE_MODES: dict[str, EquipmentFailureMode] = {
    "LITHO_FOCUS_DRIFT": EquipmentFailureMode(
        mode_id="EFM-001",
        name="Focus Drift",
        name_kr="포커스 드리프트",
        equipment_type="LITHOGRAPHY",
        failure_rate_per_1000h=2.0,
        mtbf_hours=500,
        mttr_hours=4,
        early_warning_signs=[
            "CD 변동 증가 (3-sigma 확대)",
            "오버레이 오차 증가",
            "포커스 센서 오프셋 변화"
        ],
        detection_sensors=["FOCUS_SENSOR", "ALIGNMENT_SENSOR", "CD_SEM_FEEDBACK"],
        production_impact="생산 중단 (즉시 캘리브레이션 필요)",
        wafer_risk="REWORKABLE (레지스트 제거 후 재노광 가능)",
        repair_procedure="1) 포커스 센서 캘리브레이션 2) 레티클 정렬 재설정 3) CD 검증",
        required_parts=["Focus calibration wafer", "Reference reticle"],
        preventive_measure="매 200 Lot마다 포커스 캘리브레이션, 주 1회 베이스라인 검증",
        description="노광 포커스가 서서히 드리프트하여 CD 변동 유발"
    ),
    "ETCH_ESC_FAILURE": EquipmentFailureMode(
        mode_id="EFM-010",
        name="Electrostatic Chuck Failure",
        name_kr="정전척 고장",
        equipment_type="ETCH",
        failure_rate_per_1000h=0.5,
        mtbf_hours=2000,
        mttr_hours=8,
        early_warning_signs=[
            "웨이퍼 온도 불균일 증가",
            "헬륨 누설량 증가",
            "식각 균일도 저하",
            "He backside pressure 변동"
        ],
        detection_sensors=["THERMOCOUPLE", "HE_LEAK_DETECTOR", "PRESSURE_GAUGE"],
        production_impact="생산 중단 (ESC 교체 필요)",
        wafer_risk="SCRAPPED (가공 중 웨이퍼 손상 가능)",
        repair_procedure="1) 챔버 개방 2) ESC 교체 3) 챔버 시즈닝 4) 공정 검증",
        required_parts=["Electrostatic Chuck assembly", "O-ring kit", "He supply line"],
        preventive_measure="10,000 wafer마다 ESC 상태 점검, He 누설율 주 1회 측정",
        description="정전척 열화로 웨이퍼 고정/냉각 불량, 식각 균일도 급격 저하"
    ),
    "CVD_SHOWERHEAD_CLOG": EquipmentFailureMode(
        mode_id="EFM-020",
        name="Showerhead Clogging",
        name_kr="샤워헤드 막힘",
        equipment_type="CVD",
        failure_rate_per_1000h=1.0,
        mtbf_hours=1000,
        mttr_hours=6,
        early_warning_signs=[
            "증착 두께 불균일 증가",
            "챔버 압력 변동",
            "파티클 카운트 증가",
            "증착률 저하"
        ],
        detection_sensors=["PARTICLE_COUNTER", "PRESSURE_GAUGE", "DEPOSITION_RATE_MONITOR"],
        production_impact="품질 저하 (점진적), 심할 경우 생산 중단",
        wafer_risk="REWORKABLE (초기) / SCRAPPED (심각)",
        repair_procedure="1) 챔버 세정 (NF3 remote plasma) 2) 샤워헤드 교체 (심각 시) 3) 시즈닝",
        required_parts=["Showerhead assembly", "Remote plasma source parts"],
        preventive_measure="매 500 웨이퍼마다 in-situ 세정, 3000 웨이퍼마다 샤워헤드 점검",
        description="전구체 부산물이 가스 분배판 홀을 막아 증착 불균일 유발"
    ),
    "CMP_PAD_WEAR": EquipmentFailureMode(
        mode_id="EFM-030",
        name="Polishing Pad Glazing/Wear",
        name_kr="연마 패드 마모",
        equipment_type="CMP",
        failure_rate_per_1000h=3.0,
        mtbf_hours=300,
        mttr_hours=1,
        early_warning_signs=[
            "제거율(RR) 저하",
            "WIWNU (면내 불균일) 증가",
            "디싱(dishing) 증가",
            "모터 전류 변화"
        ],
        detection_sensors=["MOTOR_CURRENT", "THICKNESS_MONITOR", "ENDPOINT_DETECTOR"],
        production_impact="품질 저하 (점진적)",
        wafer_risk="REWORKABLE",
        repair_procedure="1) 패드 교체 2) 컨디셔닝 디스크 확인 3) 슬러리 유량 검증",
        required_parts=["Polishing pad", "Conditioning disk", "Retaining ring"],
        preventive_measure="매 200 웨이퍼마다 패드 수명 모니터링, 컨디셔너 주기적 교체",
        description="연마 패드 표면 글레이징으로 제거율 저하 및 불균일 증가"
    ),
}


# ============================================================
# Lookup Interface
# ============================================================

class FailureModeOntology:
    """고장 모드 온톨로지 인터페이스"""

    @staticmethod
    def get_all_defect_types() -> dict[str, DefectType]:
        return DEFECT_TYPES

    @staticmethod
    def get_defect(defect_id: str) -> Optional[DefectType]:
        return DEFECT_TYPES.get(defect_id)

    @staticmethod
    def get_defects_by_severity(severity: FailureSeverity) -> list[DefectType]:
        return [d for d in DEFECT_TYPES.values() if d.severity == severity]

    @staticmethod
    def get_defects_for_process(process_step: str) -> list[DefectType]:
        return [d for d in DEFECT_TYPES.values()
                if process_step in d.affected_process_steps]

    @staticmethod
    def get_all_failure_modes() -> dict[str, EquipmentFailureMode]:
        return EQUIPMENT_FAILURE_MODES

    @staticmethod
    def get_failure_mode(mode_id: str) -> Optional[EquipmentFailureMode]:
        return EQUIPMENT_FAILURE_MODES.get(mode_id)

    @staticmethod
    def get_failure_modes_for_equipment(equipment_type: str) -> list[EquipmentFailureMode]:
        return [f for f in EQUIPMENT_FAILURE_MODES.values()
                if f.equipment_type == equipment_type]

    @staticmethod
    def get_early_warning_signs(equipment_type: str) -> list[dict]:
        """장비 유형별 조기 경보 신호 목록"""
        modes = [f for f in EQUIPMENT_FAILURE_MODES.values()
                 if f.equipment_type == equipment_type]
        signs = []
        for mode in modes:
            for sign in mode.early_warning_signs:
                signs.append({
                    "failure_mode": mode.name_kr,
                    "warning_sign": sign,
                    "sensors": mode.detection_sensors,
                    "impact": mode.wafer_risk
                })
        return signs
