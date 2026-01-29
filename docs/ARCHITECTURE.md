# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Silicon Nexus Platform                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          Frontend (React + TypeScript)                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │Dashboard │ │ Yield    │ │ Virtual  │ │ Supply   │ │ Reports  │      │   │
│  │  │          │ │ Analysis │ │ Fab      │ │ Chain    │ │          │      │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                          ┌───────────┴───────────┐                              │
│                          │   REST API / WebSocket │                              │
│                          └───────────┬───────────┘                              │
│                                      │                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          Backend (FastAPI)                               │   │
│  │                                                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                        API Layer                                 │   │   │
│  │  │  /simulate  /workload  /yield  /fab  /supply  /notifications    │   │   │
│  │  │  /security  /reports   /predictions  /ws                        │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  │                                  │                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                      Service Layer                               │   │   │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │   │   │
│  │  │  │YieldAnalyzer │ │VirtualFab    │ │SupplyChain   │             │   │   │
│  │  │  │RootCause     │ │Simulator     │ │RiskDetector  │             │   │   │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘             │   │   │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │   │   │
│  │  │  │Notification  │ │Prediction    │ │ReportGen     │             │   │   │
│  │  │  │Service       │ │Engine        │ │Engine        │             │   │   │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘             │   │   │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │   │   │
│  │  │  │AccessControl │ │AuditLogger   │ │DataMasking   │             │   │   │
│  │  │  │(RBAC/ABAC)   │ │              │ │              │             │   │   │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘             │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  │                                  │                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                       Data Layer                                 │   │   │
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │   │   │
│  │  │  │ SQLAlchemy   │ │ Models       │ │ Alembic      │             │   │   │
│  │  │  │ ORM          │ │              │ │ Migrations   │             │   │   │
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘             │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          Database Layer                                  │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │   │
│  │  │ PostgreSQL   │ │ TimescaleDB  │ │ Neo4j        │                    │   │
│  │  │ (Primary)    │ │ (Time-series)│ │ (Graph)      │                    │   │
│  │  │ [Active]     │ │ [Planned]    │ │ [Planned]    │                    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Domain Model Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Domain Models                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │  Yield Domain   │    │   Fab Domain    │    │ Supply Domain   │             │
│  ├─────────────────┤    ├─────────────────┤    ├─────────────────┤             │
│  │ • WaferRecord   │    │ • FabEquipment  │    │ • Supplier      │             │
│  │ • YieldEvent    │    │ • WIPItem       │    │ • Material      │             │
│  │ • Equipment     │    │ • Scenario      │    │ • SupplyRisk    │             │
│  │ • RootCause     │    │ • Bottleneck    │    │ • Inventory     │             │
│  └─────────────────┘    │ • Maintenance   │    │   Recommendation│             │
│                         └─────────────────┘    └─────────────────┘             │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ Security Domain │    │Notification Dom │    │ Workload Domain │             │
│  ├─────────────────┤    ├─────────────────┤    ├─────────────────┤             │
│  │ • User          │    │ • AlertRule     │    │ • WorkloadProfile│            │
│  │ • Role          │    │ • Alert         │    │ • ArchitectureRec│            │
│  │ • AccessPolicy  │    │ • Recipient     │    │ • Benchmark      │            │
│  │ • AuditLog      │    │ • NotifyLog     │    │                 │             │
│  │ • MaskingRule   │    │ • Channel       │    │                 │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Service Architecture

### 1. Yield Management Service

