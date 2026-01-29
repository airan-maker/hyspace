# Silicon Nexus

AI 기반 차세대 반도체 로드맵 설계 플랫폼

## Overview

Silicon Nexus는 반도체 칩 설계의 **PPA(Power, Performance, Area)** 트레이드오프와 **제조 비용**을 실시간으로 시뮬레이션하는 플랫폼입니다.

### 핵심 기능

- **PPA Optimizer**: 칩 구성(코어 수, 캐시, 공정 노드 등)에 따른 다이 면적, 전력, 성능 시뮬레이션
- **Cost Simulator**: 수율, 웨이퍼 비용, 패키징 비용을 고려한 제조 단가 및 수익성 분석
- **Alternative Comparison**: 저전력/고성능 대안 구성 자동 제안

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI + SQLAlchemy + Pydantic |
| Database | PostgreSQL |
| Container | Docker + Docker Compose |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (로컬 개발 시)
- Python 3.11+ (로컬 개발 시)

### Docker로 실행 (권장)

```bash
# 프로젝트 클론
cd silicon-nexus

# Docker Compose로 전체 스택 실행
docker-compose up -d

# 접속
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 로컬 개발 환경

#### 1. PostgreSQL 실행

```bash
docker-compose up -d db
```

#### 2. Backend 실행

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env

# 서버 실행
uvicorn app.main:app --reload
```

#### 3. Frontend 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## Project Structure

```
silicon-nexus/
├── backend/
│   ├── app/
│   │   ├── api/              # API 라우터
│   │   ├── models/           # SQLAlchemy 모델
│   │   ├── schemas/          # Pydantic 스키마
│   │   ├── services/         # 비즈니스 로직
│   │   │   ├── ppa_engine.py      # PPA 계산 엔진
│   │   │   ├── cost_simulator.py  # 비용 시뮬레이터
│   │   │   └── yield_model.py     # 수율 모델
│   │   └── main.py           # FastAPI 앱
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React 컴포넌트
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API 클라이언트
│   │   └── types/            # TypeScript 타입
│   └── package.json
├── docker-compose.yml
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/simulate/ppa` | PPA 시뮬레이션 |
| POST | `/api/simulate/ppa/alternatives` | 대안 구성 비교 |
| POST | `/api/simulate/cost` | 비용 시뮬레이션 |
| POST | `/api/simulate/full` | 통합 시뮬레이션 (PPA + 비용) |
| GET | `/api/reference/process-nodes` | 공정 노드 목록 |
| GET | `/api/reference/ip-library` | IP 라이브러리 |

## Core Algorithms

### Die Size Calculation

```
die_size = core_area + cache_area + io_area + overhead

where:
  core_area = base_core_area × num_cores × scaling_factor
  cache_area = cache_size × cache_density
  overhead = functional_area × 0.15  (routing/padding)
```

### Murphy's Yield Model

```
yield = ((1 - exp(-A×D)) / (A×D))²

where:
  A = die area (cm²)
  D = defect density (defects/cm²)
```

### Cost Breakdown

```
total_cost = good_die_cost + package_cost + test_cost

where:
  good_die_cost = (wafer_cost / gross_die) / yield_rate
```

## Configuration Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| Process Node | 3nm, 5nm, 7nm | 반도체 공정 노드 |
| CPU Cores | 2-32 | CPU 코어 수 |
| GPU Cores | 0-64 | GPU 코어 수 |
| NPU Cores | 0-32 | NPU 코어 수 |
| L2 Cache | 2-32 MB | L2 캐시 용량 |
| L3 Cache | 0-128 MB | L3 캐시 용량 |
| Target Frequency | 1.5-4.5 GHz | 목표 동작 주파수 |
| PCIe Lanes | 8-64 | PCIe 레인 수 |
| Memory Channels | 1-8 | 메모리 채널 수 |

## Sample Simulation

**Input Configuration:**
- Process: 5nm
- CPU Cores: 8
- GPU Cores: 16
- NPU Cores: 4
- L2 Cache: 8 MB
- L3 Cache: 32 MB
- Target Frequency: 3.2 GHz

**Expected Results:**
- Die Size: ~85 mm²
- TDP: ~55 W
- AI Performance: 32 TOPS
- Unit Cost: ~$45
- Gross Margin: ~50% (at $89 ASP)

## License

MIT License
