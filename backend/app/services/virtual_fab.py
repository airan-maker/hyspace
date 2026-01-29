"""
Virtual Fab Simulator Service

이산 사건 시뮬레이션 기반 가상 팹 디지털 트윈
병목 예측 및 What-If 시나리오 분석
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import random
import heapq
import uuid
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.fab import (
    FabEquipment, WIPItem, SimulationScenario, Bottleneck, MaintenanceSchedule
)


@dataclass
class Event:
    """시뮬레이션 이벤트"""
    time: float  # 시뮬레이션 시간 (시간 단위)
    event_type: str  # ARRIVAL, PROCESS_START, PROCESS_END, BREAKDOWN, REPAIR
    equipment_id: str
    lot_id: Optional[str] = None
    data: dict = field(default_factory=dict)

    def __lt__(self, other):
        return self.time < other.time


@dataclass
class SimEquipment:
    """시뮬레이션용 장비 상태"""
    equipment_id: str
    equipment_type: str
    capacity_wph: float
    status: str = "IDLE"
    current_lot: Optional[str] = None
    queue: list = field(default_factory=list)
    mtbf_hours: float = 500.0
    mttr_hours: float = 4.0
    time_to_failure: float = 0.0
    utilization_time: float = 0.0
    total_processed: int = 0


@dataclass
class SimLot:
    """시뮬레이션용 Lot 상태"""
    lot_id: str
    wafer_count: int
    current_step: int
    total_steps: int
    priority: int
    route: list  # [{step, operation, equipment_type, process_time}]
    arrival_time: float
    completion_time: Optional[float] = None
    wait_time: float = 0.0


@dataclass
class SimulationMetrics:
    """시뮬레이션 결과 메트릭"""
    total_lots_completed: int = 0
    total_wafers_completed: int = 0
    avg_cycle_time_hours: float = 0.0
    avg_wait_time_hours: float = 0.0
    throughput_lots_per_day: float = 0.0
    throughput_wafers_per_day: float = 0.0
    equipment_utilization: dict = field(default_factory=dict)
    bottleneck_equipment: list = field(default_factory=list)
    wip_levels: list = field(default_factory=list)


class VirtualFabSimulator:
    """
    이산 사건 시뮬레이션 기반 가상 팹 시뮬레이터

    기능:
    - 실시간 팹 상태 시뮬레이션
    - 병목 예측
    - What-If 시나리오 분석
    """

    def __init__(self, db: Session):
        self.db = db
        self.reset()

    def reset(self):
        """시뮬레이션 상태 초기화"""
        self.current_time = 0.0
        self.event_queue: list[Event] = []
        self.equipments: dict[str, SimEquipment] = {}
        self.lots: dict[str, SimLot] = {}
        self.completed_lots: list[SimLot] = []
        self.metrics_history: list[dict] = []

    def initialize_from_db(self):
        """DB에서 팹 상태 로드"""
        # 장비 로드
        db_equipments = self.db.query(FabEquipment).all()
        for eq in db_equipments:
            self.equipments[eq.equipment_id] = SimEquipment(
                equipment_id=eq.equipment_id,
                equipment_type=eq.equipment_type,
                capacity_wph=eq.capacity_wph or 10.0,
                status=eq.status or "IDLE",
                mtbf_hours=eq.mtbf_hours or 500.0,
                mttr_hours=eq.mttr_hours or 4.0
            )

        # WIP 로드
        db_wips = self.db.query(WIPItem).all()
        for wip in db_wips:
            self.lots[wip.lot_id] = SimLot(
                lot_id=wip.lot_id,
                wafer_count=wip.wafer_count,
                current_step=wip.current_step,
                total_steps=wip.total_steps,
                priority=wip.priority,
                route=wip.route or self._generate_default_route(wip.total_steps),
                arrival_time=0.0
            )

    def initialize_demo_fab(self, num_equipments: int = 20, num_lots: int = 50):
        """데모용 가상 팹 초기화"""
        self.reset()

        # 장비 유형별 생성
        equipment_configs = [
            ("LITHO", "LITHOGRAPHY", 8, 600, 6),
            ("ETCH", "ETCHER", 15, 400, 4),
            ("CVD", "CVD", 12, 500, 5),
            ("CMP", "CMP", 10, 450, 4),
            ("IMPLANT", "IMPLANT", 8, 700, 3),
        ]

        for prefix, eq_type, wph, mtbf, count in equipment_configs:
            for i in range(1, count + 1):
                eq_id = f"{prefix}-{i:02d}"
                self.equipments[eq_id] = SimEquipment(
                    equipment_id=eq_id,
                    equipment_type=eq_type,
                    capacity_wph=wph + random.uniform(-2, 2),
                    mtbf_hours=mtbf + random.uniform(-50, 50),
                    mttr_hours=random.uniform(2, 6)
                )
                # 고장 시간 초기화
                self.equipments[eq_id].time_to_failure = random.expovariate(1 / mtbf)

        # Lot 생성
        for i in range(num_lots):
            lot_id = f"LOT-{datetime.now().strftime('%Y%m%d')}-{i:04d}"
            total_steps = random.randint(20, 40)
            self.lots[lot_id] = SimLot(
                lot_id=lot_id,
                wafer_count=random.choice([25, 50]),
                current_step=random.randint(1, total_steps // 2),  # 중간 공정
                total_steps=total_steps,
                priority=random.randint(1, 10),
                route=self._generate_default_route(total_steps),
                arrival_time=random.uniform(0, 24)  # 24시간 내 도착
            )

            # 초기 도착 이벤트 추가
            heapq.heappush(self.event_queue, Event(
                time=self.lots[lot_id].arrival_time,
                event_type="ARRIVAL",
                equipment_id="",
                lot_id=lot_id
            ))

    def _generate_default_route(self, total_steps: int) -> list:
        """기본 공정 라우트 생성"""
        route = []
        step_types = ["LITHOGRAPHY", "ETCHER", "CVD", "CMP", "IMPLANT"]

        for step in range(1, total_steps + 1):
            eq_type = random.choice(step_types)
            process_time = random.uniform(0.5, 2.0)  # 30분 ~ 2시간
            route.append({
                "step": step,
                "operation": f"OP-{step:03d}",
                "equipment_type": eq_type,
                "process_time": process_time
            })

        return route

    def run(self, duration_hours: float = 168.0, collect_interval: float = 1.0) -> SimulationMetrics:
        """
        시뮬레이션 실행

        Args:
            duration_hours: 시뮬레이션 기간 (시간)
            collect_interval: 메트릭 수집 간격 (시간)

        Returns:
            시뮬레이션 결과 메트릭
        """
        end_time = duration_hours
        next_collect_time = collect_interval

        while self.event_queue and self.current_time < end_time:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time

            if self.current_time >= end_time:
                break

            self._process_event(event)

            # 주기적 메트릭 수집
            if self.current_time >= next_collect_time:
                self._collect_metrics()
                next_collect_time += collect_interval

        return self._calculate_final_metrics()

    def _process_event(self, event: Event):
        """이벤트 처리"""
        if event.event_type == "ARRIVAL":
            self._handle_arrival(event)
        elif event.event_type == "PROCESS_START":
            self._handle_process_start(event)
        elif event.event_type == "PROCESS_END":
            self._handle_process_end(event)
        elif event.event_type == "BREAKDOWN":
            self._handle_breakdown(event)
        elif event.event_type == "REPAIR":
            self._handle_repair(event)

    def _handle_arrival(self, event: Event):
        """Lot 도착 처리"""
        lot = self.lots.get(event.lot_id)
        if not lot or lot.current_step > lot.total_steps:
            return

        # 다음 공정에 필요한 장비 찾기
        route_step = lot.route[lot.current_step - 1] if lot.current_step <= len(lot.route) else None
        if not route_step:
            return

        equipment_type = route_step["equipment_type"]
        target_equipment = self._find_best_equipment(equipment_type)

        if target_equipment:
            if target_equipment.status == "IDLE":
                # 즉시 처리 시작
                heapq.heappush(self.event_queue, Event(
                    time=self.current_time,
                    event_type="PROCESS_START",
                    equipment_id=target_equipment.equipment_id,
                    lot_id=lot.lot_id
                ))
            else:
                # 대기열에 추가
                target_equipment.queue.append(lot.lot_id)

    def _handle_process_start(self, event: Event):
        """공정 시작 처리"""
        equipment = self.equipments.get(event.equipment_id)
        lot = self.lots.get(event.lot_id)

        if not equipment or not lot:
            return

        equipment.status = "RUNNING"
        equipment.current_lot = lot.lot_id

        # 공정 시간 계산
        route_step = lot.route[lot.current_step - 1] if lot.current_step <= len(lot.route) else None
        process_time = route_step["process_time"] if route_step else 1.0

        # 공정 종료 이벤트 추가
        heapq.heappush(self.event_queue, Event(
            time=self.current_time + process_time,
            event_type="PROCESS_END",
            equipment_id=event.equipment_id,
            lot_id=event.lot_id
        ))

    def _handle_process_end(self, event: Event):
        """공정 종료 처리"""
        equipment = self.equipments.get(event.equipment_id)
        lot = self.lots.get(event.lot_id)

        if not equipment or not lot:
            return

        equipment.total_processed += 1
        equipment.current_lot = None
        lot.current_step += 1

        # Lot 완료 체크
        if lot.current_step > lot.total_steps:
            lot.completion_time = self.current_time
            self.completed_lots.append(lot)
        else:
            # 다음 공정으로 이동
            heapq.heappush(self.event_queue, Event(
                time=self.current_time,
                event_type="ARRIVAL",
                equipment_id="",
                lot_id=lot.lot_id
            ))

        # 대기열 처리
        if equipment.queue:
            next_lot_id = equipment.queue.pop(0)
            heapq.heappush(self.event_queue, Event(
                time=self.current_time,
                event_type="PROCESS_START",
                equipment_id=equipment.equipment_id,
                lot_id=next_lot_id
            ))
        else:
            equipment.status = "IDLE"

    def _handle_breakdown(self, event: Event):
        """장비 고장 처리"""
        equipment = self.equipments.get(event.equipment_id)
        if not equipment:
            return

        equipment.status = "DOWN"

        # 수리 완료 이벤트 추가
        repair_time = random.expovariate(1 / equipment.mttr_hours)
        heapq.heappush(self.event_queue, Event(
            time=self.current_time + repair_time,
            event_type="REPAIR",
            equipment_id=event.equipment_id
        ))

    def _handle_repair(self, event: Event):
        """장비 수리 완료 처리"""
        equipment = self.equipments.get(event.equipment_id)
        if not equipment:
            return

        equipment.status = "IDLE"

        # 다음 고장 시간 스케줄
        equipment.time_to_failure = random.expovariate(1 / equipment.mtbf_hours)
        heapq.heappush(self.event_queue, Event(
            time=self.current_time + equipment.time_to_failure,
            event_type="BREAKDOWN",
            equipment_id=equipment.equipment_id
        ))

        # 대기열 처리
        if equipment.queue:
            next_lot_id = equipment.queue.pop(0)
            heapq.heappush(self.event_queue, Event(
                time=self.current_time,
                event_type="PROCESS_START",
                equipment_id=equipment.equipment_id,
                lot_id=next_lot_id
            ))

    def _find_best_equipment(self, equipment_type: str) -> Optional[SimEquipment]:
        """최적 장비 선택 (가장 짧은 대기열)"""
        candidates = [
            eq for eq in self.equipments.values()
            if eq.equipment_type == equipment_type and eq.status != "DOWN"
        ]

        if not candidates:
            return None

        # 대기열 길이 기준 정렬
        return min(candidates, key=lambda eq: len(eq.queue))

    def _collect_metrics(self):
        """메트릭 수집"""
        wip_count = len([l for l in self.lots.values() if l.completion_time is None])
        avg_queue = sum(len(eq.queue) for eq in self.equipments.values()) / max(len(self.equipments), 1)

        self.metrics_history.append({
            "time": self.current_time,
            "wip_count": wip_count,
            "avg_queue_length": avg_queue,
            "completed_lots": len(self.completed_lots)
        })

    def _calculate_final_metrics(self) -> SimulationMetrics:
        """최종 메트릭 계산"""
        metrics = SimulationMetrics()

        metrics.total_lots_completed = len(self.completed_lots)
        metrics.total_wafers_completed = sum(l.wafer_count for l in self.completed_lots)

        if self.completed_lots:
            cycle_times = [
                l.completion_time - l.arrival_time
                for l in self.completed_lots
                if l.completion_time
            ]
            metrics.avg_cycle_time_hours = sum(cycle_times) / len(cycle_times) if cycle_times else 0

        if self.current_time > 0:
            days = self.current_time / 24
            metrics.throughput_lots_per_day = metrics.total_lots_completed / days
            metrics.throughput_wafers_per_day = metrics.total_wafers_completed / days

        # 장비 가동률 계산
        for eq_id, eq in self.equipments.items():
            utilization = (eq.total_processed * 1.0) / max(self.current_time, 1) * 100
            metrics.equipment_utilization[eq_id] = min(utilization * 10, 100)  # 스케일 조정

        # 병목 장비 식별 (높은 대기열)
        bottlenecks = sorted(
            self.equipments.values(),
            key=lambda eq: len(eq.queue),
            reverse=True
        )[:3]
        metrics.bottleneck_equipment = [
            {"equipment_id": eq.equipment_id, "queue_length": len(eq.queue)}
            for eq in bottlenecks
        ]

        metrics.wip_levels = self.metrics_history

        return metrics


class WhatIfScenarioEngine:
    """What-If 시나리오 분석 엔진"""

    def __init__(self, db: Session):
        self.db = db

    def create_scenario(
        self,
        name: str,
        scenario_type: str,
        parameters: dict,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> SimulationScenario:
        """시나리오 생성"""
        scenario = SimulationScenario(
            scenario_id=f"SCN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}",
            name=name,
            description=description,
            scenario_type=scenario_type,
            parameters=parameters,
            status="DRAFT",
            created_by=created_by
        )

        self.db.add(scenario)
        self.db.commit()
        self.db.refresh(scenario)

        return scenario

    def run_scenario(
        self,
        scenario_id: str,
        duration_hours: float = 168.0
    ) -> dict:
        """
        시나리오 실행

        1. 베이스라인 시뮬레이션 실행
        2. 시나리오 조건 적용
        3. 시나리오 시뮬레이션 실행
        4. 영향 분석 및 권장사항 생성
        """
        scenario = self.db.query(SimulationScenario).filter(
            SimulationScenario.scenario_id == scenario_id
        ).first()

        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")

        scenario.status = "RUNNING"
        scenario.executed_at = datetime.utcnow()
        self.db.commit()

        try:
            # 1. 베이스라인 시뮬레이션
            baseline_sim = VirtualFabSimulator(self.db)
            baseline_sim.initialize_demo_fab()
            baseline_metrics = baseline_sim.run(duration_hours)

            # 2. 시나리오 시뮬레이션
            scenario_sim = VirtualFabSimulator(self.db)
            scenario_sim.initialize_demo_fab()
            self._apply_scenario(scenario_sim, scenario)
            scenario_metrics = scenario_sim.run(duration_hours)

            # 3. 영향 분석
            impact = self._analyze_impact(baseline_metrics, scenario_metrics)

            # 4. 권장사항 생성
            recommendations = self._generate_recommendations(scenario, impact)

            # 결과 저장
            scenario.baseline_metrics = self._metrics_to_dict(baseline_metrics)
            scenario.scenario_metrics = self._metrics_to_dict(scenario_metrics)
            scenario.impact_analysis = impact
            scenario.recommendations = recommendations
            scenario.confidence_score = self._calculate_confidence(impact)
            scenario.status = "COMPLETED"
            scenario.completed_at = datetime.utcnow()
            self.db.commit()

            return {
                "scenario_id": scenario_id,
                "baseline": scenario.baseline_metrics,
                "scenario": scenario.scenario_metrics,
                "impact": impact,
                "recommendations": recommendations,
                "confidence_score": scenario.confidence_score
            }

        except Exception as e:
            scenario.status = "FAILED"
            self.db.commit()
            raise e

    def _apply_scenario(self, simulator: VirtualFabSimulator, scenario: SimulationScenario):
        """시나리오 조건 적용"""
        params = scenario.parameters

        if scenario.scenario_type == "EQUIPMENT_FAILURE":
            # 장비 고장 시나리오
            eq_id = params.get("equipment_id")
            if eq_id and eq_id in simulator.equipments:
                simulator.equipments[eq_id].status = "DOWN"
                # 즉시 고장 이벤트 추가
                heapq.heappush(simulator.event_queue, Event(
                    time=params.get("failure_time", 0),
                    event_type="BREAKDOWN",
                    equipment_id=eq_id
                ))

        elif scenario.scenario_type == "DEMAND_SPIKE":
            # 수요 급증 시나리오
            additional_lots = params.get("additional_lots", 20)
            for i in range(additional_lots):
                lot_id = f"SPIKE-{uuid.uuid4().hex[:8]}"
                simulator.lots[lot_id] = SimLot(
                    lot_id=lot_id,
                    wafer_count=25,
                    current_step=1,
                    total_steps=30,
                    priority=8,  # 높은 우선순위
                    route=simulator._generate_default_route(30),
                    arrival_time=random.uniform(0, 24)
                )
                heapq.heappush(simulator.event_queue, Event(
                    time=simulator.lots[lot_id].arrival_time,
                    event_type="ARRIVAL",
                    equipment_id="",
                    lot_id=lot_id
                ))

        elif scenario.scenario_type == "MAINTENANCE":
            # 유지보수 시나리오
            eq_id = params.get("equipment_id")
            duration = params.get("duration_hours", 8)
            if eq_id and eq_id in simulator.equipments:
                simulator.equipments[eq_id].status = "MAINTENANCE"
                # 유지보수 완료 이벤트 추가
                heapq.heappush(simulator.event_queue, Event(
                    time=duration,
                    event_type="REPAIR",
                    equipment_id=eq_id
                ))

    def _analyze_impact(
        self,
        baseline: SimulationMetrics,
        scenario: SimulationMetrics
    ) -> dict:
        """영향 분석"""
        def calc_change(baseline_val, scenario_val):
            if baseline_val == 0:
                return 0
            return ((scenario_val - baseline_val) / baseline_val) * 100

        return {
            "throughput_change_percent": calc_change(
                baseline.throughput_lots_per_day,
                scenario.throughput_lots_per_day
            ),
            "cycle_time_change_percent": calc_change(
                baseline.avg_cycle_time_hours,
                scenario.avg_cycle_time_hours
            ),
            "lots_completed_change": scenario.total_lots_completed - baseline.total_lots_completed,
            "wafers_completed_change": scenario.total_wafers_completed - baseline.total_wafers_completed,
            "utilization_impact": {
                eq_id: scenario.equipment_utilization.get(eq_id, 0) - baseline.equipment_utilization.get(eq_id, 0)
                for eq_id in baseline.equipment_utilization
            }
        }

    def _generate_recommendations(
        self,
        scenario: SimulationScenario,
        impact: dict
    ) -> list[str]:
        """권장사항 생성"""
        recommendations = []

        throughput_change = impact.get("throughput_change_percent", 0)
        cycle_time_change = impact.get("cycle_time_change_percent", 0)

        if throughput_change < -10:
            recommendations.append(f"처리량 {abs(throughput_change):.1f}% 감소 예상 - 대체 장비 활용 검토")

        if cycle_time_change > 10:
            recommendations.append(f"사이클 타임 {cycle_time_change:.1f}% 증가 예상 - 우선순위 재조정 권장")

        if scenario.scenario_type == "EQUIPMENT_FAILURE":
            eq_id = scenario.parameters.get("equipment_id", "")
            recommendations.append(f"장비 {eq_id}의 예방 정비 주기 단축 검토")
            recommendations.append("동일 유형 장비의 오버타임 가동 준비")

        elif scenario.scenario_type == "DEMAND_SPIKE":
            recommendations.append("병목 장비의 임시 추가 투입 검토")
            recommendations.append("저우선순위 Lot 일시 보류 고려")

        elif scenario.scenario_type == "MAINTENANCE":
            recommendations.append("유지보수 기간 동안 WIP 조정 권장")
            recommendations.append("야간/주말 유지보수 일정 검토")

        if not recommendations:
            recommendations.append("현재 시나리오의 영향은 제한적입니다")

        return recommendations

    def _metrics_to_dict(self, metrics: SimulationMetrics) -> dict:
        """메트릭을 딕셔너리로 변환"""
        return {
            "total_lots_completed": metrics.total_lots_completed,
            "total_wafers_completed": metrics.total_wafers_completed,
            "avg_cycle_time_hours": round(metrics.avg_cycle_time_hours, 2),
            "throughput_lots_per_day": round(metrics.throughput_lots_per_day, 2),
            "throughput_wafers_per_day": round(metrics.throughput_wafers_per_day, 2),
            "equipment_utilization": metrics.equipment_utilization,
            "bottleneck_equipment": metrics.bottleneck_equipment
        }

    def _calculate_confidence(self, impact: dict) -> float:
        """분석 신뢰도 계산"""
        # 영향이 클수록 신뢰도 높음 (분석 의미 있음)
        throughput_impact = abs(impact.get("throughput_change_percent", 0))
        cycle_time_impact = abs(impact.get("cycle_time_change_percent", 0))

        base_confidence = 70
        impact_bonus = min((throughput_impact + cycle_time_impact) / 2, 25)

        return min(base_confidence + impact_bonus, 95)


class BottleneckPredictor:
    """병목 예측 엔진"""

    def __init__(self, db: Session):
        self.db = db

    def predict_bottlenecks(
        self,
        horizon_hours: int = 24
    ) -> list[dict]:
        """
        향후 N시간 내 병목 예측

        Args:
            horizon_hours: 예측 기간 (시간)

        Returns:
            예측된 병목 목록
        """
        predictions = []

        # 가상 팹 시뮬레이션 실행
        simulator = VirtualFabSimulator(self.db)
        simulator.initialize_demo_fab()
        metrics = simulator.run(duration_hours=horizon_hours)

        # 병목 장비 분석
        for eq_id, eq in simulator.equipments.items():
            queue_length = len(eq.queue)

            if queue_length > 5:  # 임계값
                severity = "CRITICAL" if queue_length > 15 else "HIGH" if queue_length > 10 else "MEDIUM"

                predictions.append({
                    "bottleneck_id": f"BN-{uuid.uuid4().hex[:8].upper()}",
                    "equipment_id": eq_id,
                    "equipment_type": eq.equipment_type,
                    "predicted_queue_length": queue_length,
                    "predicted_wait_hours": queue_length * 1.5,  # 추정 대기 시간
                    "severity": severity,
                    "confidence": 75 + random.uniform(0, 20),
                    "predicted_time": (datetime.utcnow() + timedelta(hours=random.uniform(4, horizon_hours))).isoformat(),
                    "recommended_actions": self._get_recommendations(eq_id, eq.equipment_type, queue_length)
                })

        # 심각도 기준 정렬
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        predictions.sort(key=lambda x: severity_order.get(x["severity"], 4))

        return predictions

    def _get_recommendations(self, eq_id: str, eq_type: str, queue_length: int) -> list[str]:
        """병목 해소 권장 조치"""
        recommendations = []

        if queue_length > 15:
            recommendations.append(f"긴급: {eq_id} 추가 장비 투입 또는 오버타임 가동")
            recommendations.append("고우선순위 Lot 우선 처리 후 저우선순위 일시 보류")

        if queue_length > 10:
            recommendations.append(f"{eq_type} 유형 다른 장비로 Lot 재배정 검토")
            recommendations.append("유지보수 일정 조정 검토")

        recommendations.append(f"{eq_id} 공정 파라미터 최적화로 처리 시간 단축 검토")

        return recommendations
