"""
Real-time Service

실시간 데이터 스트리밍 및 WebSocket 관리
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import random
import uuid

from fastapi import WebSocket
from sqlalchemy.orm import Session


class StreamType(str, Enum):
    YIELD_UPDATE = "yield_update"
    EQUIPMENT_STATUS = "equipment_status"
    WIP_MOVEMENT = "wip_movement"
    ALERT = "alert"
    METRICS = "metrics"
    HEARTBEAT = "heartbeat"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


@dataclass
class StreamMessage:
    """실시간 스트림 메시지"""
    message_id: str
    stream_type: StreamType
    timestamp: datetime
    data: dict
    priority: int = 0  # 0=normal, 1=high, 2=critical

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "stream_type": self.stream_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "priority": self.priority
        }


@dataclass
class ClientConnection:
    """클라이언트 연결 정보"""
    connection_id: str
    websocket: WebSocket
    subscriptions: set[StreamType] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


class ConnectionManager:
    """
    WebSocket 연결 관리자

    클라이언트 연결 관리, 메시지 브로드캐스트
    """

    def __init__(self):
        self._connections: dict[str, ClientConnection] = {}
        self._subscription_map: dict[StreamType, set[str]] = {
            stream_type: set() for stream_type in StreamType
        }

    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
        subscriptions: Optional[list[str]] = None
    ) -> ClientConnection:
        """새 클라이언트 연결"""
        await websocket.accept()

        connection_id = client_id or f"client-{uuid.uuid4().hex[:8]}"

        # 기본 구독: 모든 스트림
        subs = set()
        if subscriptions:
            for sub in subscriptions:
                try:
                    subs.add(StreamType(sub))
                except ValueError:
                    pass
        else:
            subs = set(StreamType)

        connection = ClientConnection(
            connection_id=connection_id,
            websocket=websocket,
            subscriptions=subs
        )

        self._connections[connection_id] = connection

        # 구독 맵 업데이트
        for stream_type in subs:
            self._subscription_map[stream_type].add(connection_id)

        # 연결 확인 메시지 전송
        await self._send_to_connection(connection, StreamMessage(
            message_id=f"conn-{uuid.uuid4().hex[:8]}",
            stream_type=StreamType.HEARTBEAT,
            timestamp=datetime.utcnow(),
            data={
                "status": "connected",
                "connection_id": connection_id,
                "subscriptions": [s.value for s in subs]
            }
        ))

        return connection

    async def disconnect(self, connection_id: str):
        """클라이언트 연결 해제"""
        if connection_id in self._connections:
            connection = self._connections[connection_id]

            # 구독 맵에서 제거
            for stream_type in connection.subscriptions:
                self._subscription_map[stream_type].discard(connection_id)

            del self._connections[connection_id]

    async def subscribe(self, connection_id: str, stream_types: list[StreamType]):
        """스트림 구독 추가"""
        if connection_id in self._connections:
            connection = self._connections[connection_id]
            for stream_type in stream_types:
                connection.subscriptions.add(stream_type)
                self._subscription_map[stream_type].add(connection_id)

    async def unsubscribe(self, connection_id: str, stream_types: list[StreamType]):
        """스트림 구독 해제"""
        if connection_id in self._connections:
            connection = self._connections[connection_id]
            for stream_type in stream_types:
                connection.subscriptions.discard(stream_type)
                self._subscription_map[stream_type].discard(connection_id)

    async def broadcast(self, message: StreamMessage):
        """특정 스트림 구독자에게 브로드캐스트"""
        subscriber_ids = self._subscription_map.get(message.stream_type, set())

        disconnected = []
        for conn_id in subscriber_ids:
            if conn_id in self._connections:
                try:
                    await self._send_to_connection(
                        self._connections[conn_id],
                        message
                    )
                except Exception:
                    disconnected.append(conn_id)

        # 실패한 연결 정리
        for conn_id in disconnected:
            await self.disconnect(conn_id)

    async def broadcast_all(self, message: StreamMessage):
        """모든 연결에 브로드캐스트"""
        disconnected = []
        for conn_id, connection in self._connections.items():
            try:
                await self._send_to_connection(connection, message)
            except Exception:
                disconnected.append(conn_id)

        for conn_id in disconnected:
            await self.disconnect(conn_id)

    async def send_to_client(self, connection_id: str, message: StreamMessage):
        """특정 클라이언트에 메시지 전송"""
        if connection_id in self._connections:
            try:
                await self._send_to_connection(
                    self._connections[connection_id],
                    message
                )
            except Exception:
                await self.disconnect(connection_id)

    async def _send_to_connection(self, connection: ClientConnection, message: StreamMessage):
        """연결에 메시지 전송"""
        await connection.websocket.send_json(message.to_dict())
        connection.last_message_at = datetime.utcnow()

    def get_connection_count(self) -> int:
        """현재 연결 수"""
        return len(self._connections)

    def get_connections_info(self) -> list[dict]:
        """모든 연결 정보"""
        return [
            {
                "connection_id": conn.connection_id,
                "connected_at": conn.connected_at.isoformat(),
                "last_message_at": conn.last_message_at.isoformat() if conn.last_message_at else None,
                "subscriptions": [s.value for s in conn.subscriptions]
            }
            for conn in self._connections.values()
        ]


class RealTimeDataService:
    """
    실시간 데이터 서비스

    시뮬레이션된 실시간 데이터 생성 및 스트리밍
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._is_streaming = False
        self._stream_task: Optional[asyncio.Task] = None

    async def start_streaming(
        self,
        connection_manager: ConnectionManager,
        interval_seconds: float = 1.0
    ):
        """실시간 스트리밍 시작"""
        self._is_streaming = True

        while self._is_streaming:
            try:
                # 수율 업데이트
                yield_message = self._generate_yield_update()
                await connection_manager.broadcast(yield_message)

                # 장비 상태 업데이트 (5초마다)
                if random.random() < 0.2:
                    equipment_message = self._generate_equipment_status()
                    await connection_manager.broadcast(equipment_message)

                # WIP 이동 업데이트 (3초마다)
                if random.random() < 0.33:
                    wip_message = self._generate_wip_movement()
                    await connection_manager.broadcast(wip_message)

                # 알림 (랜덤하게)
                if random.random() < 0.05:
                    alert_message = self._generate_alert()
                    await connection_manager.broadcast(alert_message)

                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Streaming error: {e}")
                await asyncio.sleep(1)

    def stop_streaming(self):
        """스트리밍 중지"""
        self._is_streaming = False

    def _generate_yield_update(self) -> StreamMessage:
        """수율 업데이트 생성"""
        base_yield = 91.5
        variation = random.gauss(0, 1.5)
        current_yield = max(75, min(99, base_yield + variation))

        return StreamMessage(
            message_id=f"yield-{uuid.uuid4().hex[:8]}",
            stream_type=StreamType.YIELD_UPDATE,
            timestamp=datetime.utcnow(),
            data={
                "current_yield": round(current_yield, 2),
                "target_yield": 92.0,
                "delta": round(current_yield - 92.0, 2),
                "trend": "up" if variation > 0 else "down",
                "process_step": random.choice(["LITHO", "ETCH", "CVD", "CMP", "IMPLANT"]),
                "lot_id": f"LOT-{random.randint(1000, 9999)}",
                "wafer_count": random.randint(20, 25)
            }
        )

    def _generate_equipment_status(self) -> StreamMessage:
        """장비 상태 업데이트 생성"""
        equipment_id = f"EQ-{random.choice(['LITHO', 'ETCH', 'CVD', 'CMP'])}-{random.randint(1, 5)}"
        status = random.choices(
            ["RUNNING", "IDLE", "MAINTENANCE", "DOWN"],
            weights=[0.7, 0.15, 0.1, 0.05]
        )[0]

        priority = 2 if status == "DOWN" else (1 if status == "MAINTENANCE" else 0)

        oee = random.uniform(75, 95) if status == "RUNNING" else 0

        return StreamMessage(
            message_id=f"equip-{uuid.uuid4().hex[:8]}",
            stream_type=StreamType.EQUIPMENT_STATUS,
            timestamp=datetime.utcnow(),
            data={
                "equipment_id": equipment_id,
                "status": status,
                "previous_status": random.choice(["RUNNING", "IDLE"]),
                "oee": round(oee, 1),
                "temperature": round(random.uniform(20, 30), 1),
                "utilization": round(random.uniform(60, 95), 1),
                "wip_in_queue": random.randint(0, 10),
                "estimated_completion": (datetime.utcnow() + timedelta(minutes=random.randint(5, 60))).isoformat()
            },
            priority=priority
        )

    def _generate_wip_movement(self) -> StreamMessage:
        """WIP 이동 업데이트 생성"""
        lot_id = f"LOT-{random.randint(1000, 9999)}"
        steps = ["FAB_IN", "LITHO", "ETCH", "CVD", "CMP", "IMPLANT", "METAL", "TEST", "FAB_OUT"]
        from_step = random.choice(steps[:-1])
        from_idx = steps.index(from_step)
        to_step = steps[from_idx + 1]

        return StreamMessage(
            message_id=f"wip-{uuid.uuid4().hex[:8]}",
            stream_type=StreamType.WIP_MOVEMENT,
            timestamp=datetime.utcnow(),
            data={
                "lot_id": lot_id,
                "wafer_count": random.randint(20, 25),
                "from_step": from_step,
                "to_step": to_step,
                "from_equipment": f"EQ-{from_step}-{random.randint(1, 3)}",
                "to_equipment": f"EQ-{to_step}-{random.randint(1, 3)}",
                "priority": random.choice(["NORMAL", "HIGH", "URGENT"]),
                "progress": round((from_idx + 1) / len(steps) * 100, 1),
                "estimated_completion": (datetime.utcnow() + timedelta(hours=random.randint(12, 72))).isoformat()
            }
        )

    def _generate_alert(self) -> StreamMessage:
        """알림 생성"""
        alert_types = [
            {
                "title": "수율 저하 감지",
                "severity": "WARNING",
                "category": "YIELD",
                "message": "Line A 수율이 목표치 대비 3% 하락"
            },
            {
                "title": "장비 이상 감지",
                "severity": "ERROR",
                "category": "EQUIPMENT",
                "message": "LITHO-3 진동 수준 임계치 초과"
            },
            {
                "title": "재고 부족 경고",
                "severity": "WARNING",
                "category": "SUPPLY",
                "message": "ArF 레지스트 재고 2주분 미만"
            },
            {
                "title": "긴급 유지보수 필요",
                "severity": "CRITICAL",
                "category": "MAINTENANCE",
                "message": "ETCH-2 PM 일정 초과 (7일)"
            },
            {
                "title": "품질 이상 탐지",
                "severity": "ERROR",
                "category": "QUALITY",
                "message": "Lot 2847 결함 밀도 이상"
            }
        ]

        alert = random.choice(alert_types)
        priority = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 2}.get(alert["severity"], 0)

        return StreamMessage(
            message_id=f"alert-{uuid.uuid4().hex[:8]}",
            stream_type=StreamType.ALERT,
            timestamp=datetime.utcnow(),
            data={
                "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
                **alert,
                "requires_action": alert["severity"] in ["ERROR", "CRITICAL"],
                "auto_escalate": alert["severity"] == "CRITICAL"
            },
            priority=priority
        )

    def generate_metrics_snapshot(self) -> StreamMessage:
        """현재 메트릭 스냅샷 생성"""
        return StreamMessage(
            message_id=f"metrics-{uuid.uuid4().hex[:8]}",
            stream_type=StreamType.METRICS,
            timestamp=datetime.utcnow(),
            data={
                "fab_metrics": {
                    "overall_yield": round(random.uniform(88, 95), 2),
                    "daily_output": random.randint(800, 1200),
                    "active_lots": random.randint(150, 250),
                    "equipment_utilization": round(random.uniform(75, 90), 1)
                },
                "equipment_summary": {
                    "total": 50,
                    "running": random.randint(40, 48),
                    "idle": random.randint(1, 5),
                    "maintenance": random.randint(1, 3),
                    "down": random.randint(0, 2)
                },
                "wip_summary": {
                    "total_lots": random.randint(150, 250),
                    "total_wafers": random.randint(3500, 6000),
                    "on_schedule": round(random.uniform(85, 98), 1),
                    "at_risk": random.randint(2, 15)
                },
                "alerts_summary": {
                    "critical": random.randint(0, 2),
                    "error": random.randint(0, 5),
                    "warning": random.randint(2, 10),
                    "info": random.randint(5, 20)
                }
            }
        )


# 싱글톤 인스턴스
connection_manager = ConnectionManager()
realtime_service = RealTimeDataService()
