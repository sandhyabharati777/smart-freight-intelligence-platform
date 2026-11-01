import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, shipments, dashboard, notifications

app = FastAPI(
    title=settings.APP_NAME,
    description="Smart Freight Intelligence & Shipment Monitoring Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(shipments.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": settings.APP_NAME}


@app.on_event("startup")
async def startup_event():
    """Auto-create DB tables in dev. For production, use Alembic migrations."""
    from app.db.session import engine
    from app.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
