# Development Guide

Silicon Nexus 개발 환경 설정 및 가이드

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| PostgreSQL | 15+ | Primary database |
| Git | Latest | Version control |

### Optional (Recommended)

| Software | Purpose |
|----------|---------|
| Docker | Containerized development |
| VS Code | IDE with extensions |
| Postman | API testing |

---

## Quick Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd silicon-nexus
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Database Setup

```bash
# Create database
psql -U postgres
CREATE DATABASE silicon_nexus;
\q

# Run migrations
alembic upgrade head

# (Optional) Seed demo data
python scripts/seed_demo_data.py
```

### 4. Run Backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Run development server
npm run dev
```

---

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/silicon_nexus

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Optional: External Services
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/api
```

---

## Project Structure

```
silicon-nexus/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints (routers)
│   │   │   ├── __init__.py   # Router aggregation
│   │   │   ├── yield_api.py
│   │   │   ├── fab.py
│   │   │   └── ...
│   │   ├── models/           # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── yield_event.py
│   │   │   └── ...
│   │   ├── services/         # Business logic
│   │   │   ├── yield_analyzer.py
│   │   │   ├── virtual_fab.py
│   │   │   └── ...
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── database.py       # Database connection
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   ├── tests/                # Test files
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API clients
│   │   ├── types/            # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
└── docs/                     # Documentation
```

---

## Development Workflow

### Adding a New Feature

#### 1. Create Model (if needed)

```python
# backend/app/models/my_feature.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
```

#### 2. Create Migration

```bash
alembic revision --autogenerate -m "Add my_table"
alembic upgrade head
```

#### 3. Create Service

```python
# backend/app/services/my_service.py
from sqlalchemy.orm import Session
from app.models.my_feature import MyModel

class MyService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str) -> MyModel:
        item = MyModel(name=name)
        self.db.add(item)
        self.db.commit()
        return item
```

#### 4. Create API Endpoint

```python
# backend/app/api/my_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.my_service import MyService

router = APIRouter(prefix="/my-feature", tags=["My Feature"])

@router.post("/")
def create_item(name: str, db: Session = Depends(get_db)):
    service = MyService(db)
    return service.create(name)
```

#### 5. Register Router

```python
# backend/app/api/__init__.py
from .my_feature import router as my_feature_router

api_router.include_router(my_feature_router, tags=["My Feature"])
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_yield.py -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm run test

# Run with coverage
npm run test:coverage
```

---

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Docstrings for public functions

```python
def analyze_yield(
    wafer_ids: list[str],
    threshold: float = 0.85
) -> dict:
    """
    Analyze yield for given wafers.

    Args:
        wafer_ids: List of wafer identifiers
        threshold: Yield threshold for alerts

    Returns:
        Analysis result dictionary
    """
    ...
```

### TypeScript

- Use strict mode
- Define interfaces for data structures
- Use functional components with hooks

```typescript
interface YieldData {
  wafer_id: string;
  yield_value: number;
  timestamp: string;
}

const YieldChart: React.FC<{ data: YieldData[] }> = ({ data }) => {
  ...
};
```

---

## Common Commands

### Backend

```bash
# Start server
uvicorn app.main:app --reload

# Create migration
alembic revision --autogenerate -m "message"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

### Frontend

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview build
npm run preview

# Lint
npm run lint

# Format
npm run format
```

---

## API Documentation

FastAPI 자동 문서:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Debugging

### Backend

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json:
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.main:app", "--reload"],
            "jinja": true
        }
    ]
}
```

### Frontend

- Use React DevTools browser extension
- Console logging: `console.log()`
- Network tab for API debugging

---

## Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Check PostgreSQL is running and .env credentials are correct.

### Import Error

```
ModuleNotFoundError: No module named 'app'
```

**Solution**: Ensure you're in the correct directory and virtual environment is activated.

### CORS Error

```
Access to fetch at 'http://localhost:8000/api/...' has been blocked by CORS policy
```

**Solution**: Check CORS_ORIGINS in backend .env includes your frontend URL.

### WebSocket Connection Failed

**Solution**:
1. Check WebSocket URL includes `/api/ws`
2. Verify backend is running
3. Check for proxy/firewall issues

---

## Deployment

### Docker (Recommended)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: silicon_nexus
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/silicon_nexus

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Run with Docker

```bash
docker-compose up -d
```

---

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run tests: `pytest` / `npm run test`
4. Commit: `git commit -m "Add my feature"`
5. Push: `git push origin feature/my-feature`
6. Create Pull Request
