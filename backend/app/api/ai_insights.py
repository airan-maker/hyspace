"""
AI Insights API

그래프 쿼리 결과에 대한 AI 기반 분석을 생성합니다.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from ..services.ai_insight_service import generate_insight, generate_insight_stream

router = APIRouter(prefix="/graph")


class InsightRequest(BaseModel):
    query_type: str
    results: object
    context: Optional[str] = None


@router.post("/insight")
async def create_insight(request: InsightRequest):
    """쿼리 결과에 대한 AI 인사이트를 생성합니다."""
    try:
        insight = generate_insight(request.query_type, request.results)
        return {"insight": insight, "query_type": request.query_type}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 분석 생성 실패: {str(e)}")


@router.post("/insight/stream")
async def create_insight_stream(request: InsightRequest):
    """쿼리 결과에 대한 AI 인사이트를 SSE 스트리밍으로 생성합니다."""
    try:
        return StreamingResponse(
            generate_insight_stream(request.query_type, request.results),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 분석 스트림 실패: {str(e)}")
