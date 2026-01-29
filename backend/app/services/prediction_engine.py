"""
Prediction Engine

예측 분석 통합 엔진 - 모든 ML 모델 관리 및 예측 수행
"""

from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass, field
import uuid
import random

from sqlalchemy.orm import Session

from .ml_models import (
    YieldPredictionModel,
    EquipmentFailureModel,
    DemandForecastModel,
    AnomalyDetectionModel,
    ModelType,
    ModelStatus,
    PredictionResult,
    YieldPrediction,
    FailurePrediction,
    DemandForecast
)


@dataclass
class ModelInfo:
    """모델 정보"""
    model_id: str
    model_type: str
    version: str
    status: str
    last_trained: datetime
    accuracy: Optional[float]
    feature_count: int
    prediction_count: int = 0


@dataclass
class PredictionHistory:
    """예측 이력"""
    prediction_id: str
    model_type: str
    timestamp: datetime
    input_summary: dict
    predicted_value: Any
    confidence: float
    actual_value: Optional[Any] = None
    error: Optional[float] = None


class PredictionEngine:
    """
    예측 분석 통합 엔진

    - 수율 예측
    - 장비 고장 예측
    - 수요 예측
    - 이상 탐지
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

        # 모델 초기화
        self.yield_model = YieldPredictionModel()
        self.failure_model = EquipmentFailureModel()
        self.demand_model = DemandForecastModel()
        self.anomaly_model = AnomalyDetectionModel()

        # 예측 이력
        self._prediction_history: list[PredictionHistory] = []

    def get_models_status(self) -> list[ModelInfo]:
        """모든 모델 상태 조회"""
        models = [
            self.yield_model,
            self.failure_model,
            self.demand_model,
            self.anomaly_model
        ]

        return [
            ModelInfo(
                model_id=m.model_id,
                model_type=m.model_type.value,
                version=m.version,
                status=m.status.value,
                last_trained=m.last_trained,
                accuracy=m.metrics.accuracy,
                feature_count=len(m.feature_importance),
                prediction_count=random.randint(100, 5000)
            )
            for m in models
        ]

    def get_model_details(self, model_type: str) -> dict:
        """특정 모델 상세 정보"""
        model_map = {
            ModelType.YIELD_PREDICTION.value: self.yield_model,
            ModelType.EQUIPMENT_FAILURE.value: self.failure_model,
            ModelType.DEMAND_FORECAST.value: self.demand_model,
            ModelType.ANOMALY_DETECTION.value: self.anomaly_model
        }

        model = model_map.get(model_type)
        if not model:
            raise ValueError(f"Unknown model type: {model_type}")

        return {
            "model_id": model.model_id,
            "model_type": model.model_type.value,
            "version": model.version,
            "status": model.status.value,
            "last_trained": model.last_trained.isoformat(),
            "metrics": {
                "accuracy": model.metrics.accuracy,
                "precision": model.metrics.precision,
                "recall": model.metrics.recall,
                "f1_score": model.metrics.f1_score,
                "mae": model.metrics.mae,
                "rmse": model.metrics.rmse,
                "mape": model.metrics.mape,
                "r2_score": model.metrics.r2_score,
                "auc_roc": model.metrics.auc_roc
            },
            "feature_importance": model.feature_importance,
            "description": self._get_model_description(model.model_type)
        }

    def _get_model_description(self, model_type: ModelType) -> dict:
        descriptions = {
            ModelType.YIELD_PREDICTION: {
                "name": "수율 예측 모델",
                "purpose": "공정 파라미터 기반 수율 예측",
                "algorithm": "XGBoost / LightGBM",
                "input_features": ["온도", "압력", "유량", "습도", "장비 OEE", "공정 시간"],
                "output": "예상 수율 (%)",
                "use_cases": ["수율 저하 조기 경보", "공정 파라미터 최적화", "품질 예측"]
            },
            ModelType.EQUIPMENT_FAILURE: {
                "name": "장비 고장 예측 모델",
                "purpose": "센서 데이터 기반 장비 고장 예측",
                "algorithm": "LSTM / Prophet",
                "input_features": ["진동", "운영 시간", "온도 변화", "유지보수 지연일", "오류 빈도"],
                "output": "고장 확률, 예상 시점, RUL",
                "use_cases": ["예방 정비 스케줄링", "다운타임 최소화", "부품 재고 최적화"]
            },
            ModelType.DEMAND_FORECAST: {
                "name": "수요 예측 모델",
                "purpose": "과거 데이터 기반 미래 수요 예측",
                "algorithm": "ARIMA / Prophet",
                "input_features": ["과거 수요", "계절성", "시장 성장률", "주문 파이프라인"],
                "output": "예상 수요량, 트렌드",
                "use_cases": ["생산 계획", "재고 관리", "용량 계획"]
            },
            ModelType.ANOMALY_DETECTION: {
                "name": "이상 탐지 모델",
                "purpose": "실시간 데이터 이상 감지",
                "algorithm": "Isolation Forest / Autoencoder",
                "input_features": ["실시간 센서 값", "변화율", "패턴 편차"],
                "output": "이상 점수, 심각도",
                "use_cases": ["품질 이상 조기 감지", "장비 이상 경보", "공정 모니터링"]
            }
        }
        return descriptions.get(model_type, {})

    # ==================== 수율 예측 ====================

    def predict_yield(
        self,
        process_params: dict,
        equipment_status: Optional[dict] = None,
        environment_data: Optional[dict] = None
    ) -> YieldPrediction:
        """수율 예측"""
        features = {**process_params}

        if equipment_status:
            features.update(equipment_status)
        if environment_data:
            features.update(environment_data)

        prediction = self.yield_model.predict(features)

        self._record_prediction(prediction)

        return prediction

    def batch_predict_yield(self, batch_inputs: list[dict]) -> list[YieldPrediction]:
        """배치 수율 예측"""
        return [self.predict_yield(**inputs) for inputs in batch_inputs]

    # ==================== 장비 고장 예측 ====================

    def predict_equipment_failure(
        self,
        equipment_id: str,
        sensor_data: dict,
        maintenance_history: Optional[dict] = None
    ) -> FailurePrediction:
        """장비 고장 예측"""
        features = {
            "equipment_id": equipment_id,
            **sensor_data
        }

        if maintenance_history:
            features.update(maintenance_history)

        prediction = self.failure_model.predict(features)

        self._record_prediction(prediction)

        return prediction

    def predict_fleet_failures(
        self,
        equipment_list: list[dict]
    ) -> list[FailurePrediction]:
        """전체 장비 고장 예측"""
        predictions = []

        for eq in equipment_list:
            pred = self.predict_equipment_failure(
                equipment_id=eq.get("equipment_id", ""),
                sensor_data=eq.get("sensor_data", {}),
                maintenance_history=eq.get("maintenance_history")
            )
            predictions.append(pred)

        # 위험도순 정렬
        predictions.sort(key=lambda x: x.failure_probability, reverse=True)

        return predictions

    # ==================== 수요 예측 ====================

    def forecast_demand(
        self,
        product_category: str,
        forecast_weeks: int = 4,
        market_data: Optional[dict] = None
    ) -> DemandForecast:
        """수요 예측"""
        features = {
            "product_category": product_category,
            "forecast_weeks": forecast_weeks,
            "historical_demand_4w": random.uniform(8000, 15000),  # 시뮬레이션
            "market_growth_rate": random.uniform(-0.02, 0.05),
            "customer_orders_pipeline": random.uniform(500, 2000),
            "economic_indicator": random.uniform(95, 105)
        }

        if market_data:
            features.update(market_data)

        prediction = self.demand_model.predict(features)

        self._record_prediction(prediction)

        return prediction

    def forecast_demand_multi_period(
        self,
        product_category: str,
        periods: list[int]
    ) -> list[DemandForecast]:
        """다중 기간 수요 예측"""
        return [
            self.forecast_demand(product_category, weeks)
            for weeks in periods
        ]

    # ==================== 이상 탐지 ====================

    def detect_anomalies(self, data_points: list[dict]) -> list[dict]:
        """이상 탐지"""
        return self.anomaly_model.detect(data_points)

    def detect_realtime_anomaly(
        self,
        metric_name: str,
        current_value: float,
        historical_stats: Optional[dict] = None
    ) -> dict:
        """실시간 단일 메트릭 이상 탐지"""
        if historical_stats is None:
            # 기본 통계값 시뮬레이션
            historical_stats = {
                "historical_mean": current_value * random.uniform(0.95, 1.05),
                "historical_std": abs(current_value) * random.uniform(0.05, 0.15),
                "previous_value": current_value * random.uniform(0.97, 1.03)
            }

        data_point = {
            "metric_name": metric_name,
            "value": current_value,
            **historical_stats
        }

        results = self.anomaly_model.detect([data_point])
        return results[0] if results else {}

    # ==================== 통합 예측 ====================

    def get_production_insights(self) -> dict:
        """
        통합 생산 인사이트

        수율, 장비, 수요 예측을 종합한 분석
        """
        # 샘플 수율 예측
        yield_pred = self.predict_yield(
            process_params={
                "temperature": 23.0 + random.uniform(-2, 2),
                "pressure": 1.0 + random.uniform(-0.1, 0.1),
                "flow_rate": 100 + random.uniform(-5, 5)
            },
            equipment_status={"equipment_oee": 85 + random.uniform(-5, 5)},
            environment_data={"humidity": 45 + random.uniform(-5, 5)}
        )

        # 샘플 장비 예측 (주요 장비 3대)
        equipment_predictions = self.predict_fleet_failures([
            {
                "equipment_id": f"EQ-LITHO-{i}",
                "sensor_data": {
                    "vibration_level": 0.4 + random.uniform(0, 0.4),
                    "operating_hours": 5000 + random.randint(0, 3000),
                    "error_count_7d": random.randint(0, 8)
                },
                "maintenance_history": {
                    "maintenance_overdue_days": random.randint(0, 14)
                }
            }
            for i in range(1, 4)
        ])

        # 수요 예측
        demand_pred = self.forecast_demand("SEMICONDUCTOR", forecast_weeks=4)

        # 위험 장비 식별
        high_risk_equipment = [
            p for p in equipment_predictions if p.failure_probability > 0.3
        ]

        # 종합 점수 계산
        overall_health = 100
        if yield_pred.predicted_yield < 90:
            overall_health -= (90 - yield_pred.predicted_yield) * 2
        for eq in equipment_predictions:
            if eq.failure_probability > 0.3:
                overall_health -= 10
        overall_health = max(0, min(100, overall_health))

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health_score": round(overall_health, 1),
            "yield_outlook": {
                "predicted_yield": round(yield_pred.predicted_yield, 2),
                "confidence": round(yield_pred.confidence, 2),
                "risk_factors_count": len(yield_pred.risk_factors),
                "trend": "STABLE" if yield_pred.predicted_yield > 88 else "ATTENTION"
            },
            "equipment_health": {
                "total_monitored": len(equipment_predictions),
                "high_risk_count": len(high_risk_equipment),
                "highest_risk": {
                    "equipment_id": equipment_predictions[0].equipment_id,
                    "failure_probability": round(equipment_predictions[0].failure_probability, 2),
                    "recommendation": equipment_predictions[0].maintenance_recommendation
                } if equipment_predictions else None
            },
            "demand_forecast": {
                "period": demand_pred.forecast_period,
                "forecasted_demand": round(demand_pred.forecasted_demand, 0),
                "trend": demand_pred.trend,
                "confidence": round(demand_pred.confidence, 2)
            },
            "action_items": self._generate_action_items(
                yield_pred, equipment_predictions, demand_pred
            )
        }

    def _generate_action_items(
        self,
        yield_pred: YieldPrediction,
        equipment_preds: list[FailurePrediction],
        demand_pred: DemandForecast
    ) -> list[dict]:
        """조치 항목 생성"""
        items = []

        # 수율 관련
        if yield_pred.predicted_yield < 90:
            items.append({
                "priority": "HIGH",
                "category": "YIELD",
                "action": "수율 저하 예상 - 공정 파라미터 검토 필요",
                "details": yield_pred.optimization_suggestions[:2]
            })

        # 장비 관련
        for eq_pred in equipment_preds:
            if eq_pred.failure_probability > 0.5:
                items.append({
                    "priority": "CRITICAL",
                    "category": "EQUIPMENT",
                    "action": f"{eq_pred.equipment_id} 고장 위험 높음",
                    "details": [eq_pred.maintenance_recommendation]
                })
            elif eq_pred.failure_probability > 0.3:
                items.append({
                    "priority": "HIGH",
                    "category": "EQUIPMENT",
                    "action": f"{eq_pred.equipment_id} 점검 권장",
                    "details": [eq_pred.maintenance_recommendation]
                })

        # 수요 관련
        if demand_pred.trend == "INCREASING" and demand_pred.seasonality_factor > 1.1:
            items.append({
                "priority": "MEDIUM",
                "category": "DEMAND",
                "action": "수요 증가 예상 - 생산 역량 점검",
                "details": [f"예상 수요: {round(demand_pred.forecasted_demand, 0)} units"]
            })

        # 우선순위순 정렬
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        items.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return items[:5]  # 상위 5개

    def _record_prediction(self, prediction: PredictionResult):
        """예측 이력 기록"""
        history = PredictionHistory(
            prediction_id=prediction.prediction_id,
            model_type=prediction.model_type.value,
            timestamp=prediction.timestamp,
            input_summary={"features_count": len(prediction.input_features)},
            predicted_value=prediction.predicted_value,
            confidence=prediction.confidence
        )
        self._prediction_history.append(history)

        # 최근 1000개만 유지
        if len(self._prediction_history) > 1000:
            self._prediction_history = self._prediction_history[-1000:]

    def get_prediction_history(
        self,
        model_type: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """예측 이력 조회"""
        history = self._prediction_history

        if model_type:
            history = [h for h in history if h.model_type == model_type]

        history = sorted(history, key=lambda x: x.timestamp, reverse=True)[:limit]

        return [
            {
                "prediction_id": h.prediction_id,
                "model_type": h.model_type,
                "timestamp": h.timestamp.isoformat(),
                "predicted_value": h.predicted_value,
                "confidence": h.confidence
            }
            for h in history
        ]
