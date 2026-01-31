from dataclasses import dataclass
from typing import Optional


@dataclass
class ChipConfig:
    """칩 구성 입력 파라미터"""
    process_node_nm: int  # 3, 5, 7
    cpu_cores: int
    gpu_cores: int = 0
    npu_cores: int = 0
    l2_cache_mb: float = 4.0
    l3_cache_mb: float = 0.0
    pcie_lanes: int = 16
    memory_channels: int = 2
    target_frequency_ghz: float = 3.0


@dataclass
class ProcessParams:
    """공정 노드별 파라미터"""
    node_nm: int
    base_core_area: float  # mm² per CPU core
    gpu_core_area: float  # mm² per GPU core
    npu_core_area: float  # mm² per NPU core
    cache_density: float  # mm² per MB
    io_area_per_lane: float  # mm² per PCIe lane
    memory_ctrl_area: float  # mm² per memory channel
    power_density: float  # mW per mm²
    max_frequency_ghz: float
    scaling_factor: float = 1.0


@dataclass
class PPAResult:
    """PPA 계산 결과"""
    die_size_mm2: float
    power_tdp_w: float
    performance_ghz: float
    performance_tops: float  # for AI workloads
    area_breakdown: dict
    power_breakdown: dict
    efficiency_tops_per_watt: float
    confidence_score: float


# 공정 노드별 기본 파라미터 - 온톨로지에서 확장
def _build_process_params() -> dict:
    """반도체 온톨로지에서 공정 노드 파라미터 구축"""
    # 기본 파라미터 (항상 사용 가능한 폴백)
    base_params = {
        3: ProcessParams(
            node_nm=3, base_core_area=0.50, gpu_core_area=0.15,
            npu_core_area=0.20, cache_density=0.35, io_area_per_lane=0.25,
            memory_ctrl_area=2.5, power_density=0.45, max_frequency_ghz=4.0,
        ),
        5: ProcessParams(
            node_nm=5, base_core_area=0.65, gpu_core_area=0.20,
            npu_core_area=0.28, cache_density=0.45, io_area_per_lane=0.30,
            memory_ctrl_area=3.0, power_density=0.40, max_frequency_ghz=3.5,
        ),
        7: ProcessParams(
            node_nm=7, base_core_area=0.85, gpu_core_area=0.28,
            npu_core_area=0.38, cache_density=0.60, io_area_per_lane=0.38,
            memory_ctrl_area=3.8, power_density=0.35, max_frequency_ghz=3.0,
        ),
    }

    # 1차: Neo4j 그래프에서 로드 시도
    try:
        from app.neo4j_client import Neo4jClient
        if Neo4jClient.is_available():
            records = Neo4jClient.run_query(
                "MATCH (n:ProcessNode) RETURN n.key AS key, n.node_nm AS node_nm, "
                "n.logic_density_mtr_per_mm2 AS density, n.wafer_cost_usd AS wafer_cost"
            )
            if records:
                for r in records:
                    nm = r["node_nm"]
                    nm_int = max(2, round(nm))
                    if nm_int in base_params:
                        continue
                    scale = nm_int / 3.0
                    base_params[nm_int] = ProcessParams(
                        node_nm=nm_int,
                        base_core_area=round(0.50 * scale, 3),
                        gpu_core_area=round(0.15 * scale, 3),
                        npu_core_area=round(0.20 * scale, 3),
                        cache_density=round(0.35 * scale, 3),
                        io_area_per_lane=round(0.25 * scale, 3),
                        memory_ctrl_area=round(2.5 * scale, 2),
                        power_density=round(0.45 / scale, 3),
                        max_frequency_ghz=round(4.0 / (scale ** 0.3), 1),
                        scaling_factor=round(scale, 2),
                    )
                return base_params
    except Exception:
        pass

    # 2차: 인메모리 온톨로지에서 확장
    try:
        from app.ontology import SemiconductorOntology
        all_nodes = SemiconductorOntology.get_all_nodes()
        for key, node in all_nodes.items():
            nm = node.node_nm
            nm_int = max(2, round(nm))  # Sub-2nm → 2nm bucket
            if nm_int in base_params:
                continue  # 기존 정밀 파라미터 유지
            # 3nm 기준 스케일링으로 추가 노드 생성
            scale = nm_int / 3.0
            base_params[nm_int] = ProcessParams(
                node_nm=nm_int,
                base_core_area=round(0.50 * scale, 3),
                gpu_core_area=round(0.15 * scale, 3),
                npu_core_area=round(0.20 * scale, 3),
                cache_density=round(0.35 * scale, 3),
                io_area_per_lane=round(0.25 * scale, 3),
                memory_ctrl_area=round(2.5 * scale, 2),
                power_density=round(0.45 / scale, 3),
                max_frequency_ghz=round(4.0 / (scale ** 0.3), 1),
                scaling_factor=round(scale, 2),
            )
    except Exception:
        pass  # 온톨로지 미사용 시 기본값 유지

    return base_params

