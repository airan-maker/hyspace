"""
Yield Analyzer Service

수율 분석 및 근본 원인 분석 (RCA) 엔진
Palantir-grade Root Cause Analysis Engine
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from collections import Counter
import math
import random

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.yield_event import (
    WaferRecord, YieldEvent, Equipment,
    YieldEventStatus, RootCauseType,
)
from app.schemas.yield_schema import (
    RootCause, RCARequest, RCAResponse,
    YieldEventCreate, YieldEventResponse,
    YieldDashboardResponse, YieldTrendPoint,
    YieldByEquipment, YieldByProduct,
)


@dataclass
class CorrelationResult:
    """상관관계 분석 결과"""
    factor_type: str  # EQUIPMENT, MATERIAL, PROCESS, TIME
    factor_id: str
    correlation_strength: float  # 0-1
    affected_wafer_count: int
    total_wafer_count: int
    description: str


class YieldAnalyzer:
    """
    수율 분석 및 근본 원인 분석 엔진

    주요 기능:
    - 수율 저하 이벤트 탐지
    - 영향받은 웨이퍼들의 공통 요소 분석
    - 시간적/공간적 상관관계 분석
    - 근본 원인 순위화 및 추천
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== 수율 이벤트 관리 ====================

    def create_yield_event(
        self,
        event_data: YieldEventCreate,
        created_by: Optional[str] = None
    ) -> YieldEvent:
        """수율 이벤트 생성"""
        import uuid

        event = YieldEvent(
            event_id=f"YE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            title=event_data.title,
            description=event_data.description,
            severity=event_data.severity.value,
            status=YieldEventStatus.OPEN.value,
            yield_drop_percent=event_data.yield_drop_percent,
            affected_lot_ids=event_data.affected_lot_ids or [],
            detected_at=datetime.utcnow(),
            created_by=created_by,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # 영향받은 웨이퍼 연결
        if event_data.affected_wafer_ids:
            self._link_affected_wafers(event.id, event_data.affected_wafer_ids)

        return event

    def _link_affected_wafers(self, event_id: int, wafer_ids: list[str]):
        """수율 이벤트에 영향받은 웨이퍼 연결"""
        from app.models.yield_event import YieldEventWafer

        for wafer_id in wafer_ids:
            wafer = self.db.query(WaferRecord).filter(
                WaferRecord.wafer_id == wafer_id
            ).first()

            if wafer:
                link = YieldEventWafer(
                    yield_event_id=event_id,
                    wafer_record_id=wafer.id
                )
                self.db.add(link)

        self.db.commit()

    def get_yield_events(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> list[YieldEvent]:
        """수율 이벤트 목록 조회"""
        query = self.db.query(YieldEvent)

        if status:
            query = query.filter(YieldEvent.status == status)
        if severity:
            query = query.filter(YieldEvent.severity == severity)
        if start_date:
            query = query.filter(YieldEvent.detected_at >= start_date)
        if end_date:
            query = query.filter(YieldEvent.detected_at <= end_date)

        return query.order_by(YieldEvent.detected_at.desc()).limit(limit).all()

    # ==================== 근본 원인 분석 (RCA) ====================

    def analyze_root_cause(self, request: RCARequest) -> RCAResponse:
        """
        근본 원인 분석 실행

        분석 단계:
        1. 영향받은 웨이퍼들의 공통 요소 추출
        2. 시간적 상관관계 분석 (이벤트 발생 전후)
        3. 장비별 수율 편차 분석
        4. 공정 파라미터 이상치 탐지
        5. 원인 순위화 및 신뢰도 계산
        """
        import time
        start_time = time.time()

        # 이벤트 조회
        event = self.db.query(YieldEvent).filter(
            YieldEvent.event_id == request.event_id
        ).first()

        if not event:
            raise ValueError(f"Event not found: {request.event_id}")

        # 영향받은 웨이퍼 조회
        affected_wafers = self._get_affected_wafers(event.id)

        if not affected_wafers:
            # 데모 모드: 시뮬레이션 데이터 생성
            return self._generate_demo_rca_response(request, event, time.time() - start_time)

        # 1. 공통 요소 분석
        common_factors = self._find_common_factors(affected_wafers)

        # 2. 시간적 상관관계
        temporal_correlations = self._analyze_temporal_patterns(
            event.detected_at,
            lookback_hours=request.time_window_hours
        )

        # 3. 장비별 수율 편차
        equipment_variance = self._analyze_equipment_variance(affected_wafers)

        # 4. 공정 파라미터 이상치
        process_anomalies = self._detect_process_anomalies(affected_wafers)

        # 5. 원인 순위화
        all_correlations = (
            common_factors +
            temporal_correlations +
            equipment_variance +
            process_anomalies
        )

        root_causes = self._rank_causes(all_correlations, request.analysis_depth)

        # 6. 추천 조치 생성
        recommendations = self._generate_recommendations(root_causes)

        # 7. 유사 이벤트 검색
        similar_events = []
        if request.include_similar_events:
            similar_events = self._find_similar_events(event, root_causes)

        # 신뢰도 계산
        confidence = self._calculate_confidence(root_causes, len(affected_wafers))

        analysis_time = time.time() - start_time

        return RCAResponse(
            event_id=request.event_id,
            root_causes=root_causes,
            confidence_score=confidence,
            similar_events=similar_events,
            analysis_method="Multi-factor Correlation Analysis v1.0",
            recommendations=recommendations,
            analysis_time_seconds=round(analysis_time, 3)
        )

    def _get_affected_wafers(self, event_id: int) -> list[WaferRecord]:
        """이벤트에 연결된 웨이퍼 조회"""
        from app.models.yield_event import YieldEventWafer

        wafer_ids = self.db.query(YieldEventWafer.wafer_record_id).filter(
            YieldEventWafer.yield_event_id == event_id
        ).all()

        if not wafer_ids:
            return []

        return self.db.query(WaferRecord).filter(
            WaferRecord.id.in_([w[0] for w in wafer_ids])
        ).all()

    def _find_common_factors(self, wafers: list[WaferRecord]) -> list[CorrelationResult]:
        """영향받은 웨이퍼들의 공통 요소 분석"""
        results = []
        total = len(wafers)

        if total == 0:
            return results

        # 장비별 빈도
        equipment_counts = Counter(w.equipment_id for w in wafers if w.equipment_id)
        for equip_id, count in equipment_counts.most_common(3):
            if count / total >= 0.5:  # 50% 이상 공통
                results.append(CorrelationResult(
                    factor_type="EQUIPMENT",
                    factor_id=equip_id,
                    correlation_strength=count / total,
                    affected_wafer_count=count,
                    total_wafer_count=total,
                    description=f"장비 {equip_id}에서 {count}/{total} 웨이퍼 처리"
                ))

        # Lot별 빈도
        lot_counts = Counter(w.lot_id for w in wafers if w.lot_id)
        for lot_id, count in lot_counts.most_common(3):
            if count / total >= 0.3:  # 30% 이상 공통
                results.append(CorrelationResult(
                    factor_type="MATERIAL",
                    factor_id=lot_id,
                    correlation_strength=count / total,
                    affected_wafer_count=count,
                    total_wafer_count=total,
                    description=f"Lot {lot_id}에서 {count}/{total} 웨이퍼 발생"
                ))

        # Recipe별 빈도
        recipe_counts = Counter(w.recipe_id for w in wafers if w.recipe_id)
        for recipe_id, count in recipe_counts.most_common(3):
            if count / total >= 0.5:
                results.append(CorrelationResult(
                    factor_type="PROCESS",
                    factor_id=recipe_id,
                    correlation_strength=count / total,
                    affected_wafer_count=count,
                    total_wafer_count=total,
                    description=f"Recipe {recipe_id} 사용 웨이퍼 {count}/{total}"
                ))

        return results

    def _analyze_temporal_patterns(
        self,
        event_time: datetime,
        lookback_hours: int
    ) -> list[CorrelationResult]:
        """시간적 패턴 분석 - 이벤트 발생 전후 이상 징후"""
        results = []

        start_time = event_time - timedelta(hours=lookback_hours)

        # 해당 기간 동안의 장비 상태 변화 조회
        equipments = self.db.query(Equipment).filter(
            Equipment.last_maintenance.between(start_time, event_time)
        ).all()

        for equip in equipments:
            results.append(CorrelationResult(
                factor_type="EQUIPMENT",
                factor_id=equip.equipment_id,
                correlation_strength=0.7,
                affected_wafer_count=0,
                total_wafer_count=0,
                description=f"장비 {equip.equipment_id} 유지보수 후 ({equip.last_maintenance})"
            ))

        return results

    def _analyze_equipment_variance(
        self,
        affected_wafers: list[WaferRecord]
    ) -> list[CorrelationResult]:
        """장비별 수율 편차 분석"""
        results = []

        # 영향받은 웨이퍼의 장비 목록
        equipment_ids = set(w.equipment_id for w in affected_wafers if w.equipment_id)

        for equip_id in equipment_ids:
            # 해당 장비의 전체 웨이퍼 수율 조회
            all_yields = self.db.query(WaferRecord.yield_percent).filter(
                and_(
                    WaferRecord.equipment_id == equip_id,
                    WaferRecord.yield_percent.isnot(None)
                )
            ).all()

            if len(all_yields) >= 10:
                yields = [y[0] for y in all_yields]
                avg_yield = sum(yields) / len(yields)

                # 영향받은 웨이퍼의 수율
                affected_yields = [
                    w.yield_percent for w in affected_wafers
                    if w.equipment_id == equip_id and w.yield_percent
                ]

                if affected_yields:
                    affected_avg = sum(affected_yields) / len(affected_yields)
                    variance = abs(avg_yield - affected_avg)

                    if variance > 5:  # 5% 이상 편차
                        results.append(CorrelationResult(
                            factor_type="EQUIPMENT",
                            factor_id=equip_id,
                            correlation_strength=min(variance / 20, 1.0),
                            affected_wafer_count=len(affected_yields),
                            total_wafer_count=len(yields),
                            description=f"장비 {equip_id} 수율 편차: {variance:.1f}% (평균 {avg_yield:.1f}% → {affected_avg:.1f}%)"
                        ))

        return results

    def _detect_process_anomalies(
        self,
        affected_wafers: list[WaferRecord]
    ) -> list[CorrelationResult]:
        """공정 파라미터 이상치 탐지"""
        results = []

        for wafer in affected_wafers:
            if wafer.sensor_data:
                # 센서 데이터에서 이상치 탐지
                anomalies = self._check_sensor_anomalies(wafer.sensor_data)
                for anomaly in anomalies:
                    results.append(CorrelationResult(
                        factor_type="PROCESS",
                        factor_id=f"{wafer.wafer_id}:{anomaly['param']}",
                        correlation_strength=anomaly['severity'],
                        affected_wafer_count=1,
                        total_wafer_count=1,
                        description=anomaly['description']
                    ))

        return results

    def _check_sensor_anomalies(self, sensor_data: dict) -> list[dict]:
        """센서 데이터 이상치 확인"""
        anomalies = []

        # 정상 범위 정의 (예시)
        normal_ranges = {
            'temperature': (20, 30),
            'pressure': (0.9, 1.1),
            'flow_rate': (90, 110),
        }

        for param, (min_val, max_val) in normal_ranges.items():
            if param in sensor_data:
                value = sensor_data[param]
                if value < min_val or value > max_val:
                    severity = min(abs(value - (min_val + max_val) / 2) / 10, 1.0)
                    anomalies.append({
                        'param': param,
                        'value': value,
                        'severity': severity,
                        'description': f"{param} 이상: {value} (정상 범위: {min_val}-{max_val})"
                    })

        return anomalies

    def _rank_causes(
        self,
        correlations: list[CorrelationResult],
        depth: int
    ) -> list[RootCause]:
        """원인 순위화 및 RootCause 변환"""
        if not correlations:
            return []

        # 상관관계 강도로 정렬
        sorted_correlations = sorted(
            correlations,
            key=lambda x: x.correlation_strength,
            reverse=True
        )

        # 상위 N개 선택 및 변환
        root_causes = []
        for corr in sorted_correlations[:depth]:
            cause_type = self._map_factor_to_cause_type(corr.factor_type)

            root_causes.append(RootCause(
                cause_type=cause_type,
                entity_id=corr.factor_id,
                description=corr.description,
                probability=round(corr.correlation_strength * 100, 1),
                evidence=[
                    f"영향 웨이퍼: {corr.affected_wafer_count}/{corr.total_wafer_count}",
                    f"상관관계 강도: {corr.correlation_strength:.2f}"
                ]
            ))

        return root_causes

    def _map_factor_to_cause_type(self, factor_type: str) -> RootCauseType:
        """Factor 타입을 RootCauseType으로 매핑"""
        mapping = {
            "EQUIPMENT": RootCauseType.EQUIPMENT,
            "MATERIAL": RootCauseType.MATERIAL,
            "PROCESS": RootCauseType.PROCESS,
            "TIME": RootCauseType.ENVIRONMENT,
            "HUMAN": RootCauseType.HUMAN,
        }
        return mapping.get(factor_type, RootCauseType.UNKNOWN)

    def _generate_recommendations(self, root_causes: list[RootCause]) -> list[str]:
        """근본 원인 기반 추천 조치 생성"""
        recommendations = []

        for cause in root_causes:
            if cause.cause_type == RootCauseType.EQUIPMENT:
                recommendations.append(f"장비 {cause.entity_id} 점검 및 교정 권장")
                recommendations.append(f"장비 {cause.entity_id}의 PM(예방 정비) 일정 검토")
            elif cause.cause_type == RootCauseType.MATERIAL:
                recommendations.append(f"Lot {cause.entity_id} 원자재 품질 검사 실시")
                recommendations.append(f"해당 배치 추가 사용 보류 검토")
            elif cause.cause_type == RootCauseType.PROCESS:
                recommendations.append(f"공정 파라미터 재검토: {cause.entity_id}")
                recommendations.append("SPC(통계적 공정 관리) 한계 재설정 검토")
            elif cause.cause_type == RootCauseType.ENVIRONMENT:
                recommendations.append("클린룸 환경 파라미터 점검 (온도, 습도, 파티클)")

        # 공통 권장사항
        if root_causes:
            recommendations.append("영향받은 웨이퍼 샘플 정밀 분석 실시")
            recommendations.append("유사 이벤트 재발 방지를 위한 모니터링 강화")

        return list(set(recommendations))[:8]  # 중복 제거, 최대 8개

    def _find_similar_events(
        self,
        event: YieldEvent,
        root_causes: list[RootCause]
    ) -> list[str]:
        """유사 이벤트 검색"""
        similar_ids = []

        # 동일 심각도의 최근 이벤트
        similar_events = self.db.query(YieldEvent).filter(
            and_(
                YieldEvent.id != event.id,
                YieldEvent.severity == event.severity,
                YieldEvent.detected_at >= datetime.utcnow() - timedelta(days=90)
            )
        ).limit(5).all()

        similar_ids = [e.event_id for e in similar_events]

        return similar_ids

    def _calculate_confidence(
        self,
        root_causes: list[RootCause],
        wafer_count: int
    ) -> float:
        """분석 신뢰도 계산"""
        if not root_causes:
            return 0.0

        # 기본 신뢰도 (원인 수 기반)
        base_confidence = min(len(root_causes) * 15, 50)

        # 최상위 원인의 확률 반영
        top_cause_bonus = root_causes[0].probability * 0.3

        # 데이터 양 보너스
        data_bonus = min(wafer_count * 2, 20)

        return min(base_confidence + top_cause_bonus + data_bonus, 100)

    def _generate_demo_rca_response(
        self,
        request: RCARequest,
        event: YieldEvent,
        analysis_time: float
    ) -> RCAResponse:
        """데모용 RCA 결과 생성"""
        demo_causes = [
            RootCause(
                cause_type=RootCauseType.EQUIPMENT,
                entity_id="LITHO-03",
                description="노광장비 #3 렌즈 오염 의심 - 최근 PM 이후 수율 하락 패턴",
                probability=87.5,
                evidence=[
                    "PM 후 3일간 수율 5.2% 하락",
                    "동일 장비 처리 웨이퍼 92% 영향",
                    "결함 패턴: 중심부 집중 (렌즈 특성)"
                ]
            ),
            RootCause(
                cause_type=RootCauseType.MATERIAL,
                entity_id="PR-BATCH-2024-0156",
                description="포토레지스트 배치 품질 이상 가능성",
                probability=62.3,
                evidence=[
                    "해당 배치 사용 웨이퍼 수율 평균 3.8% 낮음",
                    "점도 스펙 상한 근접 (사용 가능 범위 내)"
                ]
            ),
            RootCause(
                cause_type=RootCauseType.PROCESS,
                entity_id="ETCH-RECIPE-V2.3",
                description="식각 레시피 파라미터 드리프트",
                probability=45.0,
                evidence=[
                    "RF Power 설정값 대비 실제 출력 2.1% 편차",
                    "Chamber 압력 미세 변동 감지"
                ]
            )
        ]

        return RCAResponse(
            event_id=request.event_id,
            root_causes=demo_causes[:request.analysis_depth],
            confidence_score=87.5,
            similar_events=["YE-20260115-A3F2", "YE-20260108-B7C1"],
            analysis_method="Multi-factor Correlation Analysis v1.0 (Demo Mode)",
            recommendations=[
                "노광장비 LITHO-03 렌즈 상태 즉시 점검",
                "PR 배치 PR-BATCH-2024-0156 추가 사용 보류",
                "식각 장비 RF Generator 교정 실시",
                "영향받은 웨이퍼 샘플 FA(Failure Analysis) 진행",
                "유사 패턴 모니터링 알람 설정"
            ],
            analysis_time_seconds=round(analysis_time, 3)
        )

    # ==================== 대시보드 데이터 ====================

    def get_dashboard_data(
        self,
        days: int = 30,
        product_id: Optional[str] = None
    ) -> YieldDashboardResponse:
        """수율 대시보드 데이터 조회"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 전체 수율 계산
        overall_yield = self._calculate_overall_yield(start_date, end_date, product_id)

        # 트렌드 데이터
        trend_data = self._get_yield_trend(start_date, end_date, product_id)

        # 장비별 수율
        by_equipment = self._get_yield_by_equipment(start_date, end_date)

        # 제품별 수율
        by_product = self._get_yield_by_product(start_date, end_date)

        # 이벤트 통계
        active_events = self.db.query(YieldEvent).filter(
            YieldEvent.status.in_([
                YieldEventStatus.OPEN.value,
                YieldEventStatus.INVESTIGATING.value
            ])
        ).count()

        critical_events = self.db.query(YieldEvent).filter(
            and_(
                YieldEvent.severity == "CRITICAL",
                YieldEvent.status != YieldEventStatus.CLOSED.value
            )
        ).count()

        week_ago = datetime.utcnow() - timedelta(days=7)
        events_this_week = self.db.query(YieldEvent).filter(
            YieldEvent.detected_at >= week_ago
        ).count()

        return YieldDashboardResponse(
            overall_yield=overall_yield,
            yield_target=92.0,  # 설정 가능
            yield_vs_target=overall_yield - 92.0,
            trend_data=trend_data,
            by_equipment=by_equipment,
            by_product=by_product,
            active_events=active_events,
            critical_events=critical_events,
            events_this_week=events_this_week,
            top_defect_types=self._get_top_defect_types(),
            recent_alerts=self._get_recent_alerts()
        )

    def _calculate_overall_yield(
        self,
        start_date: datetime,
        end_date: datetime,
        product_id: Optional[str]
    ) -> float:
        """전체 수율 계산"""
        query = self.db.query(func.avg(WaferRecord.yield_percent)).filter(
            and_(
                WaferRecord.created_at.between(start_date, end_date),
                WaferRecord.yield_percent.isnot(None)
            )
        )

        if product_id:
            query = query.filter(WaferRecord.product_id == product_id)

        result = query.scalar()
        return round(result, 2) if result else 90.5  # 데모 기본값

    def _get_yield_trend(
        self,
        start_date: datetime,
        end_date: datetime,
        product_id: Optional[str]
    ) -> list[YieldTrendPoint]:
        """일별 수율 트렌드"""
        # 실제 구현시 DB 집계 쿼리 사용
        # 데모용 샘플 데이터
        trend = []
        current = start_date
        base_yield = 91.0

        while current <= end_date:
            variation = random.uniform(-2, 2)
            trend.append(YieldTrendPoint(
                date=current,
                yield_percent=round(base_yield + variation, 2),
                wafer_count=random.randint(800, 1200)
            ))
            current += timedelta(days=1)

        return trend

    def _get_yield_by_equipment(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[YieldByEquipment]:
        """장비별 수율"""
        # 데모용 샘플 데이터
        equipments = [
            ("LITHO-01", "LITHOGRAPHY", 93.2, 2450, "STABLE"),
            ("LITHO-02", "LITHOGRAPHY", 91.8, 2380, "DOWN"),
            ("LITHO-03", "LITHOGRAPHY", 88.5, 2290, "DOWN"),
            ("ETCH-01", "ETCHER", 94.1, 3200, "UP"),
            ("ETCH-02", "ETCHER", 92.7, 3150, "STABLE"),
            ("CVD-01", "CVD", 95.3, 2800, "UP"),
            ("CVD-02", "CVD", 94.8, 2750, "STABLE"),
        ]

        return [
            YieldByEquipment(
                equipment_id=eid,
                equipment_type=etype,
                avg_yield=ayield,
                wafer_count=wcount,
                trend=trend
            )
            for eid, etype, ayield, wcount, trend in equipments
        ]

    def _get_yield_by_product(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[YieldByProduct]:
        """제품별 수율"""
        # 데모용 샘플 데이터
        products = [
            ("CHIP-A1", 92.5, 15000),
            ("CHIP-A2", 91.2, 12000),
            ("CHIP-B1", 93.8, 8000),
            ("CHIP-C1", 89.5, 5000),
        ]

        return [
            YieldByProduct(
                product_id=pid,
                avg_yield=ayield,
                wafer_count=wcount
            )
            for pid, ayield, wcount in products
        ]

    def _get_top_defect_types(self) -> list[dict]:
        """주요 결함 유형"""
        return [
            {"type": "Particle", "count": 245, "percent": 32.5},
            {"type": "Pattern Defect", "count": 189, "percent": 25.1},
            {"type": "Scratch", "count": 156, "percent": 20.7},
            {"type": "Film Defect", "count": 98, "percent": 13.0},
            {"type": "Other", "count": 66, "percent": 8.7},
        ]

    def _get_recent_alerts(self) -> list[dict]:
        """최근 알림"""
        return [
            {
                "time": "2시간 전",
                "message": "LITHO-03 수율 급락 감지 (88.5%)",
                "severity": "HIGH"
            },
            {
                "time": "6시간 전",
                "message": "Lot L2024-0892 품질 이상 의심",
                "severity": "MEDIUM"
            },
            {
                "time": "1일 전",
                "message": "CVD-01 PM 완료 - 정상 가동",
                "severity": "INFO"
            },
        ]
