from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import engine, Base
from .api import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## HySpace API

    AI 기반 반도체 로드맵 설계 플랫폼의 백엔드 API입니다.

    ### 주요 기능

    * **PPA 시뮬레이션**: 칩 구성에 따른 전력, 성능, 면적 계산
    * **비용 시뮬레이션**: 제조 비용 및 수익성 분석
    * **통합 시뮬레이션**: PPA와 비용을 동시에 분석
    * **참조 데이터**: 공정 노드 및 IP 라이브러리 조회

    ### 사용 예시

    1. `/api/reference/process-nodes`에서 지원 공정 확인
    2. `/api/simulate/ppa`로 칩 구성의 PPA 계산
    3. `/api/simulate/cost`로 제조 비용 계산
    4. `/api/simulate/full`로 종합 시뮬레이션 수행
    """,
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