DEFAULT_PROCESS_PARAMS = _build_process_params()


class PPAEngine:
    """
    PPA (Power, Performance, Area) 계산 엔진
    반도체 칩의 전력, 성능, 면적 트레이드오프 시뮬레이션
    """

    ROUTING_OVERHEAD = 0.15  # 15% routing/padding overhead
    NPU_TOPS_PER_CORE = 8.0  # TOPS per NPU core (INT8)

    def __init__(self, process_params: Optional[dict] = None):
        self.process_params = process_params or DEFAULT_PROCESS_PARAMS

    def get_process_params(self, node_nm: int) -> ProcessParams:
        """공정 노드 파라미터 조회"""
        if node_nm not in self.process_params:
            raise ValueError(f"Unsupported process node: {node_nm}nm")
        return self.process_params[node_nm]

    def calculate_area(self, config: ChipConfig) -> tuple[float, dict]:
        """
        다이 면적 계산

        Returns:
            (total_die_size, area_breakdown)
        """
        params = self.get_process_params(config.process_node_nm)

        # 각 컴포넌트별 면적 계산
        cpu_area = params.base_core_area * config.cpu_cores * params.scaling_factor
        gpu_area = params.gpu_core_area * config.gpu_cores * params.scaling_factor
        npu_area = params.npu_core_area * config.npu_cores * params.scaling_factor
        l2_cache_area = config.l2_cache_mb * params.cache_density
        l3_cache_area = config.l3_cache_mb * params.cache_density
        io_area = config.pcie_lanes * params.io_area_per_lane
        memory_area = config.memory_channels * params.memory_ctrl_area

        # 기능 영역 합계
        functional_area = (
            cpu_area + gpu_area + npu_area +
            l2_cache_area + l3_cache_area +
            io_area + memory_area
        )

        # 라우팅/패딩 오버헤드 추가
        overhead_area = functional_area * self.ROUTING_OVERHEAD
        total_area = functional_area + overhead_area

        area_breakdown = {
            "cpu": round(cpu_area, 2),
            "gpu": round(gpu_area, 2),
            "npu": round(npu_area, 2),
            "l2_cache": round(l2_cache_area, 2),
            "l3_cache": round(l3_cache_area, 2),
            "io": round(io_area, 2),
            "memory_controller": round(memory_area, 2),
            "overhead": round(overhead_area, 2),
            "total": round(total_area, 2)
        }

        return total_area, area_breakdown

    def calculate_power(self, config: ChipConfig, die_size: float) -> tuple[float, dict]:
        """
        TDP(Thermal Design Power) 계산

        Returns:
            (total_power_w, power_breakdown)
        """
        params = self.get_process_params(config.process_node_nm)

        # 주파수 스케일링 팩터
        freq_ratio = config.target_frequency_ghz / params.max_frequency_ghz
        freq_scaling = freq_ratio ** 2  # 전력은 주파수의 제곱에 비례

        # 기본 전력 (면적 기반)
        base_power_mw = die_size * params.power_density * 1000  # W to mW

        # 컴포넌트별 전력 비율 추정
        cpu_power = config.cpu_cores * 800 * freq_scaling  # mW per core
        gpu_power = config.gpu_cores * 150 * freq_scaling  # mW per GPU core
        npu_power = config.npu_cores * 200  # NPU는 고정 전력
        cache_power = (config.l2_cache_mb + config.l3_cache_mb) * 50  # mW per MB
        io_power = config.pcie_lanes * 30 + config.memory_channels * 500  # mW

        total_power_mw = cpu_power + gpu_power + npu_power + cache_power + io_power
        total_power_w = total_power_mw / 1000

        power_breakdown = {
            "cpu": round(cpu_power / 1000, 2),
            "gpu": round(gpu_power / 1000, 2),
            "npu": round(npu_power / 1000, 2),
            "cache": round(cache_power / 1000, 2),
            "io": round(io_power / 1000, 2),
            "total": round(total_power_w, 2)
        }

        return total_power_w, power_breakdown

    def calculate_performance(self, config: ChipConfig) -> tuple[float, float]:
        """
        성능 지표 계산

        Returns:
            (frequency_ghz, ai_tops)
        """
        params = self.get_process_params(config.process_node_nm)

        # 실제 달성 가능한 주파수 (목표와 최대 중 낮은 값)
        actual_freq = min(config.target_frequency_ghz, params.max_frequency_ghz)

        # AI 연산 성능 (TOPS)
        ai_tops = config.npu_cores * self.NPU_TOPS_PER_CORE

        return actual_freq, ai_tops

    def calculate(self, config: ChipConfig) -> PPAResult:
        """
        종합 PPA 계산

        Args:
            config: 칩 구성 파라미터

        Returns:
            PPAResult with all metrics
        """
        # Area 계산
        die_size, area_breakdown = self.calculate_area(config)

        # Power 계산
        power_w, power_breakdown = self.calculate_power(config, die_size)

        # Performance 계산
        freq_ghz, ai_tops = self.calculate_performance(config)

        # 효율 지표
        efficiency = ai_tops / power_w if power_w > 0 and ai_tops > 0 else 0

        # 신뢰도 점수 (공정 노드 성숙도 기반)
        confidence_map = {3: 75, 5: 90, 7: 95}
        confidence = confidence_map.get(config.process_node_nm, 70)

        return PPAResult(
            die_size_mm2=round(die_size, 2),
            power_tdp_w=round(power_w, 2),
            performance_ghz=round(freq_ghz, 2),
            performance_tops=round(ai_tops, 2),
            area_breakdown=area_breakdown,
            power_breakdown=power_breakdown,
            efficiency_tops_per_watt=round(efficiency, 3),
            confidence_score=confidence
        )

    def generate_alternatives(self, config: ChipConfig) -> list[tuple[str, PPAResult]]:
        """
        대안 구성 생성 (Low Power, High Performance)
        """
        alternatives = []

        # Current configuration
        current = self.calculate(config)
        alternatives.append(("current", current))

        # Low Power variant
        low_power_config = ChipConfig(
            process_node_nm=config.process_node_nm,
            cpu_cores=max(config.cpu_cores - 2, 2),
            gpu_cores=max(config.gpu_cores - 4, 0),
            npu_cores=config.npu_cores,
            l2_cache_mb=config.l2_cache_mb,
            l3_cache_mb=max(config.l3_cache_mb - 16, 0),
            pcie_lanes=config.pcie_lanes,
            memory_channels=config.memory_channels,
            target_frequency_ghz=config.target_frequency_ghz * 0.85
        )
        low_power = self.calculate(low_power_config)
        alternatives.append(("low_power", low_power))

        # High Performance variant
        high_perf_config = ChipConfig(
            process_node_nm=config.process_node_nm,
            cpu_cores=config.cpu_cores + 4,
            gpu_cores=config.gpu_cores + 8,
            npu_cores=config.npu_cores,
            l2_cache_mb=config.l2_cache_mb * 1.5,
            l3_cache_mb=config.l3_cache_mb + 32,
            pcie_lanes=config.pcie_lanes,
            memory_channels=config.memory_channels,
            target_frequency_ghz=min(config.target_frequency_ghz * 1.15, 4.5)
        )
        high_perf = self.calculate(high_perf_config)
        alternatives.append(("high_performance", high_perf))

        return alternatives
