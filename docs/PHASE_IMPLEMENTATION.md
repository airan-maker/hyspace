# Phase Implementation Details

각 Phase별 구현 상세 내역

---

## Phase 1: Foundation

### 구현 완료

| Component | File | Description |
|-----------|------|-------------|
| PPA Simulation | `api/simulation.py` | Performance, Power, Area 최적화 |
| Process Nodes | `models/process_node.py` | 공정 노드 데이터 모델 |
| IP Library | `models/ip_library.py` | IP 블록 라이브러리 |

---

## Phase 2: Enterprise Platform

### Phase 2a: Workload Analyzer

**목적**: AI/ML 워크로드 분석 및 최적 아키텍처 추천

| Component | File | Description |
|-----------|------|-------------|
| Analyzer Engine | `services/workload_analyzer.py` | 워크로드 특성 분석 |
| Preset Profiles | `services/workload_presets.py` | 사전 정의 워크로드 |
| API Endpoints | `api/workload.py` | REST API |
| React Hook | `hooks/useWorkloadAnalysis.ts` | Frontend 훅 |

**주요 기능**:
- Workload Characterization (Memory-Bound / Compute-Bound)
- NPU Core Scaling 계산
- Memory Configuration 최적화
- 경쟁사 벤치마크 비교 (H100, MI300X)

---

### Phase 2b: Yield Management

**목적**: 수율 분석 및 근본 원인 분석 (RCA)

| Component | File | Description |
|-----------|------|-------------|
| Data Models | `models/yield_event.py` | WaferRecord, YieldEvent, Equipment |
| Yield Analyzer | `services/yield_analyzer.py` | 수율 분석 + RCA 엔진 |
| API Endpoints | `api/yield_api.py` | REST API |
| Dashboard Components | `components/YieldDashboard/*` | UI 컴포넌트 |

**RCA 알고리즘**:
```
1. 공통 요소 분석 (Common Factor Analysis)
   - 영향받은 웨이퍼들의 공유 장비/재료/작업자 식별

2. 시간적 상관관계 (Temporal Correlation)
   - 이벤트 발생 시점 전후 48시간 패턴 분석

3. 장비별 수율 편차 (Equipment Variance)
   - 장비별 수율 분포 및 이상치 탐지

4. 공정 파라미터 이상치 (Process Anomalies)
   - 온도, 압력, 유량 등 파라미터 이상 탐지

5. 신뢰도 기반 순위화 (Confidence Ranking)
   - 각 원인 후보에 대한 확률 계산 및 순위화
```

---

### Phase 2c: Virtual Fab

**목적**: 디지털 트윈 기반 Fab 시뮬레이션

| Component | File | Description |
|-----------|------|-------------|
| Data Models | `models/fab.py` | FabEquipment, WIPItem, Scenario |
| Simulator | `services/virtual_fab.py` | 이산 사건 시뮬레이션 |
| API Endpoints | `api/fab.py` | REST API |

**시뮬레이션 기능**:
- **Bottleneck Predictor**: 향후 N시간 내 병목 예측
- **What-If Scenarios**: 장비 고장, 수요 급증 시나리오 분석
- **Maintenance Optimizer**: PM 일정 최적화

**시나리오 유형**:
| Type | Description |
|------|-------------|
| EQUIPMENT_FAILURE | 특정 장비 고장 시뮬레이션 |
| DEMAND_SPIKE | 수요 급증 시나리오 |
| NEW_PROCESS | 신규 공정 도입 영향 |
| MAINTENANCE_SCHEDULE | PM 일정 변경 영향 |

---

### Phase 2d: Supply Chain

**목적**: Tier-N 공급망 가시성 및 리스크 관리

| Component | File | Description |
|-----------|------|-------------|
| Data Models | `models/supply_chain.py` | Supplier, Material, SupplyRisk |
| Supply Service | `services/supply_chain.py` | 공급망 분석 |
| Risk Detector | `services/supply_chain.py` | 리스크 탐지 |
| Inventory Optimizer | `services/supply_chain.py` | 재고 최적화 |
| API Endpoints | `api/supply.py` | REST API |

