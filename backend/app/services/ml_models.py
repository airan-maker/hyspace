"""
Machine Learning Models for Predictive Analytics

수율 예측, 장비 고장 예측, 수요 예측을 위한 ML 모델 정의
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Any
from enum import Enum
import random
import math


class ModelType(str, Enum):
    YIELD_PREDICTION = "YIELD_PREDICTION"
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    DEMAND_FORECAST = "DEMAND_FORECAST"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"
    QUALITY_PREDICTION = "QUALITY_PREDICTION"


class ModelStatus(str, Enum):
    TRAINING = "TRAINING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    RETRAINING = "RETRAINING"
    FAILED = "FAILED"


@dataclass
class ModelMetrics:
    """모델 성능 메트릭"""
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mae: Optional[float] = None  # Mean Absolute Error
    rmse: Optional[float] = None  # Root Mean Square Error
    mape: Optional[float] = None  # Mean Absolute Percentage Error
    r2_score: Optional[float] = None
    auc_roc: Optional[float] = None


@dataclass
class PredictionResult:
    """예측 결과"""
    prediction_id: str
    model_type: ModelType
    timestamp: datetime
    input_features: dict
    predicted_value: Any
    confidence: float
    confidence_interval: tuple[float, float]
    contributing_factors: list[dict]
    warnings: list[str] = field(default_factory=list)


@dataclass
class YieldPrediction(PredictionResult):
    """수율 예측 결과"""
    predicted_yield: float = 0.0
    yield_range: tuple[float, float] = (0.0, 0.0)
    risk_factors: list[dict] = field(default_factory=list)
    optimization_suggestions: list[str] = field(default_factory=list)


@dataclass
class FailurePrediction(PredictionResult):
    """장비 고장 예측 결과"""
    equipment_id: str = ""
    failure_probability: float = 0.0
    estimated_failure_time: Optional[datetime] = None
    remaining_useful_life_hours: Optional[float] = None
    maintenance_recommendation: str = ""
    failure_mode: Optional[str] = None


@dataclass
class DemandForecast(PredictionResult):
    """수요 예측 결과"""
    forecast_period: str = ""
    forecasted_demand: float = 0.0
    demand_range: tuple[float, float] = (0.0, 0.0)
    trend: str = ""  # INCREASING, DECREASING, STABLE
    seasonality_factor: float = 1.0


class BaseMLModel:
    """ML 모델 기본 클래스"""

    def __init__(self, model_id: str, model_type: ModelType):
        self.model_id = model_id
        self.model_type = model_type
        self.status = ModelStatus.READY
        self.version = "1.0.0"
        self.last_trained = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        self.metrics = ModelMetrics()
        self.feature_importance: dict[str, float] = {}

    def predict(self, features: dict) -> PredictionResult:
        raise NotImplementedError

    def get_feature_importance(self) -> dict[str, float]:
        return self.feature_importance


class YieldPredictionModel(BaseMLModel):
    """
    수율 예측 모델

    Input: 공정 파라미터, 장비 상태, 환경 데이터
    Output: 예상 수율 (%)
    Algorithm: XGBoost / LightGBM (시뮬레이션)
    """

    def __init__(self):
        super().__init__("yield_pred_v1", ModelType.YIELD_PREDICTION)
        self.metrics = ModelMetrics(
            accuracy=0.92,
            mae=1.8,
            rmse=2.4,
            mape=2.1,
            r2_score=0.89
        )
        self.feature_importance = {
            "temperature": 0.18,
            "pressure": 0.15,
            "flow_rate": 0.12,
            "humidity": 0.10,
            "equipment_age_days": 0.09,
            "equipment_oee": 0.11,
            "process_time": 0.08,
            "wafer_position": 0.07,
            "previous_yield": 0.06,
            "shift": 0.04
        }

    def predict(self, features: dict) -> YieldPrediction:
        """수율 예측 수행"""
        import uuid

        # 기본 수율 (시뮬레이션)
        base_yield = 92.0

        # 온도 영향
        temp = features.get("temperature", 23.0)
        temp_effect = -abs(temp - 23.0) * 0.5

        # 압력 영향
        pressure = features.get("pressure", 1.0)
        pressure_effect = -abs(pressure - 1.0) * 2.0

        # 장비 OEE 영향
        oee = features.get("equipment_oee", 85.0)
        oee_effect = (oee - 85.0) * 0.1

        # 습도 영향
        humidity = features.get("humidity", 45.0)
        humidity_effect = -abs(humidity - 45.0) * 0.05

        # 최종 예측
        predicted = base_yield + temp_effect + pressure_effect + oee_effect + humidity_effect
        predicted = max(70.0, min(99.5, predicted + random.uniform(-1.5, 1.5)))

        # 신뢰도 계산
        confidence = 0.85 + random.uniform(0, 0.12)
        margin = (1 - confidence) * predicted * 0.1

        # 리스크 요인 분석
        risk_factors = []
        if temp < 21.0 or temp > 25.0:
            risk_factors.append({
                "factor": "temperature",
                "current_value": temp,
                "optimal_range": "21-25°C",
                "impact": "수율 저하 가능성"
            })
        if oee < 80.0:
            risk_factors.append({
                "factor": "equipment_oee",
                "current_value": oee,
                "optimal_range": "> 85%",
                "impact": "장비 효율 저하로 인한 수율 감소"
            })

        # 최적화 제안
        suggestions = []
        if temp_effect < -0.5:
            suggestions.append("온도를 23±2°C 범위로 조정하세요")
        if pressure_effect < -0.5:
            suggestions.append("압력을 1.0±0.1 bar로 조정하세요")
        if oee_effect < 0:
            suggestions.append("장비 PM 일정을 확인하세요")

        contributing_factors = [
            {"feature": k, "importance": v, "value": features.get(k)}
            for k, v in sorted(self.feature_importance.items(), key=lambda x: -x[1])[:5]
        ]

        return YieldPrediction(
            prediction_id=f"YP-{uuid.uuid4().hex[:8].upper()}",
            model_type=self.model_type,
            timestamp=datetime.utcnow(),
            input_features=features,
            predicted_value=predicted,
            confidence=confidence,
            confidence_interval=(predicted - margin, predicted + margin),
            contributing_factors=contributing_factors,
            predicted_yield=predicted,
            yield_range=(predicted - margin, predicted + margin),
            risk_factors=risk_factors,
            optimization_suggestions=suggestions
        )


class EquipmentFailureModel(BaseMLModel):
    """
    장비 고장 예측 모델

    Input: 센서 데이터, 유지보수 이력
    Output: 고장 확률, 예상 시점
    Algorithm: LSTM / Prophet (시뮬레이션)
    """

    def __init__(self):
        super().__init__("equip_failure_v1", ModelType.EQUIPMENT_FAILURE)
        self.metrics = ModelMetrics(
            accuracy=0.88,
            precision=0.85,
            recall=0.82,
            f1_score=0.835,
            auc_roc=0.91
        )
        self.feature_importance = {
            "vibration_level": 0.22,
            "operating_hours": 0.18,
            "temperature_delta": 0.15,
            "maintenance_overdue_days": 0.14,
            "error_count_7d": 0.12,
            "power_consumption_delta": 0.08,
            "cycle_time_variance": 0.06,
            "age_days": 0.05
        }

        self.failure_modes = [
            "MOTOR_WEAR",
            "SEAL_DEGRADATION",
            "CONTAMINATION",
            "CALIBRATION_DRIFT",
            "ELECTRONIC_FAULT",
            "MECHANICAL_FATIGUE"
        ]

    def predict(self, features: dict) -> FailurePrediction:
        """장비 고장 예측 수행"""
        import uuid

        equipment_id = features.get("equipment_id", "EQ-UNKNOWN")

        # 기본 고장 확률 계산
        base_probability = 0.05

        # 진동 수준 영향
        vibration = features.get("vibration_level", 0.5)
        vibration_risk = max(0, (vibration - 0.7)) * 0.3

        # 운영 시간 영향
        operating_hours = features.get("operating_hours", 1000)
        hours_risk = min(0.2, operating_hours / 50000)

        # 유지보수 지연 영향
        maintenance_overdue = features.get("maintenance_overdue_days", 0)
        maintenance_risk = min(0.25, maintenance_overdue * 0.01)

        # 오류 빈도 영향
        error_count = features.get("error_count_7d", 0)
        error_risk = min(0.15, error_count * 0.03)

        # 최종 고장 확률
        failure_prob = base_probability + vibration_risk + hours_risk + maintenance_risk + error_risk
        failure_prob = min(0.95, max(0.01, failure_prob + random.uniform(-0.02, 0.02)))

        # 예상 고장 시점 계산
        if failure_prob > 0.3:
            hours_to_failure = int((1 - failure_prob) * 500 + random.randint(-50, 50))
            estimated_failure = datetime.utcnow() + timedelta(hours=max(12, hours_to_failure))
            rul_hours = hours_to_failure
        else:
            estimated_failure = None
            rul_hours = 1000 + random.randint(0, 500)

        # 고장 모드 예측
        failure_mode = None
        if failure_prob > 0.2:
            if vibration_risk > 0.1:
                failure_mode = "MOTOR_WEAR"
            elif maintenance_risk > 0.1:
                failure_mode = "CALIBRATION_DRIFT"
            elif error_count > 5:
                failure_mode = "ELECTRONIC_FAULT"
            else:
                failure_mode = random.choice(self.failure_modes)

        # 유지보수 권장사항
        if failure_prob > 0.5:
            recommendation = "즉시 예방 정비 필요 - 고장 위험 높음"
        elif failure_prob > 0.3:
            recommendation = "48시간 내 점검 권장 - 주의 관찰 필요"
        elif failure_prob > 0.15:
            recommendation = "다음 PM 주기에 집중 점검 권장"
        else:
            recommendation = "정상 운영 - 정기 PM 일정 유지"

        confidence = 0.80 + random.uniform(0, 0.15)

        contributing_factors = [
            {"feature": k, "importance": v, "value": features.get(k)}
            for k, v in sorted(self.feature_importance.items(), key=lambda x: -x[1])[:5]
        ]

        warnings = []
        if failure_prob > 0.5:
            warnings.append("고장 위험 높음 - 즉시 조치 필요")
        if maintenance_overdue > 7:
            warnings.append(f"유지보수 {maintenance_overdue}일 지연됨")
        if error_count > 10:
            warnings.append("최근 7일간 오류 빈도 높음")

        return FailurePrediction(
            prediction_id=f"FP-{uuid.uuid4().hex[:8].upper()}",
            model_type=self.model_type,
            timestamp=datetime.utcnow(),
            input_features=features,
            predicted_value=failure_prob,
            confidence=confidence,
            confidence_interval=(max(0, failure_prob - 0.1), min(1, failure_prob + 0.1)),
            contributing_factors=contributing_factors,
            warnings=warnings,
            equipment_id=equipment_id,
            failure_probability=failure_prob,
            estimated_failure_time=estimated_failure,
            remaining_useful_life_hours=rul_hours,
            maintenance_recommendation=recommendation,
            failure_mode=failure_mode
        )


class DemandForecastModel(BaseMLModel):
    """
    수요 예측 모델

    Input: 과거 주문, 시장 데이터
    Output: 향후 N주 수요 예측
    Algorithm: ARIMA / Prophet (시뮬레이션)
    """

    def __init__(self):
        super().__init__("demand_forecast_v1", ModelType.DEMAND_FORECAST)
        self.metrics = ModelMetrics(
            mae=125.5,
            rmse=180.2,
            mape=8.5,
            r2_score=0.85
        )
        self.feature_importance = {
            "historical_demand_4w": 0.25,
            "seasonality_index": 0.18,
            "market_growth_rate": 0.15,
            "customer_orders_pipeline": 0.14,
            "economic_indicator": 0.10,
            "competitor_activity": 0.08,
            "promotion_calendar": 0.06,
            "inventory_level": 0.04
        }

    def predict(self, features: dict) -> DemandForecast:
        """수요 예측 수행"""
        import uuid

        forecast_weeks = features.get("forecast_weeks", 4)
        product_category = features.get("product_category", "GENERAL")

        # 기본 수요 (시뮬레이션)
        base_demand = features.get("historical_demand_4w", 10000)

        # 시장 성장률 영향
        growth_rate = features.get("market_growth_rate", 0.02)
        growth_effect = base_demand * growth_rate * (forecast_weeks / 4)

        # 계절성 영향
        current_month = datetime.utcnow().month
        seasonality = {
            1: 0.85, 2: 0.90, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.10,
            7: 1.05, 8: 1.0, 9: 1.05, 10: 1.15, 11: 1.20, 12: 1.25
        }
        seasonality_factor = seasonality.get(current_month, 1.0)

        # 주문 파이프라인 영향
        pipeline = features.get("customer_orders_pipeline", 0)
        pipeline_effect = pipeline * 0.3

        # 경제 지표 영향
        economic_idx = features.get("economic_indicator", 100)
        economic_effect = base_demand * (economic_idx - 100) / 1000

        # 최종 예측
        forecasted = base_demand + growth_effect + pipeline_effect + economic_effect
        forecasted = forecasted * seasonality_factor
        forecasted = max(0, forecasted + random.uniform(-forecasted * 0.05, forecasted * 0.05))

        # 트렌드 결정
        if growth_rate > 0.03:
            trend = "INCREASING"
        elif growth_rate < -0.01:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        # 신뢰 구간
        confidence = 0.82 + random.uniform(0, 0.13)
        margin = (1 - confidence) * forecasted * 0.15

        contributing_factors = [
            {"feature": k, "importance": v, "value": features.get(k)}
            for k, v in sorted(self.feature_importance.items(), key=lambda x: -x[1])[:5]
        ]

        warnings = []
        if growth_rate < -0.05:
            warnings.append("수요 급감 예상 - 생산 조정 검토 필요")
        if growth_rate > 0.1:
            warnings.append("수요 급증 예상 - 재고 확보 권장")
        if seasonality_factor > 1.15:
            warnings.append("성수기 진입 - 생산 역량 확인 필요")

        return DemandForecast(
            prediction_id=f"DF-{uuid.uuid4().hex[:8].upper()}",
            model_type=self.model_type,
            timestamp=datetime.utcnow(),
            input_features=features,
            predicted_value=forecasted,
            confidence=confidence,
            confidence_interval=(forecasted - margin, forecasted + margin),
            contributing_factors=contributing_factors,
            warnings=warnings,
            forecast_period=f"{forecast_weeks} weeks",
            forecasted_demand=forecasted,
            demand_range=(forecasted - margin, forecasted + margin),
            trend=trend,
            seasonality_factor=seasonality_factor
        )


class AnomalyDetectionModel(BaseMLModel):
    """
    이상 탐지 모델

    Input: 실시간 센서/공정 데이터
    Output: 이상 여부, 이상 점수
    Algorithm: Isolation Forest / Autoencoder (시뮬레이션)
    """

    def __init__(self):
        super().__init__("anomaly_detect_v1", ModelType.ANOMALY_DETECTION)
        self.metrics = ModelMetrics(
            accuracy=0.94,
            precision=0.89,
            recall=0.86,
            f1_score=0.875,
            auc_roc=0.93
        )
        self.feature_importance = {
            "value_zscore": 0.30,
            "rate_of_change": 0.20,
            "deviation_from_pattern": 0.18,
            "correlation_break": 0.15,
            "historical_anomaly_freq": 0.10,
            "sensor_health": 0.07
        }

    def detect(self, data_points: list[dict]) -> list[dict]:
        """이상 탐지 수행"""
        import uuid

        results = []

        for point in data_points:
            metric_name = point.get("metric_name", "unknown")
            value = point.get("value", 0)
            historical_mean = point.get("historical_mean", value)
            historical_std = point.get("historical_std", abs(value * 0.1) or 1)

            # Z-score 계산
            z_score = abs(value - historical_mean) / historical_std if historical_std > 0 else 0

            # 이상 점수 계산 (0-1)
            anomaly_score = min(1.0, z_score / 4.0)

            # 이상 여부 판단
            is_anomaly = anomaly_score > 0.6

            # 변화율 계산
            previous_value = point.get("previous_value", value)
            rate_of_change = abs(value - previous_value) / (abs(previous_value) or 1)

            severity = "NORMAL"
            if anomaly_score > 0.8:
                severity = "CRITICAL"
            elif anomaly_score > 0.6:
                severity = "WARNING"
            elif anomaly_score > 0.4:
                severity = "INFO"

            results.append({
                "detection_id": f"AD-{uuid.uuid4().hex[:8].upper()}",
                "metric_name": metric_name,
                "value": value,
                "anomaly_score": anomaly_score,
                "is_anomaly": is_anomaly,
                "severity": severity,
                "z_score": z_score,
                "rate_of_change": rate_of_change,
                "expected_range": (
                    historical_mean - 2 * historical_std,
                    historical_mean + 2 * historical_std
                ),
                "timestamp": datetime.utcnow().isoformat(),
                "recommendation": self._get_recommendation(severity, metric_name)
            })

        return results

    def _get_recommendation(self, severity: str, metric_name: str) -> str:
        if severity == "CRITICAL":
            return f"{metric_name} 이상 감지 - 즉시 점검 필요"
        elif severity == "WARNING":
            return f"{metric_name} 주의 관찰 필요 - 모니터링 강화"
        elif severity == "INFO":
            return f"{metric_name} 경미한 변동 - 계속 관찰"
        return "정상 범위 내"
