# Silicon Nexus (HySpace) Documentation

## Overview

Silicon Nexus(HySpace)는 반도체 Fab 운영을 위한 엔터프라이즈급 디지털 트윈 플랫폼입니다.
Palantir Foundry 수준의 데이터 통합, 분석, 시각화 역량을 목표로 설계되었습니다.

---

## Documentation Index

| 문서 | 설명 |
|------|------|
| [Architecture](./ARCHITECTURE.md) | 시스템 아키텍처 및 기술 스택 |
| [API Reference](./API_REFERENCE.md) | REST API 및 WebSocket 엔드포인트 |
| [Phase Implementation](./PHASE_IMPLEMENTATION.md) | 단계별 구현 상세 |
| [Future Roadmap](./FUTURE_ROADMAP.md) | 향후 고도화 방향 |
| [Development Guide](./DEVELOPMENT_GUIDE.md) | 개발 환경 설정 및 가이드 |

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database migration
alembic upgrade head

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **WebSocket**: ws://localhost:8000/api/ws

---

## Project Structure

```
silicon-nexus/
├── backend/
│   ├── app/
│   │   ├── api/              # REST API endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   ├── schemas/          # Pydantic schemas
│   │   └── main.py           # FastAPI application
│   ├── alembic/              # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API clients
│   │   └── types/            # TypeScript types
│   └── package.json
└── docs/                     # Documentation
```

---

## Core Features

### Phase 1: Foundation
- PPA (Performance, Power, Area) 최적화 시뮬레이션
- 공정 노드 및 IP 라이브러리 관리

### Phase 2: Enterprise Platform
- **Workload Analyzer**: AI/ML 워크로드 분석 및 아키텍처 추천
- **Yield Management**: 수율 분석 및 근본 원인 분석 (RCA)
- **Virtual Fab**: 디지털 트윈 시뮬레이션
- **Supply Chain**: Tier-N 공급망 가시성 및 리스크 관리
- **Security & Governance**: RBAC/ABAC 접근 제어, 감사 로그

### Phase 3: Advanced Analytics
- **Notification System**: 다채널 알림 및 에스컬레이션
- **Report Generation**: 자동 보고서 생성 (JSON, CSV, HTML)
- **Predictive Analytics**: ML 기반 수율/장비/수요 예측
- **Real-time Dashboard**: WebSocket 기반 실시간 모니터링

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, Alembic |
| Frontend | React, TypeScript, Vite, Recharts |
| Database | PostgreSQL, (planned: TimescaleDB, Neo4j) |
| Real-time | WebSocket |
| ML/AI | Simulated (planned: scikit-learn, XGBoost, Prophet) |

---

## License

Proprietary - All rights reserved
