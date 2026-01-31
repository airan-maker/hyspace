"""
Workload-to-Spec Analyzer Engine

고객 워크로드 프로파일을 분석하여 최적의 칩 아키텍처를 추천하는 엔진
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import math

from .ppa_engine import PPAEngine, ChipConfig
from .cost_simulator import CostSimulator


class WorkloadType(str, Enum):
    AI_INFERENCE = "AI_INFERENCE"
    AI_TRAINING = "AI_TRAINING"
    IMAGE_PROCESSING = "IMAGE_PROCESSING"
    VIDEO_ENCODING = "VIDEO_ENCODING"
    SCIENTIFIC_COMPUTE = "SCIENTIFIC_COMPUTE"
    GENERAL_PURPOSE = "GENERAL_PURPOSE"
    EDGE_INFERENCE = "EDGE_INFERENCE"


class FormFactor(str, Enum):
    DATA_CENTER = "DATA_CENTER"
    EDGE_SERVER = "EDGE_SERVER"
    EMBEDDED = "EMBEDDED"
    MOBILE = "MOBILE"


class CoolingType(str, Enum):
    AIR = "AIR"
    LIQUID = "LIQUID"
    PASSIVE = "PASSIVE"


class Precision(str, Enum):
    FP32 = "FP32"
    FP16 = "FP16"
    BF16 = "BF16"
    INT8 = "INT8"
    INT4 = "INT4"


class MemoryType(str, Enum):
    HBM3 = "HBM3"
    HBM3E = "HBM3E"
    HBM4 = "HBM4"
    GDDR6 = "GDDR6"
    LPDDR5 = "LPDDR5"


@dataclass
class ComputeRequirements:
    """연산 요구사항"""
    operations_per_inference: float  # TOPS per inference
    target_latency_ms: float
    batch_size: int = 1
    precision: Precision = Precision.INT8


@dataclass
class MemoryRequirements:
    """메모리 요구사항"""
    model_size_gb: float
    activation_memory_gb: float = 0.0
    kv_cache_gb: float = 0.0  # LLM용 KV cache
    bandwidth_requirement_gbps: float = 100.0


@dataclass
class PowerConstraints:
    """전력 제약조건"""
    max_tdp_watts: float
    target_efficiency_tops_per_watt: float = 1.0


@dataclass
class DeploymentContext:
    """배포 환경"""
    form_factor: FormFactor = FormFactor.DATA_CENTER
    cooling: CoolingType = CoolingType.AIR
    volume_per_year: int = 10000


@dataclass
class WorkloadProfile:
    """완전한 워크로드 프로파일"""
    name: str
    workload_type: WorkloadType
    compute_requirements: ComputeRequirements
    memory_requirements: MemoryRequirements
    power_constraints: PowerConstraints
    deployment_context: DeploymentContext
    description: Optional[str] = None


@dataclass
class WorkloadCharacterization:
    """워크로드 특성 분석 결과"""
    compute_intensity: str  # "Memory-Bound", "Compute-Bound", "Balanced"
    arithmetic_intensity: float  # FLOPs per Byte
    bottleneck: str
    required_tops: float


@dataclass
class RecommendedArchitecture:
    """추천 아키텍처"""
    name: str
    description: str
    process_node_nm: int
    npu_cores: int
    cpu_cores: int
    gpu_cores: int
    memory_type: MemoryType
    memory_capacity_gb: int
    memory_bandwidth_tbps: float
    die_size_mm2: float
    power_tdp_w: float
    performance_tops: float
    efficiency_tops_per_watt: float
    estimated_unit_cost: float
    match_score: float  # 0-100
    is_recommended: bool
    justifications: list[str] = field(default_factory=list)
    trade_offs: list[str] = field(default_factory=list)


@dataclass
class CompetitiveBenchmark:
    """경쟁사 벤치마크"""
    competitor_name: str
    performance_tops: float
    power_tdp_w: float
    memory_bandwidth_tbps: float
    estimated_price: float
    comparison_summary: str


@dataclass
class WorkloadAnalysisResult:
    """워크로드 분석 결과"""
    workload_profile: WorkloadProfile
    characterization: WorkloadCharacterization
    recommended_architectures: list[RecommendedArchitecture]
    competitive_benchmarks: list[CompetitiveBenchmark]
    confidence_score: float
    analysis_notes: list[str] = field(default_factory=list)


# 경쟁사 스펙 데이터 - 온톨로지에서 동적 로드
def _load_competitor_specs() -> dict:
    """AI 산업 온톨로지에서 경쟁사 가속기 데이터 로드 (Neo4j → 온톨로지 → 하드코딩 순)"""
    # 1차: Neo4j 그래프에서 로드
    try:
        from app.neo4j_client import Neo4jClient
        if Neo4jClient.is_available():
            records = Neo4jClient.run_query(
                "MATCH (a:AIAccelerator) "
                "RETURN a.name AS name, a.bf16_tflops AS bf16, a.int8_tops AS int8, "
                "a.tdp_watts AS tdp, a.memory_bandwidth_tbps AS bw, "
                "a.memory_capacity_gb AS mem, a.msrp_usd AS price"
            )
            if records:
                specs = {}
                for r in records:
                    specs[r["name"]] = {
                        "tops_fp16": (r["bf16"] or 0) * 2,
                        "tops_int8": r["int8"],
                        "power_w": r["tdp"],
                        "bandwidth_tbps": r["bw"],
                        "memory_gb": r["mem"],
                        "price_estimate": r["price"] or 10000,
                    }
                return specs
    except Exception:
        pass

    # 2차: 인메모리 온톨로지
    try:
        from app.ontology import AIIndustryOntology
        accelerators = AIIndustryOntology.get_all_accelerators()
        specs = {}
        for key, acc in accelerators.items():
            specs[acc.name] = {
                "tops_fp16": acc.compute.bf16_tflops * 2,  # BF16 TFLOPS → FP16 TOPS approx
                "tops_int8": acc.compute.int8_tops,
                "power_w": acc.tdp_watts,
                "bandwidth_tbps": acc.memory.bandwidth_tbps,
                "memory_gb": acc.memory.capacity_gb,
                "price_estimate": acc.msrp_usd or 10000,
            }
        return specs
    except Exception:
        # 온톨로지 로드 실패 시 기본 데이터
        return {
            "NVIDIA H100 SXM": {
                "tops_fp16": 1979, "tops_int8": 3958, "power_w": 700,
                "bandwidth_tbps": 3.35, "memory_gb": 80, "price_estimate": 30000,
            },
            "AMD MI300X": {
                "tops_fp16": 1307, "tops_int8": 2614, "power_w": 750,
                "bandwidth_tbps": 5.3, "memory_gb": 192, "price_estimate": 15000,
            },
            "Intel Gaudi 3": {
                "tops_fp16": 900, "tops_int8": 1800, "power_w": 600,
                "bandwidth_tbps": 3.7, "memory_gb": 128, "price_estimate": 12000,
            },
        }

COMPETITOR_SPECS = _load_competitor_specs()

# 메모리 타입별 대역폭 (TB/s) - 온톨로지에서 HBM 스펙 참조
def _load_memory_bandwidth() -> dict:
    """HBM 대역폭 데이터 로드 (Neo4j → 온톨로지 → 하드코딩 순, 6-stack 기준 TB/s)"""
    # 1차: Neo4j
    try:
        from app.neo4j_client import Neo4jClient
        if Neo4jClient.is_available():
            records = Neo4jClient.run_query(
                "MATCH (h:HBMGeneration) "
                "RETURN h.generation AS gen, h.bandwidth_per_stack_gbps AS bw"
            )
            if records:
                hbm_map = {"HBM4": MemoryType.HBM4, "HBM3E": MemoryType.HBM3E, "HBM3": MemoryType.HBM3}
                bw = {}
                for r in records:
                    mt = hbm_map.get(r["gen"])
                    if mt:
                        bw[mt] = round(r["bw"] * 6 / 1000, 2)
                bw.setdefault(MemoryType.HBM4, 6.4)
                bw.setdefault(MemoryType.HBM3E, 4.8)
                bw.setdefault(MemoryType.HBM3, 3.2)
                bw[MemoryType.GDDR6] = 1.0
                bw[MemoryType.LPDDR5] = 0.128
                return bw
    except Exception:
        pass

    # 2차: 인메모리 온톨로지
    try:
        from app.ontology import AIIndustryOntology
        hbm_specs = AIIndustryOntology.get_all_hbm()
        bw = {}
        hbm_map = {"HBM4": MemoryType.HBM4, "HBM3E": MemoryType.HBM3E, "HBM3": MemoryType.HBM3}
        for key, mem_type in hbm_map.items():
            if key in hbm_specs:
                # 6-stack 기준 총 대역폭 (GB/s → TB/s)
                bw[mem_type] = round(hbm_specs[key].bandwidth_per_stack_gbps * 6 / 1000, 2)
        bw.setdefault(MemoryType.HBM4, 6.4)
        bw.setdefault(MemoryType.HBM3E, 4.8)
        bw.setdefault(MemoryType.HBM3, 3.2)
        bw[MemoryType.GDDR6] = 1.0
        bw[MemoryType.LPDDR5] = 0.128
        return bw
    except Exception:
        return {
            MemoryType.HBM4: 6.4, MemoryType.HBM3E: 4.8,
            MemoryType.HBM3: 3.2, MemoryType.GDDR6: 1.0, MemoryType.LPDDR5: 0.128,
        }

MEMORY_BANDWIDTH = _load_memory_bandwidth()

# 정밀도별 TOPS/core
TOPS_PER_CORE = {
    Precision.INT4: 32.0,
    Precision.INT8: 16.0,
    Precision.FP16: 8.0,
    Precision.BF16: 8.0,
    Precision.FP32: 2.0,
}


class WorkloadAnalyzer:
    """
    Workload-to-Spec Analyzer Engine

    고객의 워크로드 요구사항을 분석하여 최적의 칩 아키텍처를 추천
    """

    def __init__(
        self,
        ppa_engine: Optional[PPAEngine] = None,
        cost_simulator: Optional[CostSimulator] = None
    ):
        self.ppa_engine = ppa_engine or PPAEngine()
        self.cost_simulator = cost_simulator or CostSimulator()

    def characterize_workload(
        self,
        profile: WorkloadProfile
    ) -> WorkloadCharacterization:
        """
        워크로드 특성 분석

        Arithmetic Intensity를 기반으로 Memory-Bound vs Compute-Bound 판단
        """
        compute_req = profile.compute_requirements
        memory_req = profile.memory_requirements

        # 총 메모리 요구량
        total_memory_gb = (
            memory_req.model_size_gb +
            memory_req.activation_memory_gb +
            memory_req.kv_cache_gb
        )

        # Arithmetic Intensity 계산 (OPs per Byte)
        ops_per_inference = compute_req.operations_per_inference * 1e12
        bytes_accessed = total_memory_gb * 1e9 if total_memory_gb > 0 else 1e9

        arithmetic_intensity = ops_per_inference / bytes_accessed

        # 특성 분류
        if arithmetic_intensity < 1.0:
            compute_intensity = "Memory-Bound"
            bottleneck = "Memory Bandwidth"
        elif arithmetic_intensity > 10.0:
            compute_intensity = "Compute-Bound"
            bottleneck = "Compute Throughput"
        else:
            compute_intensity = "Balanced"
            bottleneck = "Mixed (Compute & Memory)"

        # 목표 지연시간 달성을 위한 필요 TOPS 계산
        inferences_per_second = (1000 / compute_req.target_latency_ms) * compute_req.batch_size
        required_tops = compute_req.operations_per_inference * inferences_per_second

        return WorkloadCharacterization(
            compute_intensity=compute_intensity,
            arithmetic_intensity=round(arithmetic_intensity, 2),
            bottleneck=bottleneck,
            required_tops=round(required_tops, 1)
        )

    def calculate_npu_cores_needed(
        self,
        required_tops: float,
        process_node: int,
        precision: Precision
    ) -> int:
        """NPU 코어 수 계산"""
        tops_per_core = TOPS_PER_CORE.get(precision, 8.0)

        # 공정 노드 스케일링
        node_scaling = {3: 1.3, 5: 1.0, 7: 0.8, 10: 0.6}
        scaling = node_scaling.get(process_node, 1.0)

        cores_needed = required_tops / (tops_per_core * scaling)

        # 20% 헤드룸 추가, 최소 8코어
        return max(8, int(cores_needed * 1.2))

    def select_memory_config(
        self,
        memory_req: MemoryRequirements,
        form_factor: FormFactor
    ) -> tuple[MemoryType, int, float]:
        """
        메모리 구성 선택

        Returns: (메모리 타입, 용량 GB, 대역폭 TB/s)
        """
        total_memory = (
            memory_req.model_size_gb +
            memory_req.activation_memory_gb +
            memory_req.kv_cache_gb
        )

        # 20% 헤드룸
        required_capacity = int(total_memory * 1.2)
        required_bandwidth = memory_req.bandwidth_requirement_gbps

        # 폼팩터별 제약
        if form_factor in [FormFactor.EMBEDDED, FormFactor.MOBILE]:
            return (
                MemoryType.LPDDR5,
                min(required_capacity, 32),
                MEMORY_BANDWIDTH[MemoryType.LPDDR5]
            )

        # 대역폭 요구에 따른 메모리 선택
        if required_bandwidth > 2000:
            memory_type = MemoryType.HBM3E
            capacity = max(96, required_capacity)
        elif required_bandwidth > 800:
            memory_type = MemoryType.HBM3
            capacity = max(80, required_capacity)
        elif required_bandwidth > 200:
            memory_type = MemoryType.GDDR6
            capacity = max(24, required_capacity)
        else:
            memory_type = MemoryType.LPDDR5
            capacity = max(16, required_capacity)

        bandwidth = MEMORY_BANDWIDTH[memory_type]

        return memory_type, capacity, bandwidth

    def generate_architecture(
        self,
        profile: WorkloadProfile,
        characterization: WorkloadCharacterization,
        variant: str = "balanced"
    ) -> RecommendedArchitecture:
        """
        아키텍처 생성

        variant: "balanced", "low_power", "high_performance"
        """
        compute_req = profile.compute_requirements
        power_constraints = profile.power_constraints
        deployment = profile.deployment_context

        # 변종에 따른 파라미터 조정
        if variant == "low_power":
            process_node = 5
            power_factor = 0.7
            perf_factor = 0.85
            name = "Power-Efficient Design"
            desc = "저전력 최적화 설계, 에너지 효율 우선"
        elif variant == "high_performance":
            process_node = 3
            power_factor = 1.3
            perf_factor = 1.2
            name = "High-Performance Design"
            desc = "최대 성능 설계, 쿨링 솔루션 필요"
        else:
            process_node = 3
            power_factor = 1.0
            perf_factor = 1.0
            name = "Balanced Design"
            desc = "성능과 효율의 균형 잡힌 설계"

        # NPU 코어 계산
        required_tops = characterization.required_tops * perf_factor
        npu_cores = self.calculate_npu_cores_needed(
            required_tops,
            process_node,
            compute_req.precision
        )

        # 메모리 구성
        memory_type, memory_capacity, memory_bw = self.select_memory_config(
            profile.memory_requirements,
            deployment.form_factor
        )

        # PPA 계산
        chip_config = ChipConfig(
            process_node_nm=process_node,
            cpu_cores=8,
            gpu_cores=0,
            npu_cores=npu_cores,
            l2_cache_mb=16,
            l3_cache_mb=64,
            pcie_lanes=32,
            memory_channels=8,
            target_frequency_ghz=2.0
        )

        ppa_result = self.ppa_engine.calculate(chip_config)

        # 전력 조정
        adjusted_power = ppa_result.power_tdp_w * power_factor

        # 비용 계산
        cost_result = self.cost_simulator.calculate_cost(
            die_size=ppa_result.die_size_mm2,
            node_nm=process_node,
            volume=deployment.volume_per_year,
            target_asp=ppa_result.die_size_mm2 * 5
        )

        # 매치 스코어 계산
        match_score = self._calculate_match_score(
            ppa_result,
            adjusted_power,
            memory_bw,
            power_constraints,
            characterization
        )

        # 근거 생성
        justifications = self._generate_justifications(
            profile, characterization, ppa_result, memory_type
        )

        # 트레이드오프 생성
        trade_offs = self._generate_trade_offs(variant, ppa_result, memory_type)

        return RecommendedArchitecture(
            name=name,
            description=desc,
            process_node_nm=process_node,
            npu_cores=npu_cores,
            cpu_cores=8,
            gpu_cores=0,
            memory_type=memory_type,
            memory_capacity_gb=memory_capacity,
            memory_bandwidth_tbps=memory_bw,
            die_size_mm2=round(ppa_result.die_size_mm2, 1),
            power_tdp_w=round(adjusted_power, 1),
            performance_tops=round(ppa_result.performance_tops * perf_factor, 1),
            efficiency_tops_per_watt=round(
                (ppa_result.performance_tops * perf_factor) / adjusted_power, 2
            ),
            estimated_unit_cost=round(cost_result.total_unit_cost, 2),
            match_score=round(match_score, 1),
            is_recommended=False,
            justifications=justifications,
            trade_offs=trade_offs
        )

    def _calculate_match_score(
        self,
        ppa_result,
        power: float,
        memory_bw: float,
        power_constraints: PowerConstraints,
        characterization: WorkloadCharacterization
    ) -> float:
        """매치 스코어 계산 (0-100)"""
        score = 100.0

        # 전력 제약 위반 시 감점
        if power > power_constraints.max_tdp_watts:
            excess = (power - power_constraints.max_tdp_watts) / power_constraints.max_tdp_watts
            score -= min(30, excess * 100)

        # 성능 부족 시 감점
        if ppa_result.performance_tops < characterization.required_tops:
            deficit = 1 - (ppa_result.performance_tops / characterization.required_tops)
            score -= min(40, deficit * 100)

        # 효율 목표 미달 시 감점
        actual_efficiency = ppa_result.performance_tops / power
        if actual_efficiency < power_constraints.target_efficiency_tops_per_watt:
            deficit = 1 - (actual_efficiency / power_constraints.target_efficiency_tops_per_watt)
            score -= min(20, deficit * 50)

        return max(0, min(100, score))

    def _generate_justifications(
        self,
        profile: WorkloadProfile,
        characterization: WorkloadCharacterization,
        ppa_result,
        memory_type: MemoryType
    ) -> list[str]:
        """추천 근거 생성"""
        justifications = []

        if characterization.compute_intensity == "Memory-Bound":
            justifications.append(
                f"워크로드가 메모리 대역폭에 제한됨 → {memory_type.value} 선택으로 대역폭 확보"
            )

        if profile.workload_type == WorkloadType.AI_INFERENCE:
            justifications.append(
                f"AI 추론 워크로드 최적화: {ppa_result.performance_tops:.0f} TOPS 제공"
            )

        if profile.deployment_context.form_factor == FormFactor.DATA_CENTER:
            justifications.append(
                "데이터센터 배포: 높은 처리량과 멀티 인스턴스 지원"
            )

        justifications.append(
            f"목표 지연시간 {profile.compute_requirements.target_latency_ms}ms 달성 가능"
        )

        return justifications

    def _generate_trade_offs(
        self,
        variant: str,
        ppa_result,
        memory_type: MemoryType
    ) -> list[str]:
        """트레이드오프 생성"""
        trade_offs = []

        if ppa_result.die_size_mm2 > 500:
            trade_offs.append("대형 다이 사이즈로 수율 영향 가능")

        if memory_type in [MemoryType.HBM3, MemoryType.HBM3E, MemoryType.HBM4]:
            trade_offs.append("HBM 패키징으로 인한 비용 증가")

        if variant == "high_performance":
            trade_offs.append("고성능 설계로 발열 관리 필요")
        elif variant == "low_power":
            trade_offs.append("저전력 설계로 피크 성능 제한")

        return trade_offs

    def get_competitive_benchmarks(
        self,
        characterization: WorkloadCharacterization,
        recommended: RecommendedArchitecture,
        precision: Precision
    ) -> list[CompetitiveBenchmark]:
        """경쟁사 벤치마크 생성"""
        benchmarks = []

        for name, specs in COMPETITOR_SPECS.items():
            # 정밀도에 따른 TOPS 선택
            if precision in [Precision.INT8, Precision.INT4]:
                competitor_tops = specs["tops_int8"]
            else:
                competitor_tops = specs["tops_fp16"]

            # 비교 분석
            perf_ratio = recommended.performance_tops / competitor_tops
            price_ratio = specs["price_estimate"] / recommended.estimated_unit_cost
            efficiency_ours = recommended.performance_tops / recommended.power_tdp_w
            efficiency_competitor = competitor_tops / specs["power_w"]
            efficiency_ratio = efficiency_ours / efficiency_competitor

            # 요약 생성
            summary_parts = []
            if perf_ratio > 1.1:
                summary_parts.append(f"{(perf_ratio-1)*100:.0f}% 높은 성능")
            elif perf_ratio < 0.9:
                summary_parts.append(f"{(1-perf_ratio)*100:.0f}% 낮은 성능")

            if efficiency_ratio > 1.1:
                summary_parts.append(f"{(efficiency_ratio-1)*100:.0f}% 높은 효율")

            if price_ratio > 2:
                summary_parts.append(f"{(price_ratio-1)*100:.0f}% 비용 절감")

            summary = ", ".join(summary_parts) if summary_parts else "유사한 성능"

            benchmarks.append(CompetitiveBenchmark(
                competitor_name=name,
                performance_tops=competitor_tops,
                power_tdp_w=specs["power_w"],
                memory_bandwidth_tbps=specs["bandwidth_tbps"],
                estimated_price=specs["price_estimate"],
                comparison_summary=summary
            ))

        return benchmarks

    def analyze(self, profile: WorkloadProfile) -> WorkloadAnalysisResult:
        """
        워크로드 분석 메인 함수

        Args:
            profile: 워크로드 프로파일

        Returns:
            완전한 분석 결과
        """
        # 1. 워크로드 특성 분석
        characterization = self.characterize_workload(profile)

        # 2. 아키텍처 옵션 생성
        architectures = []

        for variant in ["balanced", "low_power", "high_performance"]:
            arch = self.generate_architecture(profile, characterization, variant)
            architectures.append(arch)

        # 3. 최고 점수 아키텍처를 추천으로 마킹
        architectures.sort(key=lambda x: x.match_score, reverse=True)
        if architectures:
            # 첫 번째를 추천으로 설정
            best = architectures[0]
            architectures[0] = RecommendedArchitecture(
                **{**best.__dict__, "is_recommended": True}
            )

        # 4. 경쟁사 벤치마크
        benchmarks = self.get_competitive_benchmarks(
            characterization,
            architectures[0] if architectures else None,
            profile.compute_requirements.precision
        )

        # 5. 신뢰도 점수 계산
        confidence = self._calculate_confidence(profile, characterization)

        # 6. 분석 노트
        notes = self._generate_analysis_notes(profile, characterization)

        return WorkloadAnalysisResult(
            workload_profile=profile,
            characterization=characterization,
            recommended_architectures=architectures,
            competitive_benchmarks=benchmarks,
            confidence_score=confidence,
            analysis_notes=notes
        )

    def _calculate_confidence(
        self,
        profile: WorkloadProfile,
        characterization: WorkloadCharacterization
    ) -> float:
        """신뢰도 점수 계산"""
        confidence = 85.0

        # 잘 알려진 워크로드 타입은 높은 신뢰도
        if profile.workload_type in [WorkloadType.AI_INFERENCE, WorkloadType.IMAGE_PROCESSING]:
            confidence += 5

        # 일반적인 대역폭 범위면 신뢰도 증가
        if 100 <= profile.memory_requirements.bandwidth_requirement_gbps <= 2000:
            confidence += 5

        # 극단적인 요구사항은 신뢰도 감소
        if characterization.required_tops > 5000:
            confidence -= 10

        return max(50, min(95, confidence))

    def _generate_analysis_notes(
        self,
        profile: WorkloadProfile,
        characterization: WorkloadCharacterization
    ) -> list[str]:
        """분석 노트 생성"""
        notes = []

        notes.append(
            f"워크로드 특성: {characterization.compute_intensity} "
            f"(Arithmetic Intensity: {characterization.arithmetic_intensity:.1f})"
        )

        if characterization.bottleneck == "Memory Bandwidth":
            notes.append(
                "권장: HBM 메모리 채택으로 대역폭 병목 해소"
            )

        if profile.power_constraints.max_tdp_watts < 100:
            notes.append(
                "저전력 요구사항으로 인해 성능 트레이드오프 필요"
            )

        return notes
