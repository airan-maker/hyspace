"""
WebSocket API Endpoints

실시간 데이터 스트리밍 WebSocket 엔드포인트
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from sqlalchemy.orm import Session
import asyncio
import json

from app.database import get_db
from app.services.realtime import (
    connection_manager,
    realtime_service,
    StreamType,
    StreamMessage,
    RealTimeDataService
)


router = APIRouter(tags=["WebSocket"])


# ==================== WebSocket Endpoints ====================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(default=None),
    subscriptions: Optional[str] = Query(default=None)
):
    """
    실시간 데이터 WebSocket 연결

    Parameters:
    - client_id: 클라이언트 식별자 (선택)
    - subscriptions: 구독할 스트림 (콤마 구분, 선택)
      - yield_update: 수율 업데이트
      - equipment_status: 장비 상태
      - wip_movement: WIP 이동
      - alert: 알림
      - metrics: 메트릭 스냅샷
      - heartbeat: 하트비트

    Example:
    - ws://localhost:8000/api/ws?subscriptions=yield_update,alert
    """
    # 구독 파싱
    sub_list = None
    if subscriptions:
        sub_list = [s.strip() for s in subscriptions.split(",")]

    # 연결 수락
    connection = await connection_manager.connect(
        websocket=websocket,
        client_id=client_id,
        subscriptions=sub_list
    )

    try:
        # 초기 메트릭 스냅샷 전송
        initial_metrics = realtime_service.generate_metrics_snapshot()
        await connection_manager.send_to_client(
            connection.connection_id,
            initial_metrics
        )

        # 메시지 수신 대기
        while True:
            try:
                data = await websocket.receive_json()
                await handle_client_message(connection.connection_id, data)
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # 잘못된 JSON 무시
                pass

    finally:
        await connection_manager.disconnect(connection.connection_id)


@router.websocket("/ws/stream/{stream_type}")
async def stream_specific_endpoint(
    websocket: WebSocket,
    stream_type: str,
    client_id: Optional[str] = Query(default=None)
):
    """
    특정 스트림 전용 WebSocket 연결

    Path Parameters:
    - stream_type: 구독할 스트림 타입
    """
    try:
        valid_stream = StreamType(stream_type)
    except ValueError:
        await websocket.close(code=4000, reason=f"Invalid stream type: {stream_type}")
        return

    connection = await connection_manager.connect(
        websocket=websocket,
        client_id=client_id,
        subscriptions=[stream_type]
    )

    try:
        while True:
            try:
                data = await websocket.receive_json()
                await handle_client_message(connection.connection_id, data)
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                pass

    finally:
        await connection_manager.disconnect(connection.connection_id)


async def handle_client_message(connection_id: str, data: dict):
    """
    클라이언트 메시지 처리

    지원 명령:
    - subscribe: 스트림 구독
    - unsubscribe: 스트림 구독 해제
    - ping: 연결 확인
    - request_metrics: 메트릭 요청
    """
    action = data.get("action")

    if action == "subscribe":
        streams = data.get("streams", [])
        stream_types = []
        for s in streams:
            try:
                stream_types.append(StreamType(s))
            except ValueError:
                pass
        await connection_manager.subscribe(connection_id, stream_types)

        # 확인 메시지
        await connection_manager.send_to_client(
            connection_id,
            StreamMessage(
                message_id=f"sub-ack-{datetime.utcnow().timestamp()}",
                stream_type=StreamType.HEARTBEAT,
                timestamp=datetime.utcnow(),
                data={
                    "action": "subscribed",
                    "streams": [s.value for s in stream_types]
                }
            )
        )

    elif action == "unsubscribe":
        streams = data.get("streams", [])
        stream_types = []
        for s in streams:
            try:
                stream_types.append(StreamType(s))
            except ValueError:
                pass
        await connection_manager.unsubscribe(connection_id, stream_types)

        await connection_manager.send_to_client(
            connection_id,
            StreamMessage(
                message_id=f"unsub-ack-{datetime.utcnow().timestamp()}",
                stream_type=StreamType.HEARTBEAT,
                timestamp=datetime.utcnow(),
                data={
                    "action": "unsubscribed",
                    "streams": [s.value for s in stream_types]
                }
            )
        )

    elif action == "ping":
        await connection_manager.send_to_client(
            connection_id,
            StreamMessage(
                message_id=f"pong-{datetime.utcnow().timestamp()}",
                stream_type=StreamType.HEARTBEAT,
                timestamp=datetime.utcnow(),
                data={"action": "pong"}
            )
        )

    elif action == "request_metrics":
        metrics = realtime_service.generate_metrics_snapshot()
        await connection_manager.send_to_client(connection_id, metrics)


# ==================== REST Endpoints for WebSocket Management ====================

@router.get("/realtime/status")
def get_realtime_status():
    """실시간 서비스 상태"""
    return {
        "status": "active",
        "connection_count": connection_manager.get_connection_count(),
        "available_streams": [s.value for s in StreamType],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/realtime/connections")
def get_connections():
    """현재 연결 목록"""
    return {
        "count": connection_manager.get_connection_count(),
        "connections": connection_manager.get_connections_info()
    }


@router.post("/realtime/broadcast")
async def broadcast_message(
    stream_type: str,
    message: dict,
    priority: int = 0
):
    """
    관리자: 수동 브로드캐스트

    테스트 및 긴급 알림용
    """
    try:
        valid_stream = StreamType(stream_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stream type: {stream_type}")

    stream_message = StreamMessage(
        message_id=f"manual-{datetime.utcnow().timestamp()}",
        stream_type=valid_stream,
        timestamp=datetime.utcnow(),
        data=message,
        priority=priority
    )

    await connection_manager.broadcast(stream_message)

    return {
        "status": "broadcasted",
        "message_id": stream_message.message_id,
        "recipients": connection_manager.get_connection_count()
    }


@router.get("/realtime/metrics")
def get_current_metrics():
    """현재 메트릭 스냅샷 (REST)"""
    metrics = realtime_service.generate_metrics_snapshot()
    return metrics.to_dict()


# ==================== Streaming Control ====================

_streaming_task: Optional[asyncio.Task] = None


@router.post("/realtime/start-streaming")
async def start_streaming(interval: float = Query(default=1.0, ge=0.5, le=10.0)):
    """
    실시간 스트리밍 시작

    Parameters:
    - interval: 업데이트 간격 (초)
    """
    global _streaming_task

    if _streaming_task and not _streaming_task.done():
        return {"status": "already_running"}

    async def run_streaming():
        await realtime_service.start_streaming(
            connection_manager,
            interval_seconds=interval
        )

    _streaming_task = asyncio.create_task(run_streaming())

    return {
        "status": "started",
        "interval_seconds": interval
    }


@router.post("/realtime/stop-streaming")
def stop_streaming():
    """실시간 스트리밍 중지"""
    global _streaming_task

    realtime_service.stop_streaming()

    if _streaming_task:
        _streaming_task.cancel()
        _streaming_task = None

    return {"status": "stopped"}


# ==================== Demo Data Generation ====================

@router.post("/realtime/demo/generate-events")
async def generate_demo_events(count: int = Query(default=10, ge=1, le=100)):
    """
    데모: 테스트 이벤트 생성

    각 스트림 타입별로 이벤트 생성 후 브로드캐스트
    """
    import random

    generated = []

    for _ in range(count):
        event_type = random.choice([
            "yield", "equipment", "wip", "alert"
        ])

        if event_type == "yield":
            msg = realtime_service._generate_yield_update()
        elif event_type == "equipment":
            msg = realtime_service._generate_equipment_status()
        elif event_type == "wip":
            msg = realtime_service._generate_wip_movement()
        else:
            msg = realtime_service._generate_alert()

        await connection_manager.broadcast(msg)
        generated.append({
            "message_id": msg.message_id,
            "stream_type": msg.stream_type.value
        })

        await asyncio.sleep(0.1)  # 약간의 딜레이

    return {
        "generated_count": len(generated),
        "events": generated
    }


@router.post("/realtime/demo/simulate-alert")
async def simulate_alert(
    severity: str = Query(default="WARNING"),
    category: str = Query(default="YIELD"),
    title: str = Query(default="Test Alert"),
    message: str = Query(default="This is a test alert")
):
    """데모: 테스트 알림 생성"""
    import uuid

    alert_message = StreamMessage(
        message_id=f"alert-{uuid.uuid4().hex[:8]}",
        stream_type=StreamType.ALERT,
        timestamp=datetime.utcnow(),
        data={
            "alert_id": f"ALT-TEST-{uuid.uuid4().hex[:8].upper()}",
            "title": title,
            "message": message,
            "severity": severity,
            "category": category,
            "requires_action": severity in ["ERROR", "CRITICAL"],
            "auto_escalate": severity == "CRITICAL",
            "is_test": True
        },
        priority=2 if severity == "CRITICAL" else (1 if severity in ["ERROR", "WARNING"] else 0)
    )

    await connection_manager.broadcast(alert_message)

    return {
        "status": "broadcasted",
        "alert": alert_message.to_dict()
    }