**Tier 구조**:
```
Tier 0 (자사) ← Tier 1 (1차 협력사) ← Tier 2 (2차 협력사) ← Tier 3 (원자재)
```

**리스크 유형**:
| Type | Description |
|------|-------------|
| GEOPOLITICAL | 지정학적 리스크 (분쟁, 제재) |
| LOGISTICS | 물류 리스크 (운송 지연, 항만 혼잡) |
| QUALITY | 품질 리스크 (불량률 상승) |
| CAPACITY | 용량 리스크 (공급 부족) |
| FINANCIAL | 재무 리스크 (공급자 파산) |
| NATURAL_DISASTER | 자연재해 |

---

### Phase 2e: Security & Governance

**목적**: RBAC/ABAC 접근 제어 및 감사 로깅

| Component | File | Description |
|-----------|------|-------------|
| Data Models | `models/security.py` | User, Role, AccessPolicy, AuditLog |
| Access Control | `services/access_control.py` | RBAC/ABAC 엔진 |
| Audit Logger | `services/audit_logger.py` | 감사 로그 |
| Data Masking | `services/data_masking.py` | 데이터 마스킹 |
| API Endpoints | `api/security.py` | REST API |

**접근 제어 모델**:
```
┌─────────────────────────────────────────────┐
│              Policy Evaluation              │
│                                             │
│  RBAC Check          ABAC Check             │
│  ──────────          ──────────             │
│  Role: Engineer      Time: 09:00-18:00      │
│  Resource: yield_data IP: 10.0.0.0/8       │
│  Action: VIEW        Contract: ACTIVE       │
│                                             │
│           Combined Result: ALLOW/DENY       │
└─────────────────────────────────────────────┘
```

**마스킹 유형**:
| Type | Example |
|------|---------|
| HIDE | `[HIDDEN]` |
| HASH | `a1b2c3...` |
| PARTIAL | `***-1234` |
| RANGE | `80-90%` |
| CATEGORY | `High`, `Medium`, `Low` |

---

## Phase 3: Advanced Analytics

### Phase 3a: Real-time Dashboard

**목적**: WebSocket 기반 실시간 모니터링

| Component | File | Description |
|-----------|------|-------------|
| Connection Manager | `services/realtime.py` | WebSocket 연결 관리 |
| Data Streams | `services/realtime.py` | 실시간 데이터 생성 |
| WebSocket API | `api/websocket.py` | WS 엔드포인트 |
| React Hook | `hooks/useRealtime.ts` | Frontend 훅 |

**스트림 유형**:
| Stream | Update Frequency | Data |
|--------|------------------|------|
| yield_update | 1초 | 현재 수율, 트렌드, 로트 정보 |
| equipment_status | On change | 장비 상태, OEE, 온도 |
| wip_movement | On move | WIP 이동, 진행률 |
| alert | On trigger | 알림, 심각도 |
| metrics | On request | Fab 전체 메트릭 |

**구독 모델**:
```javascript
// 클라이언트 → 서버
{"action": "subscribe", "streams": ["yield_update", "alert"]}

// 서버 → 클라이언트
{
  "message_id": "yield-abc123",
  "stream_type": "yield_update",
  "timestamp": "2024-01-29T12:00:00Z",
  "data": {
    "current_yield": 92.5,
    "trend": "up"
  },
  "priority": 0
}
```

---

### Phase 3b: Predictive Analytics

**목적**: ML 기반 예측 분석 (시뮬레이션)

| Component | File | Description |
|-----------|------|-------------|
| ML Models | `services/ml_models.py` | 모델 정의 |
| Prediction Engine | `services/prediction_engine.py` | 예측 오케스트레이션 |
| API Endpoints | `api/predictions.py` | REST API |

**모델 상세**:

#### Yield Prediction Model
```
Input Features:
- temperature, pressure, flow_rate, humidity
- equipment_oee, process_time, wafer_position

Output:
- predicted_yield (%)
- confidence (0-1)
- risk_factors
- optimization_suggestions

Algorithm: XGBoost/LightGBM (simulated)
```

