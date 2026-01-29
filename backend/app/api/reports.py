"""
Reports API Endpoints

보고서 생성 및 관리 API
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.report_generator import ReportGenerator, ScheduledReportManager
from app.services.audit_logger import AuditLogger

router = APIRouter(prefix="/reports", tags=["Reports"])


# ==================== Schemas ====================

class ReportRequest(BaseModel):
    report_type: str
    format: str = "json"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ScheduleCreate(BaseModel):
    report_type: str
    schedule: str  # cron expression
    format: str = "html"
    recipients: list[str]


# ==================== Report Types ====================

@router.get("/types")
def get_report_types():
    """사용 가능한 보고서 유형 목록"""
    return {
        "report_types": [
            {
                "type": "daily_yield",
                "name": "일간 수율 리포트",
                "description": "일일 수율 현황, 장비별 성능, 이벤트 요약",
                "default_period": "1 day",
                "available_formats": ["json", "csv", "html"]
            },
            {
                "type": "weekly_performance",
                "name": "주간 성과 요약",
                "description": "주간 생산/품질 KPI, 트렌드 분석, 액션 아이템",
                "default_period": "7 days",
                "available_formats": ["json", "csv", "html"]
            },
            {
                "type": "monthly_executive",
                "name": "월간 경영진 대시보드",
                "description": "경영진용 종합 KPI, 재무 영향, 전략적 권장사항",
                "default_period": "30 days",
                "available_formats": ["json", "html"]
            },
            {
                "type": "supply_chain_risk",
                "name": "공급망 리스크 보고서",
                "description": "공급업체 현황, 리스크 분석, 완화 조치",
                "default_period": "7 days",
                "available_formats": ["json", "html"]
            },
            {
                "type": "audit_compliance",
                "name": "감사 컴플라이언스 보고서",
                "description": "접근 로그, 보안 이벤트, 컴플라이언스 상태",
                "default_period": "30 days",
                "available_formats": ["json", "csv"]
            }
        ]
    }


# ==================== Generate Reports ====================

@router.post("/generate")
def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    보고서 생성

    지정된 유형과 기간에 대한 보고서를 생성합니다.
    """
    generator = ReportGenerator(db)

    try:
        report = generator.generate_report(
            report_type=request.report_type,
            format=request.format,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # 감사 로그
        audit = AuditLogger(db)
        audit.log(
            user_id=0,
            user_role="system",
            action="GENERATE_REPORT",
            resource="report",
            resource_id=report.get("report_id", request.report_type),
            details={"report_type": request.report_type, "format": request.format}
        )

        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/generate/{report_type}")
def generate_report_get(
    report_type: str,
    format: str = Query(default="json", regex="^(json|csv|html)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    보고서 생성 (GET)

    URL 파라미터로 보고서 생성
    """
    generator = ReportGenerator(db)

    try:
        report = generator.generate_report(
            report_type=report_type,
            format=format,
            start_date=start_date,
            end_date=end_date
        )

        # CSV/HTML 포맷은 직접 컨텐츠 반환
        if format == "csv":
            return Response(
                content=report["content"],
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={report['filename']}"}
            )
        elif format == "html":
            return Response(
                content=report["content"],
                media_type="text/html"
            )

        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Quick Reports ====================

@router.get("/daily-yield")
def get_daily_yield_report(
    format: str = Query(default="json", regex="^(json|csv|html)$"),
    db: Session = Depends(get_db)
):
    """일간 수율 리포트 (오늘)"""
    generator = ReportGenerator(db)
    return generator.generate_report("daily_yield", format=format)


@router.get("/weekly-performance")
def get_weekly_performance_report(
    format: str = Query(default="json", regex="^(json|csv|html)$"),
    db: Session = Depends(get_db)
):
    """주간 성과 요약 (이번 주)"""
    generator = ReportGenerator(db)
    return generator.generate_report("weekly_performance", format=format)


@router.get("/monthly-executive")
def get_monthly_executive_report(
    format: str = Query(default="json", regex="^(json|html)$"),
    db: Session = Depends(get_db)
):
    """월간 경영진 대시보드 (이번 달)"""
    generator = ReportGenerator(db)
    return generator.generate_report("monthly_executive", format=format)


@router.get("/supply-risk")
def get_supply_risk_report(
    format: str = Query(default="json", regex="^(json|html)$"),
    db: Session = Depends(get_db)
):
    """공급망 리스크 보고서"""
    generator = ReportGenerator(db)
    return generator.generate_report("supply_chain_risk", format=format)


@router.get("/audit-compliance")
def get_audit_compliance_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = Query(default="json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """감사 컴플라이언스 보고서"""
    generator = ReportGenerator(db)
    return generator.generate_report(
        "audit_compliance",
        format=format,
        start_date=start_date,
        end_date=end_date
    )


# ==================== Scheduled Reports ====================

@router.get("/schedules")
def get_scheduled_reports(db: Session = Depends(get_db)):
    """스케줄된 보고서 목록"""
    manager = ScheduledReportManager(db)
    return {
        "schedules": manager.get_scheduled_reports()
    }


@router.post("/schedules")
def create_scheduled_report(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db)
):
    """보고서 스케줄 생성"""
    # 실제 구현 시 APScheduler 또는 Celery Beat 사용
    return {
        "message": "Schedule created",
        "schedule_id": f"SCH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "report_type": schedule.report_type,
        "schedule": schedule.schedule,
        "format": schedule.format,
        "recipients": schedule.recipients
    }


# ==================== Export ====================

@router.get("/export/{report_type}/{format}")
def export_report(
    report_type: str,
    format: str,
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    보고서 내보내기

    지정된 포맷으로 보고서를 다운로드합니다.
    """
    generator = ReportGenerator(db)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    try:
        report = generator.generate_report(
            report_type=report_type,
            format=format,
            start_date=start_date,
            end_date=end_date
        )

        if format == "csv":
            return Response(
                content=report["content"],
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={report['filename']}"
                }
            )
        elif format == "html":
            return Response(
                content=report["content"],
                media_type="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename={report['filename']}"
                }
            )
        else:
            return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
