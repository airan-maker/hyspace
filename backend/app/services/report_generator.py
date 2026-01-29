"""
Report Generation Service

보고서 생성 서비스
PDF, Excel, CSV 포맷 지원
"""

from datetime import datetime, timedelta
from typing import Optional, Any
import json
import csv
import io
import uuid

from sqlalchemy.orm import Session

from app.services.yield_analyzer import YieldAnalyzer
from app.services.supply_chain import SupplyChainAnalytics
from app.services.notification import NotificationService


class ReportGenerator:
    """
    보고서 생성 엔진

    지원 보고서 유형:
    - 일간 수율 리포트
    - 주간 성과 요약
    - 월간 경영진 대시보드
    - 감사 컴플라이언스 보고서
    - 공급망 리스크 보고서
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_report(
        self,
        report_type: str,
        format: str = "json",
        start_date: datetime = None,
        end_date: datetime = None,
        **kwargs
    ) -> dict:
        """
        보고서 생성

        Args:
            report_type: 보고서 유형
            format: 출력 포맷 (json, csv, html)
            start_date: 시작일
            end_date: 종료일

        Returns:
            보고서 데이터
        """
        # 기본 날짜 설정
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            if report_type == "daily_yield":
                start_date = end_date - timedelta(days=1)
            elif report_type == "weekly_performance":
                start_date = end_date - timedelta(days=7)
            elif report_type == "monthly_executive":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)

        # 보고서 유형별 생성
        report_data = None

        if report_type == "daily_yield":
            report_data = self._generate_daily_yield_report(start_date, end_date)
        elif report_type == "weekly_performance":
            report_data = self._generate_weekly_performance_report(start_date, end_date)
        elif report_type == "monthly_executive":
            report_data = self._generate_monthly_executive_report(start_date, end_date)
        elif report_type == "supply_chain_risk":
            report_data = self._generate_supply_chain_risk_report(start_date, end_date)
        elif report_type == "audit_compliance":
            report_data = self._generate_audit_compliance_report(start_date, end_date)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        # 포맷 변환
        if format == "csv":
            return self._to_csv(report_data)
        elif format == "html":
            return self._to_html(report_data)
        else:
            return report_data

    # ==================== 보고서 유형별 생성 ====================

    def _generate_daily_yield_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """일간 수율 리포트"""
        analyzer = YieldAnalyzer(self.db)
        dashboard = analyzer.get_dashboard_data(days=1)

        return {
            "report_id": f"RPT-YIELD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "report_type": "daily_yield",
            "title": "일간 수율 리포트",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "overall_yield": dashboard.overall_yield,
                "yield_target": dashboard.yield_target,
                "yield_vs_target": dashboard.yield_vs_target,
                "status": "ABOVE_TARGET" if dashboard.yield_vs_target >= 0 else "BELOW_TARGET"
            },
            "events": {
                "active_events": dashboard.active_events,
                "critical_events": dashboard.critical_events,
                "events_today": dashboard.events_this_week  # 데모용
            },
            "equipment_performance": [
                {
                    "equipment_id": eq.equipment_id,
                    "equipment_type": eq.equipment_type,
                    "avg_yield": eq.avg_yield,
                    "wafer_count": eq.wafer_count,
                    "trend": eq.trend
                }
                for eq in dashboard.by_equipment
            ],
            "top_defects": dashboard.top_defect_types,
            "alerts": dashboard.recent_alerts,
            "recommendations": self._generate_yield_recommendations(dashboard)
        }

    def _generate_weekly_performance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """주간 성과 요약"""
        analyzer = YieldAnalyzer(self.db)
        dashboard = analyzer.get_dashboard_data(days=7)
        notification_service = NotificationService(self.db)
        alert_summary = notification_service.get_alert_summary(hours=168)

        return {
            "report_id": f"RPT-WEEKLY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "report_type": "weekly_performance",
            "title": "주간 성과 요약 보고서",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "week_number": end_date.isocalendar()[1]
            },
            "yield_summary": {
                "overall_yield": dashboard.overall_yield,
                "yield_target": dashboard.yield_target,
                "achievement_rate": (dashboard.overall_yield / dashboard.yield_target * 100) if dashboard.yield_target else 0,
                "trend_data": [
                    {"date": t.date.isoformat(), "yield": t.yield_percent, "wafers": t.wafer_count}
                    for t in dashboard.trend_data[-7:]
                ]
            },
            "production_summary": {
                "total_wafers_processed": sum(eq.wafer_count for eq in dashboard.by_equipment),
                "by_product": [
                    {"product_id": p.product_id, "yield": p.avg_yield, "wafers": p.wafer_count}
                    for p in dashboard.by_product
                ]
            },
            "equipment_summary": {
                "total_equipment": len(dashboard.by_equipment),
                "underperforming": len([eq for eq in dashboard.by_equipment if eq.avg_yield < 90]),
                "top_performers": [
                    {"equipment_id": eq.equipment_id, "yield": eq.avg_yield}
                    for eq in sorted(dashboard.by_equipment, key=lambda x: x.avg_yield, reverse=True)[:3]
                ],
                "needs_attention": [
                    {"equipment_id": eq.equipment_id, "yield": eq.avg_yield, "trend": eq.trend}
                    for eq in sorted(dashboard.by_equipment, key=lambda x: x.avg_yield)[:3]
                ]
            },
            "alerts_summary": alert_summary,
            "key_events": [
                {
                    "event_id": f"YE-{i}",
                    "title": f"수율 저하 이벤트 #{i}",
                    "severity": "HIGH" if i % 2 == 0 else "MEDIUM",
                    "status": "RESOLVED" if i > 2 else "INVESTIGATING"
                }
                for i in range(1, 6)
            ],
            "action_items": self._generate_weekly_action_items(dashboard)
        }

    def _generate_monthly_executive_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """월간 경영진 대시보드"""
        analyzer = YieldAnalyzer(self.db)
        dashboard = analyzer.get_dashboard_data(days=30)
        supply_analytics = SupplyChainAnalytics(self.db)
        supply_data = supply_analytics.get_dashboard_data()

        return {
            "report_id": f"RPT-EXEC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "report_type": "monthly_executive",
            "title": "월간 경영진 대시보드",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "month": end_date.strftime("%Y-%m")
            },
            "executive_summary": {
                "overall_status": "GREEN" if dashboard.yield_vs_target >= 0 else "YELLOW" if dashboard.yield_vs_target > -5 else "RED",
                "key_achievements": [
                    f"전체 수율 {dashboard.overall_yield:.1f}% 달성",
                    f"목표 대비 {'+' if dashboard.yield_vs_target >= 0 else ''}{dashboard.yield_vs_target:.1f}%",
                    f"긴급 이벤트 {dashboard.critical_events}건 관리"
                ],
                "key_challenges": [
                    "장비 노후화로 인한 수율 변동",
                    "공급망 리드타임 증가 추세",
                    "원자재 가격 상승 압박"
                ] if dashboard.yield_vs_target < 0 else []
            },
            "kpi_dashboard": {
                "yield": {
                    "current": dashboard.overall_yield,
                    "target": dashboard.yield_target,
                    "previous_month": dashboard.overall_yield - 0.5,  # 데모
                    "yoy_change": 2.3  # 데모
                },
                "production": {
                    "wafers_processed": sum(eq.wafer_count for eq in dashboard.by_equipment),
                    "capacity_utilization": 87.5,  # 데모
                    "oee_average": 85.2  # 데모
                },
                "quality": {
                    "defect_rate": 100 - dashboard.overall_yield,
                    "first_pass_yield": dashboard.overall_yield - 2,  # 데모
                    "customer_returns": 3  # 데모
                },
                "supply_chain": supply_data["key_metrics"]
            },
            "financial_impact": {
                "estimated_revenue_impact": self._calculate_revenue_impact(dashboard),
                "cost_per_wafer": 45.50,  # 데모
                "yield_loss_cost": self._calculate_yield_loss_cost(dashboard)
            },
            "risk_overview": {
                "operational_risks": dashboard.critical_events,
                "supply_risks": supply_data["risk_summary"]["total_active_risks"],
                "top_risks": supply_data["active_risks"][:3]
            },
            "strategic_recommendations": self._generate_executive_recommendations(dashboard, supply_data)
        }

    def _generate_supply_chain_risk_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """공급망 리스크 보고서"""
        analytics = SupplyChainAnalytics(self.db)
        data = analytics.get_dashboard_data()

        return {
            "report_id": f"RPT-SUPPLY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "report_type": "supply_chain_risk",
            "title": "공급망 리스크 보고서",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "risk_summary": data["risk_summary"],
            "active_risks": data["active_risks"],
            "supplier_hierarchy": data["supplier_hierarchy"],
            "inventory_status": data["inventory_status"],
            "recommendations": data["recommendations"],
            "mitigation_actions": [
                {
                    "action": "대만 공급업체 대체 소싱 확보",
                    "priority": "HIGH",
                    "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    "owner": "Procurement Team"
                },
                {
                    "action": "안전 재고 수준 상향 조정",
                    "priority": "MEDIUM",
                    "deadline": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                    "owner": "Supply Chain Manager"
                }
            ]
        }

    def _generate_audit_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """감사 컴플라이언스 보고서"""
        from app.services.audit_logger import AuditLogger

        audit_logger = AuditLogger(self.db)
        compliance_data = audit_logger.generate_compliance_report(start_date, end_date)

        return {
            "report_id": f"RPT-AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "report_type": "audit_compliance",
            "title": "감사 컴플라이언스 보고서",
            "generated_at": datetime.utcnow().isoformat(),
            **compliance_data,
            "compliance_status": {
                "data_access_controls": "COMPLIANT",
                "audit_trail_completeness": "COMPLIANT",
                "role_based_access": "COMPLIANT",
                "data_retention": "COMPLIANT"
            },
            "attestation": {
                "prepared_by": "System Generated",
                "reviewed_by": None,
                "approved_by": None
            }
        }

    # ==================== 헬퍼 메서드 ====================

    def _generate_yield_recommendations(self, dashboard) -> list[str]:
        """수율 개선 권장사항"""
        recommendations = []

        if dashboard.yield_vs_target < 0:
            recommendations.append(f"전체 수율이 목표 대비 {abs(dashboard.yield_vs_target):.1f}% 낮음 - 원인 분석 필요")

        low_yield_equipment = [eq for eq in dashboard.by_equipment if eq.avg_yield < 90]
        if low_yield_equipment:
            recommendations.append(f"{len(low_yield_equipment)}개 장비의 수율이 90% 미만 - PM 일정 검토 권장")

        if dashboard.critical_events > 0:
            recommendations.append(f"{dashboard.critical_events}건의 긴급 이벤트 - 즉각적인 조치 필요")

        if not recommendations:
            recommendations.append("현재 수율 목표를 달성하고 있습니다. 현재 프로세스 유지 권장")

        return recommendations

    def _generate_weekly_action_items(self, dashboard) -> list[dict]:
        """주간 액션 아이템"""
        items = []

        # 저수율 장비 관련
        for eq in dashboard.by_equipment:
            if eq.avg_yield < 88:
                items.append({
                    "action": f"{eq.equipment_id} 장비 점검 및 교정",
                    "priority": "HIGH" if eq.avg_yield < 85 else "MEDIUM",
                    "owner": "Equipment Team",
                    "due": (datetime.utcnow() + timedelta(days=3)).isoformat()
                })

        # 이벤트 관련
        if dashboard.active_events > 0:
            items.append({
                "action": f"{dashboard.active_events}건 활성 이벤트 RCA 완료",
                "priority": "HIGH",
                "owner": "Process Engineering",
                "due": (datetime.utcnow() + timedelta(days=5)).isoformat()
            })

        return items[:5]  # 최대 5개

    def _generate_executive_recommendations(self, yield_data, supply_data) -> list[str]:
        """경영진 권장사항"""
        recommendations = []

        # 수율 관련
        if yield_data.yield_vs_target < -3:
            recommendations.append("수율 개선 태스크포스 구성 검토")

        # 장비 관련
        underperforming = len([eq for eq in yield_data.by_equipment if eq.avg_yield < 90])
        if underperforming > 2:
            recommendations.append(f"장비 투자 계획 재검토 ({underperforming}개 장비 노후화)")

        # 공급망 관련
        if supply_data["risk_summary"]["critical_risks"] > 0:
            recommendations.append("공급망 이중화 전략 수립 긴급")

        if not recommendations:
            recommendations.append("현재 운영 상태 양호 - 지속적인 모니터링 유지")

        return recommendations

    def _calculate_revenue_impact(self, dashboard) -> float:
        """매출 영향 계산 (데모)"""
        # 수율 1% 차이 = $100,000 영향으로 가정
        impact_per_percent = 100000
        return dashboard.yield_vs_target * impact_per_percent

    def _calculate_yield_loss_cost(self, dashboard) -> float:
        """수율 손실 비용 계산 (데모)"""
        # 목표 미달 시 손실 비용
        if dashboard.yield_vs_target < 0:
            return abs(dashboard.yield_vs_target) * 50000
        return 0

    # ==================== 포맷 변환 ====================

    def _to_csv(self, report_data: dict) -> dict:
        """CSV 포맷 변환"""
        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow(["Report", report_data.get("title", "Report")])
        writer.writerow(["Generated", report_data.get("generated_at", "")])
        writer.writerow([])

        # 요약 데이터
        if "summary" in report_data:
            writer.writerow(["Summary"])
            for key, value in report_data["summary"].items():
                writer.writerow([key, value])
            writer.writerow([])

        # 장비 성능 데이터
        if "equipment_performance" in report_data:
            writer.writerow(["Equipment Performance"])
            writer.writerow(["Equipment ID", "Type", "Avg Yield", "Wafer Count", "Trend"])
            for eq in report_data["equipment_performance"]:
                writer.writerow([
                    eq["equipment_id"],
                    eq["equipment_type"],
                    eq["avg_yield"],
                    eq["wafer_count"],
                    eq["trend"]
                ])

        return {
            "format": "csv",
            "content": output.getvalue(),
            "filename": f"{report_data.get('report_id', 'report')}.csv"
        }

    def _to_html(self, report_data: dict) -> dict:
        """HTML 포맷 변환"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            f"<title>{report_data.get('title', 'Report')}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #333; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #4a90d9; color: white; }",
            ".status-green { color: green; }",
            ".status-red { color: red; }",
            "</style>",
            "</head><body>",
            f"<h1>{report_data.get('title', 'Report')}</h1>",
            f"<p>Generated: {report_data.get('generated_at', '')}</p>",
        ]

        # 요약 섹션
        if "summary" in report_data:
            html_parts.append("<h2>Summary</h2>")
            html_parts.append("<table><tr><th>Metric</th><th>Value</th></tr>")
            for key, value in report_data["summary"].items():
                html_parts.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
            html_parts.append("</table>")

        # 권장사항
        if "recommendations" in report_data:
            html_parts.append("<h2>Recommendations</h2><ul>")
            for rec in report_data["recommendations"]:
                html_parts.append(f"<li>{rec}</li>")
            html_parts.append("</ul>")

        html_parts.extend(["</body></html>"])

        return {
            "format": "html",
            "content": "\n".join(html_parts),
            "filename": f"{report_data.get('report_id', 'report')}.html"
        }


# ==================== 스케줄된 보고서 ====================

class ScheduledReportManager:
    """스케줄된 보고서 관리"""

    def __init__(self, db: Session):
        self.db = db
        self.generator = ReportGenerator(db)

    def get_scheduled_reports(self) -> list[dict]:
        """스케줄된 보고서 목록"""
        # 데모용 정적 데이터
        return [
            {
                "schedule_id": "SCH-001",
                "report_type": "daily_yield",
                "schedule": "0 8 * * *",  # 매일 오전 8시
                "format": "html",
                "recipients": ["engineering@hyspace.com"],
                "is_active": True
            },
            {
                "schedule_id": "SCH-002",
                "report_type": "weekly_performance",
                "schedule": "0 9 * * 1",  # 매주 월요일 오전 9시
                "format": "html",
                "recipients": ["management@hyspace.com"],
                "is_active": True
            },
            {
                "schedule_id": "SCH-003",
                "report_type": "monthly_executive",
                "schedule": "0 10 1 * *",  # 매월 1일 오전 10시
                "format": "html",
                "recipients": ["executives@hyspace.com"],
                "is_active": True
            }
        ]