#### Equipment Failure Model
```
Input Features:
- vibration_level, operating_hours, temperature_delta
- maintenance_overdue_days, error_count_7d

Output:
- failure_probability (0-1)
- estimated_failure_time
- remaining_useful_life_hours
- maintenance_recommendation
- failure_mode

Algorithm: LSTM/Prophet (simulated)
```

#### Demand Forecast Model
```
Input Features:
- historical_demand_4w, market_growth_rate
- customer_orders_pipeline, economic_indicator

Output:
- forecasted_demand (units)
- trend (INCREASING/DECREASING/STABLE)
- seasonality_factor
- confidence_interval

Algorithm: ARIMA/Prophet (simulated)
```

#### Anomaly Detection Model
```
Input:
- metric_name, value
- historical_mean, historical_std

Output:
- anomaly_score (0-1)
- is_anomaly (boolean)
- severity (NORMAL/INFO/WARNING/CRITICAL)
- z_score

Algorithm: Isolation Forest (simulated)
```

---

### Phase 3c: Notification System

**목적**: 다채널 알림 및 에스컬레이션

| Component | File | Description |
|-----------|------|-------------|
| Data Models | `models/notification.py` | AlertRule, Alert, Recipient |
| Alert Engine | `services/notification.py` | 알림 규칙 엔진 |
| Dispatcher | `services/notification.py` | 다채널 발송 |
| API Endpoints | `api/notifications.py` | REST API |

**알림 규칙 유형**:
| Type | Description | Example |
|------|-------------|---------|
| THRESHOLD | 임계값 기반 | yield < 85% |
| ANOMALY | 이상 탐지 기반 | 3-sigma 이탈 |
| TREND | 트렌드 기반 | 연속 5회 하락 |
| EVENT | 이벤트 기반 | 장비 다운 |

**알림 채널**:
| Channel | Configuration |
|---------|---------------|
| EMAIL | SMTP 설정 |
| SLACK | Webhook URL |
| SMS | Twilio 연동 |
| IN_APP | WebSocket 푸시 |
| WEBHOOK | Custom endpoint |

**에스컬레이션 매트릭스**:
```
Level 1 (담당자) → 30분 미응답 → Level 2 (팀장) → 30분 미응답 → Level 3 (임원)
```

---

### Phase 3d: Report Generation

**목적**: 자동화된 보고서 생성

| Component | File | Description |
|-----------|------|-------------|
| Report Generator | `services/report_generator.py` | 보고서 생성 엔진 |
| API Endpoints | `api/reports.py` | REST API |

**보고서 유형**:
| Report | Contents |
|--------|----------|
| daily_yield | 일간 수율 요약, 주요 이벤트, 장비별 수율 |
| weekly_performance | 주간 KPI, 트렌드, 병목 분석 |
| monthly_executive | 경영진용 요약, 목표 대비 실적 |
| supply_chain_risk | 리스크 현황, 재고 상태, 권장 조치 |
| audit_compliance | 감사 로그 요약, 접근 통계 |

**출력 형식**:
- JSON: 원시 데이터
- CSV: 스프레드시트 호환
- HTML: 포맷팅된 보고서

---

## Implementation Statistics

### Backend

| Category | Count |
|----------|-------|
| API Routers | 11 |
| SQLAlchemy Models | 25+ |
| Service Classes | 15+ |
| API Endpoints | 80+ |

### File Count by Module

| Module | Files |
|--------|-------|
| api/ | 12 |
| models/ | 8 |
| services/ | 12 |
| Total | 32+ |

### Lines of Code (Estimated)

| Component | LOC |
|-----------|-----|
| Backend Python | ~8,000 |
| Frontend TypeScript | ~3,000 |
| Total | ~11,000 |

---

## API Summary by Phase

| Phase | Prefix | Endpoints |
|-------|--------|-----------|
| 1 | /simulate | 3 |
| 2a | /workload | 3 |
| 2b | /yield | 10 |
| 2c | /fab | 12 |
| 2d | /supply | 15 |
| 2e | /security | 10 |
| 3a | /ws, /realtime | 8 |
| 3b | /predictions | 12 |
| 3c | /notifications | 15 |
| 3d | /reports | 5 |
