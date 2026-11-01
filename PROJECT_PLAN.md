# Smart Freight Intelligence & Shipment Monitoring Platform

## Environment
- Node.js: v24.13.0 | Python: 3.13.6 | npm: 11.6.2 | pip: 25.2
- Docker: NOT INSTALLED — Docker Compose files provided but not runnable locally
- PostgreSQL: Requires local install or use SQLite for dev (configured via .env)
- Redis/Celery: Optional — graceful fallback if unavailable
- Neo4j: Optional — graceful fallback if unavailable

## Architecture

```
smart-freight/
├── backend/           # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── core/      # Config, security, deps
│   │   ├── db/        # Models, session
│   │   ├── schemas/   # Pydantic models
│   │   ├── services/  # Business logic
│   │   └── tasks/     # Celery tasks
│   ├── alembic/       # DB migrations
│   ├── tests/         # pytest
│   └── main.py
├── frontend/          # React + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── api/       # Axios clients
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── store/     # Zustand state
│   │   └── types/
│   └── index.html
├── docker-compose.yml
├── .env.example
└── README.md
```

## Tech Stack
- Frontend: React 18, TypeScript, Vite, Tailwind CSS, Zustand, React Query, React Router v6
- Backend: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- Database: PostgreSQL (SQLite fallback for dev via env var)
- Auth: JWT (python-jose), bcrypt
- Background: Celery + Redis (optional, graceful fallback)
- Graph: Neo4j (optional, graceful fallback)
- Tests: pytest, httpx, vitest

## Phases & Progress

### Phase 1 — Core Application
- [x] Project structure scaffolding
- [x] Backend: Auth (register/login/JWT)
- [x] Backend: Shipment CRUD + tracking events
- [x] Backend: Dashboard analytics endpoints
- [x] Backend: ETA conflict detection + delay risk scoring
- [x] Backend: Notifications (persistent, read/unread)
- [x] Frontend: Auth pages + protected routes
- [x] Frontend: Shipment list with search/filter/sort/paginate
- [x] Frontend: Shipment detail + tracking timeline
- [x] Frontend: Dashboard with real analytics
- [x] Frontend: Notifications panel

### Phase 2 — Data & Reliability
- [x] Alembic migrations
- [x] Seed data script
- [x] Input validation + error handling
- [x] DB indexes
- [x] Backend tests (pytest)
- [x] .env.example + .gitignore

### Phase 3 — Optional Services
- [x] Celery tasks (stale detection, ETA check, risk update)
- [x] Neo4j supply-chain queries
- [x] Graceful fallback when services unavailable

### Phase 4 — Verification & Docs
- [x] Run tests, fix failures
- [x] README with full setup instructions
- [x] Docker Compose

## Acceptance Criteria
1. Auth: register, login, protected routes work
2. Shipments: create, read, update, delete, search, filter, paginate
3. Tracking: add events, view history
4. Dashboard: metrics from real DB queries
5. ETA conflicts detected and exposed via API
6. Risk scores calculated with explanations
7. Notifications persisted and toggleable
8. All endpoints return proper HTTP codes and validation errors
9. Tests pass for critical paths
10. README covers all setup steps
