from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .database import engine, Base, SessionLocal
from .api import api_router

settings = get_settings()


def init_security_defaults():
    """Initialize default roles, policies, and masking rules"""
    try:
        from .services.access_control import (
            initialize_default_roles,
            initialize_default_policies
        )
        from .services.data_masking import initialize_default_masking_rules

        db = SessionLocal()
        try:
            initialize_default_roles(db)
            initialize_default_policies(db)
            initialize_default_masking_rules(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Warning: Could not initialize security defaults: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    # Initialize security defaults
    init_security_defaults()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## HySpace API

    AI 기반 반도체 로드맵 설계 및 Fab 디지털 트윈 플랫폼의 백엔드 API입니다.

    ### 주요 기능

    * **PPA 시뮬레이션**: 칩 구성에 따른 전력, 성능, 면적 계산
    * **비용 시뮬레이션**: 제조 비용 및 수익성 분석
    * **워크로드 분석**: AI 워크로드 기반 최적 아키텍처 추천
    * **수율 관리**: 실시간 수율 모니터링 및 근본 원인 분석 (RCA)
    * **보안 거버넌스**: RBAC/ABAC 접근 제어 및 감사 로그

    ### API 카테고리

    * `/api/simulate/*` - PPA/비용 시뮬레이션
    * `/api/workload/*` - 워크로드 분석
    * `/api/yield/*` - 수율 관리 및 RCA
    * `/api/security/*` - 접근 제어 및 감사
    * `/api/reference/*` - 참조 데이터
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
