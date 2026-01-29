import math
from dataclasses import dataclass


@dataclass
class YieldResult:
    yield_rate: float  # 0-1
    gross_die: int
    net_die: int
    defect_density: float
    die_size: float


class YieldModel:
    """
    반도체 수율 계산 모델
    Murphy's Yield Model 기반
    """

    WAFER_DIAMETER_MM = 300
    EDGE_EXCLUSION_MM = 3

    @classmethod
    def calculate_usable_area(cls) -> float:
        """웨이퍼의 사용 가능한 면적 계산 (mm²)"""
        radius = (cls.WAFER_DIAMETER_MM / 2) - cls.EDGE_EXCLUSION_MM
        return math.pi * (radius ** 2)

    @classmethod
    def calculate_gross_die(cls, die_size: float) -> int:
        """
        웨이퍼당 총 다이 개수 계산 (불량품 포함)

        Args:
            die_size: 다이 면적 (mm²)

        Returns:
            웨이퍼당 총 다이 개수
        """
        usable_area = cls.calculate_usable_area()
        # 간단한 모델: 면적 나누기 (실제로는 더 복잡한 다이 배치 알고리즘 사용)
        return int(usable_area / die_size)

    @classmethod
    def murphy_yield(cls, die_size: float, defect_density: float) -> float:
        """
        Murphy's Yield Model

        Y = ((1 - exp(-A*D)) / (A*D))²

        Args:
            die_size: 다이 면적 (mm²)
            defect_density: 결함 밀도 (defects/cm²)

        Returns:
            수율 (0-1)
        """
        # mm² to cm² conversion for defect density calculation
        die_size_cm2 = die_size / 100
        factor = defect_density * die_size_cm2

        if factor < 0.001:
            return 0.99  # 매우 작은 다이는 높은 수율

        try:
            yield_rate = ((1 - math.exp(-factor)) / factor) ** 2
            return min(max(yield_rate, 0.0), 0.99)  # 0-99% 범위로 제한
        except (ZeroDivisionError, OverflowError):
            return 0.5

    @classmethod
    def poisson_yield(cls, die_size: float, defect_density: float) -> float:
        """
        Poisson Yield Model (대안 모델)

        Y = exp(-A*D)

        Args:
            die_size: 다이 면적 (mm²)
            defect_density: 결함 밀도 (defects/cm²)

        Returns:
            수율 (0-1)
        """
        die_size_cm2 = die_size / 100
        factor = defect_density * die_size_cm2
        return math.exp(-factor)

    @classmethod
    def calculate(
        cls,
        die_size: float,
        defect_density: float,
        model: str = "murphy"
    ) -> YieldResult:
        """
        수율 및 다이 수량 종합 계산

        Args:
            die_size: 다이 면적 (mm²)
            defect_density: 결함 밀도 (defects/cm²)
            model: 수율 모델 ("murphy" or "poisson")

        Returns:
            YieldResult with all calculations
        """
        if model == "murphy":
            yield_rate = cls.murphy_yield(die_size, defect_density)
        else:
            yield_rate = cls.poisson_yield(die_size, defect_density)

        gross_die = cls.calculate_gross_die(die_size)
        net_die = int(gross_die * yield_rate)

        return YieldResult(
            yield_rate=yield_rate,
            gross_die=gross_die,
            net_die=net_die,
            defect_density=defect_density,
            die_size=die_size
        )
