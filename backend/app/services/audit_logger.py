"""
Audit Logger Service

감사 로그 기록 및 조회 서비스
Palantir-grade Audit Trail
"""

from datetime import datetime, timedelta
from typing import Optional, Any
import json
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.security import AuditLog


class AuditLogger:
    """
    감사 로그 서비스

    기능:
    - 모든 데이터 접근/수정 기록
    - 사용자 활동 추적
    - 보안 이벤트 기록
    - 컴플라이언스 보고서 생성
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== 로그 기록 ====================

    def log(
        self,
        user_id: int,
        user_role: str,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        result: str = "SUCCESS",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        감사 로그 기록

        Args:
            user_id: 사용자 ID
            user_role: 사용자 역할
            action: 수행 동작 (VIEW, EDIT, DELETE, LOGIN, EXPORT, etc.)
            resource: 리소스 유형 (yield_events, equipment, etc.)
            resource_id: 특정 리소스 ID (선택)
            result: 결과 (SUCCESS, DENIED, ERROR)
            ip_address: 클라이언트 IP
            user_agent: 브라우저/클라이언트 정보
            details: 추가 상세 정보
        """
        import uuid

        log_entry = AuditLog(
            log_id=f"LOG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_role=user_role,
            action=action,
            resource=resource,
            resource_id=resource_id,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)

        return log_entry

    def log_view(
        self,
        user_id: int,
        user_role: str,
        resource: str,
        resource_id: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """VIEW 액션 로그"""
        return self.log(
            user_id=user_id,
            user_role=user_role,
            action="VIEW",
            resource=resource,
            resource_id=resource_id,
            **kwargs
        )

    def log_edit(
        self,
        user_id: int,
        user_role: str,
        resource: str,
        resource_id: str,
        old_value: Any = None,
        new_value: Any = None,
        **kwargs
    ) -> AuditLog:
        """EDIT 액션 로그"""
        details = kwargs.get("details", {})
        if old_value is not None:
            details["old_value"] = self._serialize_value(old_value)
        if new_value is not None:
            details["new_value"] = self._serialize_value(new_value)

        return self.log(
            user_id=user_id,
            user_role=user_role,
            action="EDIT",
            resource=resource,
            resource_id=resource_id,
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )

    def log_delete(
        self,
        user_id: int,
        user_role: str,
        resource: str,
        resource_id: str,
        deleted_data: Any = None,
        **kwargs
    ) -> AuditLog:
        """DELETE 액션 로그"""
        details = kwargs.get("details", {})
        if deleted_data is not None:
            details["deleted_data"] = self._serialize_value(deleted_data)

        return self.log(
            user_id=user_id,
            user_role=user_role,
            action="DELETE",
            resource=resource,
            resource_id=resource_id,
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )

    def log_export(
        self,
        user_id: int,
        user_role: str,
        resource: str,
        export_format: str,
        record_count: int,
        **kwargs
    ) -> AuditLog:
        """EXPORT 액션 로그"""
        details = kwargs.get("details", {})
        details["export_format"] = export_format
        details["record_count"] = record_count

        return self.log(
            user_id=user_id,
            user_role=user_role,
            action="EXPORT",
            resource=resource,
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )

    def log_login(
        self,
        user_id: int,
        result: str = "SUCCESS",
        failure_reason: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """LOGIN 이벤트 로그"""
        details = kwargs.get("details", {})
        if failure_reason:
            details["failure_reason"] = failure_reason

        return self.log(
            user_id=user_id,
            user_role="N/A",
            action="LOGIN",
            resource="auth",
            result=result,
            details=details if details else None,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )

    def log_logout(self, user_id: int, user_role: str, **kwargs) -> AuditLog:
        """LOGOUT 이벤트 로그"""
        return self.log(
            user_id=user_id,
            user_role=user_role,
            action="LOGOUT",
            resource="auth",
            **kwargs
        )

    def log_access_denied(
        self,
        user_id: int,
        user_role: str,
        resource: str,
        reason: str,
        **kwargs
    ) -> AuditLog:
        """접근 거부 로그"""
        details = kwargs.get("details", {})
        details["denial_reason"] = reason

        return self.log(
            user_id=user_id,
            user_role=user_role,
            action="ACCESS_DENIED",
            resource=resource,
            result="DENIED",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: Optional[int] = None,
        **kwargs
    ) -> AuditLog:
        """보안 이벤트 로그"""
        details = kwargs.get("details", {})
        details["event_type"] = event_type
        details["severity"] = severity
        details["description"] = description

        return self.log(
            user_id=user_id or 0,
            user_role="SYSTEM",
            action="SECURITY_EVENT",
            resource="security",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )

    def _serialize_value(self, value: Any) -> Any:
        """값을 JSON 직렬화 가능한 형태로 변환"""
        if hasattr(value, "__dict__"):
            return {k: str(v) for k, v in value.__dict__.items() if not k.startswith("_")}
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (list, dict)):
            return value
        else:
            return str(value)

    # ==================== 로그 조회 ====================

    def get_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        result: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """감사 로그 조회"""
        query = self.db.query(AuditLog)

        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource:
            query = query.filter(AuditLog.resource == resource)
        if result:
            query = query.filter(AuditLog.result == result)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        return query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()

    def get_user_activity(
        self,
        user_id: int,
        days: int = 30
    ) -> list[AuditLog]:
        """특정 사용자의 활동 로그"""
        start_date = datetime.utcnow() - timedelta(days=days)

        return self.db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= start_date
            )
        ).order_by(desc(AuditLog.timestamp)).all()

    def get_resource_history(
        self,
        resource: str,
        resource_id: str,
        limit: int = 50
    ) -> list[AuditLog]:
        """특정 리소스의 변경 이력"""
        return self.db.query(AuditLog).filter(
            and_(
                AuditLog.resource == resource,
                AuditLog.resource_id == resource_id
            )
        ).order_by(desc(AuditLog.timestamp)).limit(limit).all()

    def get_security_events(
        self,
        severity: Optional[str] = None,
        days: int = 7
    ) -> list[AuditLog]:
        """보안 이벤트 조회"""
        start_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(AuditLog).filter(
            and_(
                AuditLog.action == "SECURITY_EVENT",
                AuditLog.timestamp >= start_date
            )
        )

        if severity:
            # details JSON 필드에서 severity 필터링
            # PostgreSQL jsonb 연산자 사용 가능
            pass

        return query.order_by(desc(AuditLog.timestamp)).all()

    def get_failed_logins(
        self,
        hours: int = 24
    ) -> list[AuditLog]:
        """실패한 로그인 시도 조회"""
        start_date = datetime.utcnow() - timedelta(hours=hours)

        return self.db.query(AuditLog).filter(
            and_(
                AuditLog.action == "LOGIN",
                AuditLog.result != "SUCCESS",
                AuditLog.timestamp >= start_date
            )
        ).order_by(desc(AuditLog.timestamp)).all()

    def get_denied_accesses(
        self,
        hours: int = 24
    ) -> list[AuditLog]:
        """접근 거부 이력 조회"""
        start_date = datetime.utcnow() - timedelta(hours=hours)

        return self.db.query(AuditLog).filter(
            and_(
                AuditLog.result == "DENIED",
                AuditLog.timestamp >= start_date
            )
        ).order_by(desc(AuditLog.timestamp)).all()

    # ==================== 통계 및 분석 ====================

    def get_activity_summary(
        self,
        days: int = 30
    ) -> dict:
        """활동 요약 통계"""
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = self.db.query(AuditLog).filter(
            AuditLog.timestamp >= start_date
        ).all()

        # 액션별 집계
        action_counts = {}
        user_counts = {}
        resource_counts = {}
        result_counts = {"SUCCESS": 0, "DENIED": 0, "ERROR": 0}

        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
            user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1
            resource_counts[log.resource] = resource_counts.get(log.resource, 0) + 1
            if log.result in result_counts:
                result_counts[log.result] += 1

        return {
            "period_days": days,
            "total_events": len(logs),
            "by_action": action_counts,
            "by_result": result_counts,
            "unique_users": len(user_counts),
            "most_active_users": sorted(
                user_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "most_accessed_resources": sorted(
                resource_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def get_daily_trend(
        self,
        days: int = 30
    ) -> list[dict]:
        """일별 활동 트렌드"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 일별 집계 (실제로는 DB 집계 함수 사용)
        logs = self.db.query(AuditLog).filter(
            AuditLog.timestamp >= start_date
        ).all()

        daily_counts = {}
        for log in logs:
            date_key = log.timestamp.strftime("%Y-%m-%d")
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

        trend = []
        current = start_date
        while current <= end_date:
            date_key = current.strftime("%Y-%m-%d")
            trend.append({
                "date": date_key,
                "count": daily_counts.get(date_key, 0)
            })
            current += timedelta(days=1)

        return trend

    # ==================== 보고서 생성 ====================

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "full"
    ) -> dict:
        """컴플라이언스 보고서 생성"""
        logs = self.db.query(AuditLog).filter(
            AuditLog.timestamp.between(start_date, end_date)
        ).all()

        report = {
            "report_type": report_type,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_events": len(logs),
                "successful_operations": len([l for l in logs if l.result == "SUCCESS"]),
                "denied_accesses": len([l for l in logs if l.result == "DENIED"]),
                "errors": len([l for l in logs if l.result == "ERROR"])
            },
            "security_incidents": [],
            "data_exports": [],
            "privileged_operations": []
        }

        # 보안 인시던트
        for log in logs:
            if log.action == "SECURITY_EVENT":
                report["security_incidents"].append({
                    "timestamp": log.timestamp.isoformat(),
                    "details": log.details
                })

            # 데이터 내보내기
            if log.action == "EXPORT":
                report["data_exports"].append({
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "resource": log.resource,
                    "details": log.details
                })

            # 권한 있는 작업 (DELETE, 관리자 작업)
            if log.action in ["DELETE", "ADMIN_ACTION"] or log.user_role == "admin":
                report["privileged_operations"].append({
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id
                })

        return report

    def export_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """감사 로그 내보내기"""
        logs = self.get_logs(start_date=start_date, end_date=end_date, limit=10000)

        if format == "json":
            return json.dumps([
                {
                    "log_id": log.log_id,
                    "timestamp": log.timestamp.isoformat(),
                    "user_id": log.user_id,
                    "user_role": log.user_role,
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "result": log.result,
                    "ip_address": log.ip_address,
                    "details": log.details
                }
                for log in logs
            ], indent=2)

        elif format == "csv":
            lines = ["log_id,timestamp,user_id,user_role,action,resource,resource_id,result,ip_address"]
            for log in logs:
                lines.append(
                    f"{log.log_id},{log.timestamp.isoformat()},{log.user_id},{log.user_role},"
                    f"{log.action},{log.resource},{log.resource_id or ''},{log.result},{log.ip_address or ''}"
                )
            return "\n".join(lines)

        return ""
