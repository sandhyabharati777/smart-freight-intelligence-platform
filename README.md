# Smart Freight Intelligence & Shipment Monitoring Platform

A full-stack freight visibility platform with real-time shipment tracking, ETA conflict detection, explainable delay-risk scoring, and supply chain analytics.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Zustand, React Query, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 async, Alembic |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose) + bcrypt |
| Background | Celery + Redis *(optional — graceful fallback)* |
| Graph | Neo4j *(optional — graceful fallback)* |
| Deploy | Docker Compose |

---

## Quick Start (Local Dev — No Docker Required)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (on drive with free space)
python -m venv venv

# Activate
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env if needed (defaults use SQLite — no DB setup required)

# Start the API server
python main.py
# → http://localhost:8000
# → http://localhost:8000/api/docs (Swagger UI)
```

### 2. Seed Demo Data

```bash
# (with venv activated)
python seed.py
```

Demo accounts:
| Email | Password | Role |
|-------|----------|------|
| admin@smartfreight.demo | Admin@123 | Admin |
| ops@smartfreight.demo | Demo@1234 | Ops Manager |

> All seeded shipment/carrier data is labeled **[SIMULATED]**.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login (returns JWT) |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/shipments` | List shipments (search, filter, sort, paginate) |
| POST | `/api/shipments` | Create shipment |
| GET | `/api/shipments/{id}` | Get shipment details + tracking events |
| PATCH | `/api/shipments/{id}` | Update shipment |
| DELETE | `/api/shipments/{id}` | Delete shipment |
| POST | `/api/shipments/{id}/events` | Add tracking event |
| GET | `/api/shipments/{id}/events` | Get tracking event history |
| GET | `/api/dashboard/stats` | Dashboard analytics |
| GET | `/api/notifications` | List notifications |
| PATCH | `/api/notifications/{id}` | Mark read/unread |
| POST | `/api/notifications/mark-all-read` | Mark all read |
| GET | `/api/health` | Health check |

Full interactive docs: **http://localhost:8000/api/docs**

---

## Configuration (`.env`)

```env
# Required
SECRET_KEY=your-long-random-secret-key

# Database (SQLite default — no setup needed)
DATABASE_URL=sqlite+aiosqlite:///./smart_freight.db

# Optional: PostgreSQL
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/smart_freight

# Optional: Redis (enables Celery background tasks)
# REDIS_URL=redis://localhost:6379/0

# Optional: Neo4j (enables supply-chain graph queries)
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your-password
```

---

## Running Tests

```bash
cd backend
.\venv\Scripts\activate  # or source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_shipments.py -v
python -m pytest tests/test_risk.py -v
```

Tests use an **in-memory SQLite** database — no external services needed.

---

## Background Jobs (Celery + Redis)

> Celery is **optional**. Core CRUD works without it.

If Redis is available (`REDIS_URL` set in `.env`):

```bash
# Start Celery worker
celery -A app.tasks.celery_tasks:celery_app worker --loglevel=info

# Start Celery Beat (scheduler)
celery -A app.tasks.celery_tasks:celery_app beat --loglevel=info
```

Scheduled tasks:
- **Stale detection** (every hour): flags shipments with no updates for 48h+
- **ETA conflict check** (every 30 min): detects and notifies on scheduling conflicts

You can also run these manually as sync functions:
```python
from app.tasks.celery_tasks import run_stale_detection_sync, run_eta_conflict_check_sync
run_stale_detection_sync()
run_eta_conflict_check_sync()
```

---

## Supply Chain Graph (Neo4j)

> Neo4j is **optional**. All other features work without it.

When `NEO4J_URI` is not configured, graph endpoints return clearly-labeled **[SIMULATED]** fallback data.

---

## Docker Compose (Production)

```bash
# Copy and configure env
cp backend/.env.example backend/.env
# Edit SECRET_KEY and any other values

docker compose up -d
```

Services started:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Neo4j** on ports 7474 (browser), 7687 (bolt)
- **Backend API** on port 8000
- **Celery Worker + Beat**
- **Frontend** on port 5173

> Docker is required for this deployment mode.

---

## Features

### ✅ Phase 1 — Core Application
- JWT authentication (register, login, protected routes)
- Shipment CRUD with full field support
- Tracking event history with timeline UI
- Search, filter (status/mode/risk), sort, paginate
- Database-driven dashboard analytics with Recharts
- Explainable delay-risk scoring (transparent weighted factors)
- ETA conflict detection (ETD/ETA ordering, transit time sanity, past-ETA checks)
- Persistent notifications with read/unread status

### ✅ Phase 2 — Data & Reliability
- SQLAlchemy 2.0 async ORM with proper indexes
- Pydantic v2 validation on all inputs
- Seed script with realistic demo data (all labeled [SIMULATED])
- pytest test suite (auth, shipments, risk service)
- `.env.example`, `.gitignore`

### ✅ Phase 3 — Optional Services
- Celery tasks with documented fallback behavior
- Neo4j service with graceful fallback returning simulated data
- Background stale detection and ETA conflict tasks

### ✅ Phase 4 — Verification & Docs
- Test suite passes for auth, risk scoring, and CRUD
- Docker Compose with all services
- This README

---

## Known Limitations

| Limitation | Reason | Mitigation |
|-----------|--------|------------|
| Docker not tested locally | Docker not installed on build machine | Compose file provided for reference |
| `pydantic[email]` not installed | C: drive full; pip can't write to temp | Email validated with regex instead |
| No live carrier tracking | Carrier APIs require paid accounts | All carrier data labeled [SIMULATED] |
| Celery tasks not auto-running | Redis not configured by default | Sync fallback functions provided |
| Neo4j graph queries | Neo4j not started by default | Documented fallback with simulated data |

---

## Project Structure

```
smart-freight/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (auth, shipments, dashboard, notifications)
│   │   ├── core/          # Config, security (JWT/bcrypt), dependencies
│   │   ├── db/            # SQLAlchemy models + session
│   │   ├── schemas/       # Pydantic v2 schemas
│   │   ├── services/      # Risk scoring, ETA detection, Neo4j
│   │   └── tasks/         # Celery tasks
│   ├── tests/             # pytest test suite
│   ├── alembic/           # DB migrations (configured)
│   ├── main.py            # Entry point + startup
│   ├── seed.py            # Demo data seeder
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/           # Axios client + endpoint functions
│   │   ├── components/    # Layout, UI (badges, stats, spinner, etc.)
│   │   ├── pages/         # Dashboard, Shipments, Detail, NewShipment, Notifications, Auth
│   │   ├── store/         # Zustand auth store
│   │   └── types/         # TypeScript type definitions
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```
