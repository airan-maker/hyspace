"""
Prediction API Endpoints

예측 분석 API - 수율/장비/수요 예측
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.prediction_engine import PredictionEngine
from app.services.audit_logger import AuditLogger


router = APIRouter(prefix="/predictions", tags=["Predictive Analytics"])


# ==================== Schemas ====================

class YieldPredictionRequest(BaseModel):
    temperature: float = Field(23.0, description="공정 온도 (°C)")
    pressure: float = Field(1.0, description="공정 압력 (bar)")
    flow_rate: float = Field(100.0, description="유량 (sccm)")
    humidity: Optional[float] = Field(45.0, description="습도 (%)")
    equipment_oee: Optional[float] = Field(85.0, description="장비 OEE (%)")
    process_time: Optional[float] = Field(None, description="공정 시간 (min)")
    wafer_position: Optional[int] = Field(None, description="웨이퍼 위치")


class YieldPredictionResponse(BaseModel):
    prediction_id: str
    predicted_yield: float
    confidence: float
    yield_range: tuple[float, float]
    risk_factors: list[dict]
    optimization_suggestions: list[str]
    contributing_factors: list[dict]
    timestamp: datetime


class EquipmentFailureRequest(BaseModel):
    equipment_id: str
    vibration_level: float = Field(0.5, description="진동 수준 (0-1)")
    operating_hours: int = Field(1000, description="운영 시간")
    temperature_delta: Optional[float] = Field(None, description="온도 변화")
    maintenance_overdue_days: int = Field(0, description="유지보수 지연일")
    error_count_7d: int = Field(0, description="최근 7일 오류 수")
    power_consumption_delta: Optional[float] = Field(None, description="전력 소비 변화율")


class EquipmentFailureResponse(BaseModel):
    prediction_id: str
    equipment_id: str
    failure_probability: float
    estimated_failure_time: Optional[datetime]
    remaining_useful_life_hours: Optional[float]
    maintenance_recommendation: str
    failure_mode: Optional[str]
    confidence: float
    contributing_factors: list[dict]
    warnings: list[str]
    timestamp: datetime


class DemandForecastRequest(BaseModel):
    product_category: str = Field(..., description="제품 카테고리")
    forecast_weeks: int = Field(4, ge=1, le=52, description="예측 기간 (주)")
    historical_demand_4w: Optional[float] = Field(None, description="최근 4주 수요")
    market_growth_rate: Optional[float] = Field(None, description="시장 성장률")
    customer_orders_pipeline: Optional[float] = Field(None, description="주문 파이프라인")
    economic_indicator: Optional[float] = Field(None, description="경제 지표")


class DemandForecastResponse(BaseModel):
    prediction_id: str
    forecast_period: str
    forecasted_demand: float
    demand_range: tuple[float, float]
    trend: str
    seasonality_factor: float
    confidence: float
    contributing_factors: list[dict]
    warnings: list[str]
    timestamp: datetime


class AnomalyDetectionRequest(BaseModel):
    metric_name: str
    value: float
    historical_mean: Optional[float] = None
    historical_std: Optional[float] = None
    previous_value: Optional[float] = None


class AnomalyDetectionResponse(BaseModel):
    detection_id: str
    metric_name: str
    value: float
    anomaly_score: float
    is_anomaly: bool
    severity: str
    z_score: float
    expected_range: tuple[float, float]
    recommendation: str
    timestamp: str


class BatchAnomalyRequest(BaseModel):
    data_points: list[AnomalyDetectionRequest]


class ModelStatusResponse(BaseModel):
    model_id: str
    model_type: str
    version: str
    status: str
    last_trained: datetime
    accuracy: Optional[float]
    feature_count: int
    prediction_count: int


# ==================== Models Status ====================

@router.get("/models", response_model=list[ModelStatusResponse])
def get_models_status(db: Session = Depends(get_db)):
    """모든 ML 모델 상태 조회"""
    engine = PredictionEngine(db)
    return engine.get_models_status()


@router.get("/models/{model_type}")
def get_model_details(
    model_type: str,
    db: Session = Depends(get_db)
):
    """특정 모델 상세 정보"""
    engine = PredictionEngine(db)
    try:
        return engine.get_model_details(model_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== Yield Prediction ====================

@router.post("/yield", response_model=YieldPredictionResponse)
def predict_yield(
    request: YieldPredictionRequest,
    db: Session = Depends(get_db)
):
    """수율 예측"""
    engine = PredictionEngine(db)

    process_params = {
        "temperature": request.temperature,
        "pressure": request.pressure,
        "flow_rate": request.flow_rate
    }

    equipment_status = {}
    if request.equipment_oee:
        equipment_status["equipment_oee"] = request.equipment_oee

    environment_data = {}
    if request.humidity:
        environment_data["humidity"] = request.humidity

    prediction = engine.predict_yield(
        process_params=process_params,
        equipment_status=equipment_status if equipment_status else None,
        environment_data=environment_data if environment_data else None
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="PREDICT",
        resource="yield_prediction",
        resource_id=prediction.prediction_id,
        details={"predicted_yield": prediction.predicted_yield}
    )

    return YieldPredictionResponse(
        prediction_id=prediction.prediction_id,
        predicted_yield=prediction.predicted_yield,
        confidence=prediction.confidence,
        yield_range=prediction.yield_range,
        risk_factors=prediction.risk_factors,
        optimization_suggestions=prediction.optimization_suggestions,
        contributing_factors=prediction.contributing_factors,
        timestamp=prediction.timestamp
    )


@router.post("/yield/batch")
def batch_predict_yield(
    requests: list[YieldPredictionRequest],
    db: Session = Depends(get_db)
):
    """배치 수율 예측"""
    engine = PredictionEngine(db)

    batch_inputs = [
        {
            "process_params": {
                "temperature": r.temperature,
                "pressure": r.pressure,
                "flow_rate": r.flow_rate
            },
            "equipment_status": {"equipment_oee": r.equipment_oee} if r.equipment_oee else None,
            "environment_data": {"humidity": r.humidity} if r.humidity else None
        }
        for r in requests
    ]

    predictions = engine.batch_predict_yield(batch_inputs)

    return {
        "count": len(predictions),
        "predictions": [
            {
                "prediction_id": p.prediction_id,
                "predicted_yield": p.predicted_yield,
                "confidence": p.confidence
            }
            for p in predictions
        ]
    }


# ==================== Equipment Failure Prediction ====================

@router.post("/equipment-failure", response_model=EquipmentFailureResponse)
def predict_equipment_failure(
    request: EquipmentFailureRequest,
    db: Session = Depends(get_db)
):
    """장비 고장 예측"""
    engine = PredictionEngine(db)

    sensor_data = {
        "vibration_level": request.vibration_level,
        "operating_hours": request.operating_hours,
        "error_count_7d": request.error_count_7d
    }

    if request.temperature_delta:
        sensor_data["temperature_delta"] = request.temperature_delta
    if request.power_consumption_delta:
        sensor_data["power_consumption_delta"] = request.power_consumption_delta

    maintenance_history = {
        "maintenance_overdue_days": request.maintenance_overdue_days
    }

    prediction = engine.predict_equipment_failure(
        equipment_id=request.equipment_id,
        sensor_data=sensor_data,
        maintenance_history=maintenance_history
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="PREDICT",
        resource="equipment_failure",
        resource_id=prediction.prediction_id,
        details={
            "equipment_id": prediction.equipment_id,
            "failure_probability": prediction.failure_probability
        }
    )

    return EquipmentFailureResponse(
        prediction_id=prediction.prediction_id,
        equipment_id=prediction.equipment_id,
        failure_probability=prediction.failure_probability,
        estimated_failure_time=prediction.estimated_failure_time,
        remaining_useful_life_hours=prediction.remaining_useful_life_hours,
        maintenance_recommendation=prediction.maintenance_recommendation,
        failure_mode=prediction.failure_mode,
        confidence=prediction.confidence,
        contributing_factors=prediction.contributing_factors,
        warnings=prediction.warnings,
        timestamp=prediction.timestamp
    )


@router.post("/equipment-failure/fleet")
def predict_fleet_failures(
    equipment_list: list[EquipmentFailureRequest],
    db: Session = Depends(get_db)
):
    """전체 장비 고장 예측"""
    engine = PredictionEngine(db)

    fleet_data = [
        {
            "equipment_id": eq.equipment_id,
            "sensor_data": {
                "vibration_level": eq.vibration_level,
                "operating_hours": eq.operating_hours,
                "error_count_7d": eq.error_count_7d
            },
            "maintenance_history": {
                "maintenance_overdue_days": eq.maintenance_overdue_days
            }
        }
        for eq in equipment_list
    ]

    predictions = engine.predict_fleet_failures(fleet_data)

    return {
        "count": len(predictions),
        "high_risk_count": sum(1 for p in predictions if p.failure_probability > 0.3),
        "predictions": [
            {
                "equipment_id": p.equipment_id,
                "failure_probability": p.failure_probability,
                "remaining_useful_life_hours": p.remaining_useful_life_hours,
                "maintenance_recommendation": p.maintenance_recommendation,
                "failure_mode": p.failure_mode
            }
            for p in predictions
        ]
    }


# ==================== Demand Forecast ====================

@router.post("/demand", response_model=DemandForecastResponse)
def forecast_demand(
    request: DemandForecastRequest,
    db: Session = Depends(get_db)
):
    """수요 예측"""
    engine = PredictionEngine(db)

    market_data = {}
    if request.historical_demand_4w:
        market_data["historical_demand_4w"] = request.historical_demand_4w
    if request.market_growth_rate:
        market_data["market_growth_rate"] = request.market_growth_rate
    if request.customer_orders_pipeline:
        market_data["customer_orders_pipeline"] = request.customer_orders_pipeline
    if request.economic_indicator:
        market_data["economic_indicator"] = request.economic_indicator

    prediction = engine.forecast_demand(
        product_category=request.product_category,
        forecast_weeks=request.forecast_weeks,
        market_data=market_data if market_data else None
    )

    return DemandForecastResponse(
        prediction_id=prediction.prediction_id,
        forecast_period=prediction.forecast_period,
        forecasted_demand=prediction.forecasted_demand,
        demand_range=prediction.demand_range,
        trend=prediction.trend,
        seasonality_factor=prediction.seasonality_factor,
        confidence=prediction.confidence,
        contributing_factors=prediction.contributing_factors,
        warnings=prediction.warnings,
        timestamp=prediction.timestamp
    )


@router.post("/demand/multi-period")
def forecast_demand_multi_period(
    product_category: str,
    periods: list[int] = Query(default=[1, 4, 12, 26]),
    db: Session = Depends(get_db)
):
    """다중 기간 수요 예측"""
    engine = PredictionEngine(db)

    forecasts = engine.forecast_demand_multi_period(product_category, periods)

    return {
        "product_category": product_category,
        "forecasts": [
            {
                "period_weeks": f.forecast_period,
                "forecasted_demand": f.forecasted_demand,
                "trend": f.trend,
                "confidence": f.confidence
            }
            for f in forecasts
        ]
    }


# ==================== Anomaly Detection ====================

@router.post("/anomaly", response_model=AnomalyDetectionResponse)
def detect_anomaly(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_db)
):
    """단일 메트릭 이상 탐지"""
    engine = PredictionEngine(db)

    historical_stats = {}
    if request.historical_mean is not None:
        historical_stats["historical_mean"] = request.historical_mean
    if request.historical_std is not None:
        historical_stats["historical_std"] = request.historical_std
    if request.previous_value is not None:
        historical_stats["previous_value"] = request.previous_value

    result = engine.detect_realtime_anomaly(
        metric_name=request.metric_name,
        current_value=request.value,
        historical_stats=historical_stats if historical_stats else None
    )

    return AnomalyDetectionResponse(**result)


@router.post("/anomaly/batch")
def detect_anomalies_batch(
    request: BatchAnomalyRequest,
    db: Session = Depends(get_db)
):
    """배치 이상 탐지"""
    engine = PredictionEngine(db)

    data_points = [
        {
            "metric_name": dp.metric_name,
            "value": dp.value,
            "historical_mean": dp.historical_mean,
            "historical_std": dp.historical_std,
            "previous_value": dp.previous_value
        }
        for dp in request.data_points
    ]

    results = engine.detect_anomalies(data_points)

    anomaly_count = sum(1 for r in results if r["is_anomaly"])

    return {
        "total_checked": len(results),
        "anomaly_count": anomaly_count,
        "results": results
    }


# ==================== Integrated Insights ====================

@router.get("/insights")
def get_production_insights(db: Session = Depends(get_db)):
    """
    통합 생산 인사이트

    수율, 장비, 수요 예측을 종합한 실시간 분석
    """
    engine = PredictionEngine(db)
    return engine.get_production_insights()


@router.get("/history")
def get_prediction_history(
    model_type: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """예측 이력 조회"""
    engine = PredictionEngine(db)
    return engine.get_prediction_history(model_type=model_type, limit=limit)


# ==================== Demo ====================

@router.post("/demo/run-all")
def run_demo_predictions(db: Session = Depends(get_db)):
    """
    데모: 모든 예측 모델 실행

    테스트용 샘플 데이터로 예측 수행
    """
    import random

    engine = PredictionEngine(db)

    # 수율 예측
    yield_pred = engine.predict_yield(
        process_params={
            "temperature": 23.0 + random.uniform(-3, 3),
            "pressure": 1.0 + random.uniform(-0.2, 0.2),
            "flow_rate": 100 + random.uniform(-10, 10)
        },
        equipment_status={"equipment_oee": 80 + random.uniform(0, 15)},
        environment_data={"humidity": 45 + random.uniform(-10, 10)}
    )

    # 장비 고장 예측
    failure_pred = engine.predict_equipment_failure(
        equipment_id="EQ-DEMO-001",
        sensor_data={
            "vibration_level": 0.5 + random.uniform(0, 0.4),
            "operating_hours": 3000 + random.randint(0, 2000),
            "error_count_7d": random.randint(0, 10)
        },
        maintenance_history={
            "maintenance_overdue_days": random.randint(0, 14)
        }
    )

    # 수요 예측
    demand_pred = engine.forecast_demand(
        product_category="SEMICONDUCTOR",
        forecast_weeks=4
    )

    # 이상 탐지
    anomaly_result = engine.detect_realtime_anomaly(
        metric_name="temperature",
        current_value=25.0 + random.uniform(-5, 5)
    )

    return {
        "demo_timestamp": datetime.utcnow().isoformat(),
        "yield_prediction": {
            "predicted_yield": yield_pred.predicted_yield,
            "confidence": yield_pred.confidence,
            "risk_factors_count": len(yield_pred.risk_factors)
        },
        "failure_prediction": {
            "equipment_id": failure_pred.equipment_id,
            "failure_probability": failure_pred.failure_probability,
            "recommendation": failure_pred.maintenance_recommendation
        },
        "demand_forecast": {
            "forecasted_demand": demand_pred.forecasted_demand,
            "trend": demand_pred.trend
        },
        "anomaly_detection": {
            "metric": anomaly_result.get("metric_name"),
            "is_anomaly": anomaly_result.get("is_anomaly"),
            "severity": anomaly_result.get("severity")
        }
    }
