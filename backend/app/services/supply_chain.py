"""
Supply Chain Service

공급망 관리 서비스
리스크 탐지, 재고 최적화, Tier-N 가시성
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid
import random

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.supply_chain import (
    Supplier, Material, SupplyRisk, InventoryRecommendation,
    SupplyChainEvent
)


class SupplyChainService:
    """공급망 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 공급업체 관리 ====================

    def create_supplier(
        self,
        supplier_id: str,
        name: str,
        tier: str,
        country: str,
        **kwargs
    ) -> Supplier:
        """공급업체 등록"""
        supplier = Supplier(
            supplier_id=supplier_id,
            name=name,
            tier=tier,
            country=country,
            **kwargs
        )

        # 리스크 점수 자동 계산
        supplier.risk_score = self._calculate_supplier_risk_score(supplier)

        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)

        return supplier

    def _calculate_supplier_risk_score(self, supplier: Supplier) -> float:
        """공급업체 리스크 점수 계산"""
        base_score = 30

        # 지정학적 리스크 (국가별)
        high_risk_countries = ["Taiwan", "China", "Russia", "Ukraine"]
        if supplier.country in high_risk_countries:
            base_score += 30

        # Tier 레벨 (하위 Tier일수록 가시성 낮음)
        tier_risk = {"TIER_1": 0, "TIER_2": 10, "TIER_3": 20}
        base_score += tier_risk.get(supplier.tier, 10)

        # 품질 평가
        if supplier.quality_rating:
            base_score -= (supplier.quality_rating - 80) * 0.5

        # 정시 납품률
        if supplier.on_time_delivery_rate:
            base_score -= (supplier.on_time_delivery_rate - 90) * 0.3

        return max(0, min(100, base_score))

    def get_suppliers(
        self,
        tier: Optional[str] = None,
        country: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100
    ) -> list[Supplier]:
        """공급업체 목록 조회"""
        query = self.db.query(Supplier).filter(Supplier.is_active == is_active)

        if tier:
            query = query.filter(Supplier.tier == tier)
        if country:
            query = query.filter(Supplier.country == country)

        return query.limit(limit).all()

    def get_supplier_hierarchy(self) -> dict:
        """공급업체 계층 구조 조회"""
        suppliers = self.db.query(Supplier).filter(Supplier.is_active == True).all()

        hierarchy = {
            "TIER_0": {"name": "자사 (HySpace)", "suppliers": []},
            "TIER_1": {"name": "1차 협력사", "suppliers": []},
            "TIER_2": {"name": "2차 협력사", "suppliers": []},
            "TIER_3": {"name": "원자재 공급", "suppliers": []},
        }

        for supplier in suppliers:
            tier = supplier.tier
            if tier in hierarchy:
                hierarchy[tier]["suppliers"].append({
                    "supplier_id": supplier.supplier_id,
                    "name": supplier.name,
                    "country": supplier.country,
                    "risk_score": supplier.risk_score,
                    "materials_count": len(supplier.materials)
                })

        return hierarchy

    # ==================== 자재 관리 ====================

    def create_material(
        self,
        material_id: str,
        name: str,
        category: str,
        **kwargs
    ) -> Material:
        """자재 등록"""
        material = Material(
            material_id=material_id,
            name=name,
            category=category,
            **kwargs
        )

        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)

        return material

    def get_materials(
        self,
        category: Optional[str] = None,
        criticality: Optional[str] = None,
        below_reorder: bool = False,
        limit: int = 100
    ) -> list[Material]:
        """자재 목록 조회"""
        query = self.db.query(Material).filter(Material.is_active == True)

        if category:
            query = query.filter(Material.category == category)
        if criticality:
            query = query.filter(Material.criticality == criticality)
        if below_reorder:
            query = query.filter(Material.current_stock <= Material.reorder_point)

        return query.limit(limit).all()

    def get_inventory_status(self) -> dict:
        """재고 현황 요약"""
        materials = self.db.query(Material).filter(Material.is_active == True).all()

        total_value = sum(m.total_value or 0 for m in materials)
        below_safety = len([m for m in materials if m.current_stock and m.safety_stock and m.current_stock < m.safety_stock])
        below_reorder = len([m for m in materials if m.current_stock and m.reorder_point and m.current_stock <= m.reorder_point])

        by_category = {}
        for m in materials:
            cat = m.category or "OTHER"
            if cat not in by_category:
                by_category[cat] = {"count": 0, "value": 0}
            by_category[cat]["count"] += 1
            by_category[cat]["value"] += m.total_value or 0

        by_criticality = {}
        for m in materials:
            crit = m.criticality or "UNKNOWN"
            if crit not in by_criticality:
                by_criticality[crit] = 0
            by_criticality[crit] += 1

        return {
            "total_materials": len(materials),
            "total_inventory_value": round(total_value, 2),
            "materials_below_safety_stock": below_safety,
            "materials_below_reorder_point": below_reorder,
            "by_category": by_category,
            "by_criticality": by_criticality
        }

    # ==================== 리스크 관리 ====================

    def create_risk(
        self,
        title: str,
        risk_type: str,
        severity: str,
        description: Optional[str] = None,
        source: str = "INTERNAL",
        **kwargs
    ) -> SupplyRisk:
        """리스크 등록"""
        risk = SupplyRisk(
            risk_id=f"RISK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            title=title,
            description=description,
            risk_type=risk_type,
            severity=severity,
            source=source,
            status="OPEN",
            **kwargs
        )

        self.db.add(risk)
        self.db.commit()
        self.db.refresh(risk)

        return risk

    def get_risks(
        self,
        severity: Optional[str] = None,
        risk_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> list[SupplyRisk]:
        """리스크 목록 조회"""
        query = self.db.query(SupplyRisk)

        if severity:
            query = query.filter(SupplyRisk.severity == severity)
        if risk_type:
            query = query.filter(SupplyRisk.risk_type == risk_type)
        if status:
            query = query.filter(SupplyRisk.status == status)

        return query.order_by(SupplyRisk.detected_at.desc()).limit(limit).all()

    def get_risk_summary(self) -> dict:
        """리스크 현황 요약"""
        risks = self.db.query(SupplyRisk).filter(
            SupplyRisk.status.in_(["OPEN", "MONITORING", "MITIGATING"])
        ).all()

        by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        by_type = {}

        for risk in risks:
            if risk.severity in by_severity:
                by_severity[risk.severity] += 1
            risk_type = risk.risk_type or "OTHER"
            by_type[risk_type] = by_type.get(risk_type, 0) + 1

        return {
            "total_active_risks": len(risks),
            "critical_risks": by_severity["CRITICAL"],
            "high_risks": by_severity["HIGH"],
            "by_severity": by_severity,
            "by_type": by_type
        }


class RiskDetector:
    """리스크 탐지 엔진"""

    def __init__(self, db: Session):
        self.db = db
        self.supply_service = SupplyChainService(db)

    def scan_for_risks(self) -> list[dict]:
        """리스크 자동 스캔"""
        detected_risks = []

        # 1. 재고 부족 리스크
        detected_risks.extend(self._detect_inventory_risks())

        # 2. 공급업체 집중 리스크
        detected_risks.extend(self._detect_concentration_risks())

        # 3. 리드타임 리스크
        detected_risks.extend(self._detect_leadtime_risks())

        # 4. 지정학적 리스크 (데모)
        detected_risks.extend(self._detect_geopolitical_risks())

        return detected_risks

    def _detect_inventory_risks(self) -> list[dict]:
        """재고 부족 리스크 탐지"""
        risks = []

        materials = self.db.query(Material).filter(
            Material.is_active == True,
            Material.current_stock <= Material.reorder_point
        ).all()

        for material in materials:
            if material.current_stock and material.safety_stock:
                if material.current_stock < material.safety_stock:
                    severity = "CRITICAL" if material.criticality == "CRITICAL" else "HIGH"
                else:
                    severity = "MEDIUM"

                risks.append({
                    "risk_type": "INVENTORY_SHORTAGE",
                    "severity": severity,
                    "title": f"재고 부족 경고: {material.name}",
                    "description": f"현재 재고 {material.current_stock} {material.unit} (안전재고: {material.safety_stock})",
                    "material_id": material.material_id,
                    "recommended_action": "긴급 발주 검토"
                })

        return risks

    def _detect_concentration_risks(self) -> list[dict]:
        """공급업체 집중 리스크 탐지"""
        risks = []

        # 단일 공급업체 자재 탐지
        materials = self.db.query(Material).filter(Material.is_active == True).all()

        for material in materials:
            if len(material.suppliers) == 1 and material.criticality in ["CRITICAL", "HIGH"]:
                supplier = material.suppliers[0]
                risks.append({
                    "risk_type": "CONCENTRATION",
                    "severity": "HIGH" if material.criticality == "CRITICAL" else "MEDIUM",
                    "title": f"단일 공급업체 의존: {material.name}",
                    "description": f"유일한 공급업체: {supplier.name} ({supplier.country})",
                    "material_id": material.material_id,
                    "supplier_id": supplier.supplier_id,
                    "recommended_action": "대체 공급업체 확보 검토"
                })

        return risks

    def _detect_leadtime_risks(self) -> list[dict]:
        """리드타임 리스크 탐지"""
        risks = []

        # 재고가 리드타임 내 소진 예상되는 자재
        materials = self.db.query(Material).filter(
            Material.is_active == True,
            Material.daily_consumption > 0
        ).all()

        for material in materials:
            if material.current_stock and material.daily_consumption and material.lead_time_days:
                days_until_stockout = material.current_stock / material.daily_consumption
                if days_until_stockout < material.lead_time_days:
                    risks.append({
                        "risk_type": "LEADTIME",
                        "severity": "CRITICAL" if days_until_stockout < 7 else "HIGH",
                        "title": f"재고 소진 임박: {material.name}",
                        "description": f"예상 소진일: {int(days_until_stockout)}일 후 (리드타임: {material.lead_time_days}일)",
                        "material_id": material.material_id,
                        "recommended_action": "긴급 발주 또는 익스프레스 배송 요청"
                    })

        return risks

    def _detect_geopolitical_risks(self) -> list[dict]:
        """지정학적 리스크 탐지 (데모 데이터)"""
        # 실제로는 뉴스 API, 외부 리스크 데이터 소스 연동
        demo_risks = [
            {
                "risk_type": "GEOPOLITICAL",
                "severity": "HIGH",
                "title": "대만 해협 긴장 고조",
                "description": "TSMC 등 주요 반도체 공급업체 영향 가능성",
                "source": "NEWS",
                "recommended_action": "대만 공급업체 대체 재고 확보 검토"
            },
            {
                "risk_type": "LOGISTICS",
                "severity": "MEDIUM",
                "title": "홍해 운송 지연",
                "description": "수에즈 우회로 인한 유럽발 자재 리드타임 2주 증가 예상",
                "source": "NEWS",
                "recommended_action": "유럽 공급업체 발주 리드타임 조정"
            }
        ]

        return demo_risks


class InventoryOptimizer:
    """재고 최적화 엔진"""

    def __init__(self, db: Session):
        self.db = db

    def generate_recommendations(self) -> list[dict]:
        """재고 최적화 권장사항 생성"""
        recommendations = []

        materials = self.db.query(Material).filter(Material.is_active == True).all()

        for material in materials:
            rec = self._analyze_material(material)
            if rec:
                recommendations.append(rec)

        # 긴급도 기준 정렬
        urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        recommendations.sort(key=lambda x: urgency_order.get(x.get("urgency", "LOW"), 4))

        return recommendations

    def _analyze_material(self, material: Material) -> Optional[dict]:
        """개별 자재 분석"""
        if not material.current_stock or not material.reorder_point:
            return None

        # 재발주 필요
        if material.current_stock <= material.reorder_point:
            order_qty = (material.max_stock or material.reorder_point * 2) - material.current_stock

            return {
                "recommendation_id": f"REC-{uuid.uuid4().hex[:8].upper()}",
                "material_id": material.material_id,
                "material_name": material.name,
                "action": "REORDER",
                "urgency": "CRITICAL" if material.current_stock < (material.safety_stock or 0) else "HIGH",
                "quantity": order_qty,
                "unit": material.unit,
                "rationale": f"현재 재고 {material.current_stock} {material.unit}가 재발주점 {material.reorder_point} 이하",
                "cost_impact": order_qty * (material.unit_cost or 0),
                "risk_mitigation": "재고 소진으로 인한 생산 중단 방지"
            }

        # 과잉 재고
        if material.max_stock and material.current_stock > material.max_stock * 1.2:
            excess = material.current_stock - material.max_stock

            return {
                "recommendation_id": f"REC-{uuid.uuid4().hex[:8].upper()}",
                "material_id": material.material_id,
                "material_name": material.name,
                "action": "REDUCE",
                "urgency": "LOW",
                "quantity": excess,
                "unit": material.unit,
                "rationale": f"최대 재고 {material.max_stock} 대비 {excess} {material.unit} 과잉",
                "cost_impact": -excess * (material.unit_cost or 0) * 0.1,  # 재고 유지비 절감
                "risk_mitigation": "재고 유지 비용 절감, 진부화 리스크 감소"
            }

        return None

    def simulate_order_impact(
        self,
        material_id: str,
        order_quantity: float,
        lead_time_days: int
    ) -> dict:
        """발주 영향 시뮬레이션"""
        material = self.db.query(Material).filter(
            Material.material_id == material_id
        ).first()

        if not material:
            raise ValueError(f"Material not found: {material_id}")

        current = material.current_stock or 0
        daily_consumption = material.daily_consumption or 0

        # 입고 전 재고 예측
        stock_before_delivery = current - (daily_consumption * lead_time_days)
        stock_after_delivery = stock_before_delivery + order_quantity

        # 재고 소진 여부
        will_stockout = stock_before_delivery < 0

        # 비용 계산
        order_cost = order_quantity * (material.unit_cost or 0)

        return {
            "material_id": material_id,
            "order_quantity": order_quantity,
            "order_cost": round(order_cost, 2),
            "lead_time_days": lead_time_days,
            "current_stock": current,
            "projected_stock_at_delivery": max(0, stock_before_delivery),
            "stock_after_delivery": stock_after_delivery,
            "will_stockout_before_delivery": will_stockout,
            "stockout_day": int(current / daily_consumption) if daily_consumption > 0 and will_stockout else None,
            "recommendation": "긴급 익스프레스 배송 검토" if will_stockout else "정상 발주 진행"
        }


class SupplyChainAnalytics:
    """공급망 분석"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_data(self) -> dict:
        """대시보드 데이터"""
        supply_service = SupplyChainService(self.db)
        risk_detector = RiskDetector(self.db)
        optimizer = InventoryOptimizer(self.db)

        # 데모 데이터 포함
        return {
            "supplier_hierarchy": supply_service.get_supplier_hierarchy(),
            "inventory_status": supply_service.get_inventory_status(),
            "risk_summary": supply_service.get_risk_summary(),
            "active_risks": self._get_demo_risks(),
            "recommendations": optimizer.generate_recommendations()[:5],
            "key_metrics": {
                "total_suppliers": 45,
                "tier1_suppliers": 12,
                "total_materials": 320,
                "critical_materials": 28,
                "inventory_value_millions": 125.5,
                "avg_on_time_delivery": 94.2,
                "supply_chain_risk_index": 42.5
            }
        }

    def _get_demo_risks(self) -> list[dict]:
        """데모 리스크 데이터"""
        return [
            {
                "risk_id": "RISK-20260129-A1B2C3",
                "title": "ASML EUV 장비 리드타임 증가",
                "risk_type": "CAPACITY",
                "severity": "HIGH",
                "description": "글로벌 수요 증가로 EUV 리소그래피 장비 리드타임 18개월로 증가",
                "detected_at": "2026-01-25T10:30:00",
                "status": "MONITORING",
                "affected_supplier": "ASML"
            },
            {
                "risk_id": "RISK-20260129-D4E5F6",
                "title": "네온 가스 공급 불안정",
                "risk_type": "GEOPOLITICAL",
                "severity": "MEDIUM",
                "description": "우크라이나 상황으로 인한 반도체용 희귀가스 공급 불안정",
                "detected_at": "2026-01-28T14:20:00",
                "status": "MITIGATING",
                "affected_material": "Neon Gas"
            },
            {
                "risk_id": "RISK-20260129-G7H8I9",
                "title": "포토레지스트 품질 이슈",
                "risk_type": "QUALITY",
                "severity": "LOW",
                "description": "JSR 포토레지스트 신규 배치 품질 검사 진행 중",
                "detected_at": "2026-01-29T09:00:00",
                "status": "OPEN",
                "affected_supplier": "JSR Corporation"
            }
        ]