```
┌──────────────────────────────────────────────────────────────────┐
│                    Yield Management System                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input Sources                    Analysis Engine                │
│  ─────────────                    ───────────────                │
│  ┌──────────────┐                ┌──────────────────────────┐    │
│  │ Wafer Data   │───────────────▶│ YieldAnalyzer            │    │
│  │ Lot Data     │                │ • Trend Analysis         │    │
│  │ Equipment    │                │ • Statistical Analysis   │    │
│  │ Process Params│               │ • Correlation Engine     │    │
│  └──────────────┘                └───────────┬──────────────┘    │
│                                              │                    │
│                                              ▼                    │
│                                 ┌──────────────────────────┐     │
│                                 │ Root Cause Analyzer       │     │
│                                 │ • Multi-factor Analysis  │     │
│                                 │ • Temporal Correlation   │     │
│                                 │ • Equipment Variance     │     │
│                                 │ • Confidence Scoring     │     │
│                                 └───────────┬──────────────┘     │
│                                              │                    │
│                                              ▼                    │
│  Output                         ┌──────────────────────────┐     │
│  ──────                         │ Results                   │     │
│  • Yield Dashboard              │ • RCA Report             │     │
│  • Trend Charts                 │ • Corrective Actions     │     │
│  • Alert Triggers               │ • Confidence Score       │     │
│                                 └──────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

### 2. Virtual Fab Simulator

```
┌──────────────────────────────────────────────────────────────────┐
│                    Virtual Fab Digital Twin                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                 Discrete Event Simulation                 │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │    │
│  │  │Equipment│  │Equipment│  │Equipment│  │Equipment│     │    │
│  │  │ LITHO   │─▶│  ETCH   │─▶│  CVD    │─▶│  CMP    │     │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │    │
│  │       ▲                                       │          │    │
│  │       │           WIP Flow                    │          │    │
│  │       └───────────────────────────────────────┘          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                    │
│              ┌───────────────┼───────────────┐                   │
│              ▼               ▼               ▼                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│  │ Bottleneck   │ │ What-If      │ │ Maintenance  │              │
│  │ Predictor    │ │ Scenario     │ │ Optimizer    │              │
│  │              │ │ Engine       │ │              │              │
│  │ • Queue Depth│ │ • Equipment  │ │ • PM Schedule│              │
│  │ • Wait Time  │ │   Failure    │ │ • Downtime   │              │
│  │ • Throughput │ │ • Demand     │ │   Minimization│             │
│  └──────────────┘ │   Spike      │ └──────────────┘              │
│                   └──────────────┘                               │
└──────────────────────────────────────────────────────────────────┘
```

### 3. Predictive Analytics Engine

```
┌──────────────────────────────────────────────────────────────────┐
│                    Prediction Engine                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                     ML Models                             │    │
│  │                                                          │    │
│  │  ┌─────────────────┐  ┌─────────────────┐               │    │
│  │  │ Yield Prediction│  │ Equipment Failure│               │    │
│  │  │ Model           │  │ Model            │               │    │
│  │  │ ───────────────│  │ ────────────────│               │    │
│  │  │ • XGBoost sim  │  │ • LSTM sim       │               │    │
│  │  │ • Process params│ │ • Sensor data    │               │    │
│  │  │ • Environment  │  │ • Maintenance    │               │    │
│  │  │ Output: Yield % │  │ Output: P(fail) │               │    │
│  │  └─────────────────┘  └─────────────────┘               │    │
│  │                                                          │    │
│  │  ┌─────────────────┐  ┌─────────────────┐               │    │
│  │  │ Demand Forecast │  │ Anomaly Detection│               │    │
│  │  │ Model           │  │ Model            │               │    │
│  │  │ ───────────────│  │ ────────────────│               │    │
│  │  │ • Prophet sim  │  │ • Isolation Forest│              │    │
│  │  │ • Historical   │  │   sim            │               │    │
│  │  │ • Seasonality  │  │ • Z-score based  │               │    │
│  │  │ Output: Units  │  │ Output: Score    │               │    │
│  │  └─────────────────┘  └─────────────────┘               │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                    │
│                              ▼                                    │
│                   ┌──────────────────────┐                       │
│                   │ Integrated Insights   │                       │
│                   │ • Overall Health Score│                       │
│                   │ • Action Items        │                       │
│                   │ • Risk Summary        │                       │
│                   └──────────────────────┘                       │
└──────────────────────────────────────────────────────────────────┘
```

### 4. Real-time Streaming Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Real-time Data Flow                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Data Sources              Connection Manager      Clients       │
│  ────────────              ──────────────────      ───────       │
│                                                                  │
│  ┌──────────────┐         ┌──────────────────┐                   │
│  │ Yield Updates│────────▶│                  │   ┌───────────┐   │
│  │ (1s interval)│         │                  │──▶│ Dashboard │   │
│  └──────────────┘         │   WebSocket      │   └───────────┘   │
│                           │   Connection     │                   │
│  ┌──────────────┐         │   Manager        │   ┌───────────┐   │
│  │ Equipment    │────────▶│                  │──▶│ Mobile    │   │
│  │ Status       │         │  ┌────────────┐  │   └───────────┘   │
│  └──────────────┘         │  │Subscription│  │                   │
│                           │  │   Map      │  │   ┌───────────┐   │
│  ┌──────────────┐         │  └────────────┘  │──▶│ Alerting  │   │
│  │ WIP Movement │────────▶│                  │   │ System    │   │
│  └──────────────┘         │                  │   └───────────┘   │
│                           │                  │                   │
│  ┌──────────────┐         │                  │   ┌───────────┐   │
│  │ Alerts       │────────▶│                  │──▶│ External  │   │
│  │              │         │                  │   │ Systems   │   │
│  └──────────────┘         └──────────────────┘   └───────────┘   │
│                                                                  │
│  Stream Types:                                                   │
│  • yield_update      • equipment_status    • wip_movement        │
│  • alert             • metrics             • heartbeat           │
└──────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Security & Governance Layer                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                   Access Control                          │    │
│  │                                                          │    │
│  │  ┌─────────────────┐    ┌─────────────────┐             │    │
│  │  │      RBAC       │    │      ABAC       │             │    │
│  │  │ ───────────────│    │ ───────────────│             │    │
│  │  │ • Admin        │    │ • Time-based   │             │    │
│  │  │ • Engineer     │    │ • IP-based     │             │    │
│  │  │ • Operator     │    │ • Location     │             │    │
│  │  │ • Partner      │    │ • Contract     │             │    │
│  │  │ • Viewer       │    │   Period       │             │    │
│  │  └─────────────────┘    └─────────────────┘             │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                    │
│              ┌───────────────┼───────────────┐                   │
│              ▼               ▼               ▼                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│  │ Data Masking │ │ Audit Logger │ │ Policy       │              │
│  │              │ │              │ │ Enforcement  │              │
│  │ • HIDE       │ │ • All Actions│ │              │              │
│  │ • HASH       │ │ • User Track │ │ • ALLOW      │              │
│  │ • PARTIAL    │ │ • IP Logging │ │ • DENY       │              │
│  │ • RANGE      │ │ • Exportable │ │ • MASK       │              │
│  │ • CATEGORY   │ │              │ │              │              │
│  └──────────────┘ └──────────────┘ └──────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Details

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | FastAPI | 0.109.0 | REST API, WebSocket |
| ORM | SQLAlchemy | 2.0.25 | Database ORM |
| Migration | Alembic | 1.13.1 | Schema migration |
| Validation | Pydantic | 2.5.3 | Data validation |
| Server | Uvicorn | 0.27.0 | ASGI server |
| WebSocket | websockets | 12.0 | Real-time communication |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 18 | UI Framework |
| Language | TypeScript | Type safety |
| Build | Vite | Fast bundling |
| Charts | Recharts | Data visualization |
| HTTP | Axios | API communication |

### Database (Current & Planned)

| Database | Status | Use Case |
|----------|--------|----------|
| PostgreSQL | Active | Primary relational data |
| TimescaleDB | Planned | Time-series sensor data |
| Neo4j | Planned | Knowledge graph, RCA relationships |
| Redis | Planned | Caching, Pub/Sub |

---

## File Structure

```
backend/app/
├── api/
│   ├── __init__.py          # Router aggregation
│   ├── simulation.py        # PPA simulation
│   ├── workload.py          # Workload analysis
│   ├── yield_api.py         # Yield management
│   ├── fab.py               # Virtual fab
│   ├── supply.py            # Supply chain
│   ├── security.py          # Security/governance
│   ├── notifications.py     # Alert system
│   ├── reports.py           # Report generation
│   ├── predictions.py       # ML predictions
│   └── websocket.py         # Real-time streaming
├── models/
│   ├── __init__.py          # Model exports
│   ├── yield_event.py       # Yield domain
│   ├── fab.py               # Fab domain
│   ├── supply_chain.py      # Supply domain
│   ├── security.py          # Security domain
│   └── notification.py      # Notification domain
├── services/
│   ├── yield_analyzer.py    # Yield analysis + RCA
│   ├── virtual_fab.py       # Fab simulation
│   ├── supply_chain.py      # Supply chain service
│   ├── access_control.py    # RBAC/ABAC
│   ├── audit_logger.py      # Audit logging
│   ├── data_masking.py      # Data masking
│   ├── notification.py      # Notification service
│   ├── report_generator.py  # Report generation
│   ├── ml_models.py         # ML model definitions
│   ├── prediction_engine.py # Prediction orchestration
│   └── realtime.py          # WebSocket management
└── main.py                  # Application entry
```
