# API Reference

Base URL: `http://localhost:8000/api`

---

## Table of Contents

1. [Simulation API](#simulation-api)
2. [Workload Analysis API](#workload-analysis-api)
3. [Yield Management API](#yield-management-api)
4. [Virtual Fab API](#virtual-fab-api)
5. [Supply Chain API](#supply-chain-api)
6. [Security API](#security-api)
7. [Notifications API](#notifications-api)
8. [Reports API](#reports-api)
9. [Predictions API](#predictions-api)
10. [WebSocket API](#websocket-api)

---

## Simulation API

**Prefix**: `/simulate`

### PPA Optimization

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/simulate/ppa` | Run PPA optimization simulation |
| GET | `/simulate/history` | Get simulation history |
| GET | `/simulate/{sim_id}` | Get specific simulation result |

---

## Workload Analysis API

**Prefix**: `/workload`

### Workload Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workload/analyze` | Analyze workload and recommend architecture |
| GET | `/workload/presets` | Get preset workload profiles |
| GET | `/workload/presets/{preset_id}` | Get specific preset details |

#### Request Example: Analyze Workload
```json
POST /workload/analyze
{
  "name": "LLM Inference - Llama-3 70B",
  "workload_type": "AI_INFERENCE",
  "compute_requirements": {
    "operations_per_inference": 140,
    "target_latency_ms": 100,
    "batch_size": 8,
    "precision": "INT8"
  },
  "memory_requirements": {
    "model_size_gb": 70,
    "bandwidth_requirement_gbps": 800
  },
  "power_constraints": {
    "max_tdp_watts": 300
  }
}
```

---

## Yield Management API

**Prefix**: `/yield`

### Wafer Records

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/yield/wafers` | Create wafer record |
| GET | `/yield/wafers` | List wafer records |
| GET | `/yield/wafers/{wafer_id}` | Get specific wafer |

### Yield Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/yield/events` | Create yield event |
| GET | `/yield/events` | List yield events |
| GET | `/yield/events/{event_id}` | Get specific event |

### Root Cause Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/yield/events/{event_id}/analyze` | Run RCA on event |
| GET | `/yield/events/{event_id}/rca` | Get RCA results |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/yield/dashboard` | Get yield dashboard data |
| GET | `/yield/trends` | Get yield trends |

---

## Virtual Fab API

**Prefix**: `/fab`

### Equipment

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fab/equipment` | List all equipment |
| GET | `/fab/equipment/{equipment_id}` | Get equipment details |
| POST | `/fab/equipment` | Create equipment |
| PUT | `/fab/equipment/{equipment_id}` | Update equipment |

### WIP Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fab/wip` | List WIP items |
| GET | `/fab/wip/{lot_id}` | Get WIP item details |
| POST | `/fab/wip` | Create WIP item |

### Simulation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fab/status` | Get current fab status |
| GET | `/fab/bottlenecks` | Get bottleneck predictions |
| POST | `/fab/scenarios` | Create simulation scenario |
| POST | `/fab/scenarios/{id}/run` | Run scenario simulation |
| GET | `/fab/scenarios/{id}/result` | Get simulation results |

### Maintenance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fab/maintenance/schedule` | Get maintenance schedule |
| POST | `/fab/maintenance/optimize` | Optimize maintenance schedule |

---

## Supply Chain API

**Prefix**: `/supply`

### Suppliers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/supply/suppliers` | List suppliers |
| GET | `/supply/suppliers/{id}` | Get supplier details |
| POST | `/supply/suppliers` | Create supplier |
| PUT | `/supply/suppliers/{id}` | Update supplier |

### Materials

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/supply/materials` | List materials |
| GET | `/supply/materials/{id}` | Get material details |
| POST | `/supply/materials` | Create material |

### Risk Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/supply/risks` | List supply risks |
| GET | `/supply/risks/{id}` | Get risk details |
| POST | `/supply/risks` | Create risk alert |
| PUT | `/supply/risks/{id}` | Update risk |

### Inventory Optimization

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/supply/recommendations` | Get inventory recommendations |
| POST | `/supply/recommendations/{id}/execute` | Execute recommendation |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/supply/dashboard` | Supply chain dashboard |
| GET | `/supply/risk-map` | Geographic risk visualization |

---

## Security API

**Prefix**: `/security`

### Users & Roles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/security/users` | List users |
| POST | `/security/users` | Create user |
| GET | `/security/roles` | List roles |
| POST | `/security/roles` | Create role |

### Access Policies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/security/policies` | List access policies |
| POST | `/security/policies` | Create policy |
| PUT | `/security/policies/{id}` | Update policy |
| DELETE | `/security/policies/{id}` | Delete policy |

### Audit Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/security/audit` | Query audit logs |
| POST | `/security/audit/export` | Export audit logs |

### Access Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/security/access-check` | Check access permission |

---

## Notifications API

**Prefix**: `/notifications`

### Alert Rules

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/rules` | List alert rules |
| POST | `/notifications/rules` | Create alert rule |
| GET | `/notifications/rules/{id}` | Get rule details |
| PUT | `/notifications/rules/{id}` | Update rule |
| POST | `/notifications/rules/{id}/mute` | Mute rule |
| POST | `/notifications/rules/{id}/unmute` | Unmute rule |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/alerts` | List alerts |
| GET | `/notifications/alerts/active` | List active alerts |
| GET | `/notifications/alerts/summary` | Alert summary stats |
| GET | `/notifications/alerts/{id}` | Get alert details |
| POST | `/notifications/alerts/{id}/acknowledge` | Acknowledge alert |
| POST | `/notifications/alerts/{id}/resolve` | Resolve alert |

### Recipients

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/recipients` | List recipients |
| POST | `/notifications/recipients` | Create recipient |
| GET | `/notifications/recipients/{id}` | Get recipient details |

### Real-time Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/notifications/check` | Check metrics and trigger alerts |

---

## Reports API

**Prefix**: `/reports`

### Report Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/types` | List available report types |
| POST | `/reports/generate` | Generate report |
| GET | `/reports/{report_id}` | Get generated report |
| GET | `/reports/{report_id}/download` | Download report |

### Report Types

| Report Type | Description |
|-------------|-------------|
| `daily_yield` | Daily yield summary |
| `weekly_performance` | Weekly performance metrics |
| `monthly_executive` | Monthly executive dashboard |
| `supply_chain_risk` | Supply chain risk report |
| `audit_compliance` | Audit compliance report |

### Export Formats

- `JSON` - Raw data format
- `CSV` - Spreadsheet compatible
- `HTML` - Formatted report

#### Request Example: Generate Report
```json
POST /reports/generate
{
  "report_type": "daily_yield",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "format": "HTML"
}
```

---

## Predictions API

**Prefix**: `/predictions`

### Model Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predictions/models` | List all ML models |
| GET | `/predictions/models/{type}` | Get model details |

### Yield Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predictions/yield` | Predict yield |
| POST | `/predictions/yield/batch` | Batch yield prediction |

#### Request Example
```json
POST /predictions/yield
{
  "temperature": 23.0,
  "pressure": 1.0,
  "flow_rate": 100.0,
  "humidity": 45.0,
  "equipment_oee": 85.0
}
```

### Equipment Failure Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predictions/equipment-failure` | Predict equipment failure |
| POST | `/predictions/equipment-failure/fleet` | Fleet-wide prediction |

#### Request Example
```json
POST /predictions/equipment-failure
{
  "equipment_id": "EQ-LITHO-1",
  "vibration_level": 0.5,
  "operating_hours": 3000,
  "maintenance_overdue_days": 5,
  "error_count_7d": 3
}
```

### Demand Forecast

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predictions/demand` | Forecast demand |
| POST | `/predictions/demand/multi-period` | Multi-period forecast |

### Anomaly Detection

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predictions/anomaly` | Detect single anomaly |
| POST | `/predictions/anomaly/batch` | Batch anomaly detection |

### Integrated Insights

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predictions/insights` | Get production insights |
| GET | `/predictions/history` | Get prediction history |

### Demo

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predictions/demo/run-all` | Run all predictions demo |

---

## WebSocket API

### Connection

```
ws://localhost:8000/api/ws?subscriptions=yield_update,alert
```

**Query Parameters**:
- `client_id` (optional): Client identifier
- `subscriptions` (optional): Comma-separated stream types

### Stream Types

| Stream Type | Description | Update Frequency |
|-------------|-------------|------------------|
| `yield_update` | Real-time yield data | 1 second |
| `equipment_status` | Equipment state changes | On change |
| `wip_movement` | WIP tracking updates | On movement |
| `alert` | Alert notifications | On trigger |
| `metrics` | Fab metrics snapshot | On request |
| `heartbeat` | Connection health | On action |

### Client Messages

```json
// Subscribe to streams
{"action": "subscribe", "streams": ["yield_update", "alert"]}

// Unsubscribe from streams
{"action": "unsubscribe", "streams": ["wip_movement"]}

// Request current metrics
{"action": "request_metrics"}

// Ping (connection check)
{"action": "ping"}
```

### Server Message Format

```json
{
  "message_id": "yield-abc123",
  "stream_type": "yield_update",
  "timestamp": "2024-01-29T12:00:00Z",
  "data": {
    "current_yield": 92.5,
    "target_yield": 92.0,
    "delta": 0.5,
    "trend": "up",
    "process_step": "LITHO",
    "lot_id": "LOT-1234"
  },
  "priority": 0
}
```

### REST Endpoints for WebSocket Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/realtime/status` | Service status |
| GET | `/realtime/connections` | Active connections |
| POST | `/realtime/broadcast` | Manual broadcast |
| GET | `/realtime/metrics` | Current metrics (REST) |
| POST | `/realtime/start-streaming` | Start auto-streaming |
| POST | `/realtime/stop-streaming` | Stop auto-streaming |

---

## Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

### Paginated Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## Authentication

현재 인증은 구현되지 않음 (개발 단계).
향후 JWT 기반 인증 추가 예정.

```
Authorization: Bearer <token>
```
