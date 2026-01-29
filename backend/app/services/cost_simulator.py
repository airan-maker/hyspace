from dataclasses import dataclass
from typing import Optional
from .yield_model import YieldModel


@dataclass
class CostBreakdown:
    """비용 분석 결과"""
    wafer_cost: float
    die_cost: float
    good_die_cost: float
    package_cost: float
    test_cost: float
    total_unit_cost: float
    target_asp: float
    gross_margin: float
    gross_margin_percent: float
    net_die_per_wafer: int
    yield_rate: float


@dataclass
class VolumeEconomics:
    """볼륨별 경제성 분석"""
    volume: int
    unit_cost: float
    total_cost: float
    volume_discount: float
    break_even_volume: int


# 공정 노드별 웨이퍼 비용 (USD)
DEFAULT_WAFER_COSTS = {
    3: 20000,
    5: 16000,
    7: 10000,
    10: 6000,
    14: 4000,
}

# 공정 노드별 결함 밀도 (defects/cm²)
DEFAULT_DEFECT_DENSITY = {
    3: 0.12,  # 신규 공정, 높은 결함률
    5: 0.08,  # 성숙 공정
    7: 0.05,  # 매우 성숙한 공정
    10: 0.04,
    14: 0.03,
}


class CostSimulator:
    """
    반도체 제조 비용 시뮬레이터
    웨이퍼 비용, 수율, 패키징, 테스트 비용을 종합 계산
    """

    def __init__(
        self,
        wafer_costs: Optional[dict] = None,
        defect_densities: Optional[dict] = None
    ):
        self.wafer_costs = wafer_costs or DEFAULT_WAFER_COSTS
        self.defect_densities = defect_densities or DEFAULT_DEFECT_DENSITY

    def get_wafer_cost(self, node_nm: int) -> float:
        """공정 노드별 웨이퍼 비용 조회"""
        return self.wafer_costs.get(node_nm, 8000)

    def get_defect_density(self, node_nm: int) -> float:
        """공정 노드별 결함 밀도 조회"""
        return self.defect_densities.get(node_nm, 0.06)

    def estimate_package_cost(self, die_size: float, node_nm: int) -> float:
        """
        패키징 비용 추정

        다이 크기와 공정에 따라 패키징 복잡도 결정
        """
        # 기본 패키지 비용
        base_cost = 3.0

        # 다이 크기에 따른 비용 증가
        if die_size > 100:
            size_factor = 1.5 + (die_size - 100) * 0.02
        elif die_size > 50:
            size_factor = 1.2
        else:
            size_factor = 1.0

        # 선단 공정은 고급 패키징 필요 (CoWoS 등)
        if node_nm <= 5:
            advanced_factor = 2.0
        elif node_nm <= 7:
            advanced_factor = 1.5
        else:
            advanced_factor = 1.0

        return base_cost * size_factor * advanced_factor

    def estimate_test_cost(self, die_size: float) -> float:
        """
        테스트 비용 추정

        다이 크기가 클수록 테스트 시간 증가
        """
        base_test_cost = 1.5
        size_factor = 1.0 + (die_size / 200)  # 200mm² 기준
        return base_test_cost * size_factor

    def calculate_volume_discount(self, volume: int) -> float:
        """
        대량 생산 할인율 계산

        볼륨이 증가할수록 단가 감소
        """
        if volume >= 1000000:
            return 0.75  # 25% 할인
        elif volume >= 500000:
            return 0.82
        elif volume >= 100000:
            return 0.88
        elif volume >= 50000:
            return 0.93
        elif volume >= 10000:
            return 0.97
        else:
            return 1.0

    def calculate_cost(
        self,
        die_size: float,
        node_nm: int,
        volume: int = 100000,
        target_asp: float = 100.0
    ) -> CostBreakdown:
        """
        종합 비용 계산

        Args:
            die_size: 다이 면적 (mm²)
            node_nm: 공정 노드 (nm)
            volume: 연간 생산량
            target_asp: 목표 판매가 (USD)

        Returns:
            CostBreakdown with all cost metrics
        """
        wafer_cost = self.get_wafer_cost(node_nm)
        defect_density = self.get_defect_density(node_nm)

        # 수율 계산
        yield_result = YieldModel.calculate(die_size, defect_density)

        # 다이 비용
        if yield_result.gross_die > 0:
            die_cost = wafer_cost / yield_result.gross_die
        else:
            die_cost = wafer_cost  # fallback

        # 양품 다이 비용 (수율 반영)
        if yield_result.yield_rate > 0:
            good_die_cost = die_cost / yield_result.yield_rate
        else:
            good_die_cost = die_cost * 2  # fallback

        # 패키징 및 테스트 비용
        package_cost = self.estimate_package_cost(die_size, node_nm)
        test_cost = self.estimate_test_cost(die_size)

        # 총 단가
        base_unit_cost = good_die_cost + package_cost + test_cost

        # 볼륨 할인 적용
        volume_discount = self.calculate_volume_discount(volume)
        total_unit_cost = base_unit_cost * volume_discount

        # 마진 계산
        gross_margin = target_asp - total_unit_cost
        gross_margin_percent = (gross_margin / target_asp * 100) if target_asp > 0 else 0

        return CostBreakdown(
            wafer_cost=round(wafer_cost, 2),
            die_cost=round(die_cost, 2),
            good_die_cost=round(good_die_cost, 2),
            package_cost=round(package_cost, 2),
            test_cost=round(test_cost, 2),
            total_unit_cost=round(total_unit_cost, 2),
            target_asp=round(target_asp, 2),
            gross_margin=round(gross_margin, 2),
            gross_margin_percent=round(gross_margin_percent, 1),
            net_die_per_wafer=yield_result.net_die,
            yield_rate=round(yield_result.yield_rate * 100, 1)
        )

    def analyze_volume_economics(
        self,
        die_size: float,
        node_nm: int,
        target_asp: float,
        volumes: list[int] = None
    ) -> list[VolumeEconomics]:
        """
        볼륨별 경제성 분석
        """
        if volumes is None:
            volumes = [10000, 50000, 100000, 500000, 1000000]

        results = []
        fixed_costs = 50000000  # 마스크, NRE 등 고정비용 (예시)

        for volume in volumes:
            cost_result = self.calculate_cost(
                die_size, node_nm, volume, target_asp
            )

            # 고정비용 분담
            fixed_per_unit = fixed_costs / volume if volume > 0 else fixed_costs
            total_unit_cost = cost_result.total_unit_cost + fixed_per_unit

            total_cost = total_unit_cost * volume
            volume_discount = self.calculate_volume_discount(volume)

            # 손익분기점 계산
            margin_per_unit = target_asp - total_unit_cost
            if margin_per_unit > 0:
                break_even = int(fixed_costs / margin_per_unit)
            else:
                break_even = -1  # 손익분기 불가

            results.append(VolumeEconomics(
                volume=volume,
                unit_cost=round(total_unit_cost, 2),
                total_cost=round(total_cost, 2),
                volume_discount=round(volume_discount, 2),
                break_even_volume=break_even
            ))

        return results

    def compare_nodes(
        self,
        die_sizes: dict[int, float],
        volume: int = 100000,
        target_asp: float = 100.0
    ) -> dict[int, CostBreakdown]:
        """
        여러 공정 노드 간 비용 비교

        Args:
            die_sizes: {node_nm: die_size} 매핑
            volume: 생산량
            target_asp: 목표 ASP

        Returns:
            {node_nm: CostBreakdown} 매핑
        """
        results = {}
        for node_nm, die_size in die_sizes.items():
            results[node_nm] = self.calculate_cost(
                die_size, node_nm, volume, target_asp
            )
        return results
