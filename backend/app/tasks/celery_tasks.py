"""
Celery task definitions for background processing.
These tasks require Redis to be running. If Redis is unavailable,
the tasks can be called synchronously as regular functions.
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

# Graceful import — Celery is optional
try:
    from celery import Celery
    from app.core.config import settings

    if settings.REDIS_URL:
        celery_app = Celery(
            "smart_freight",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL,
        )
        celery_app.conf.update(
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"],
            timezone="UTC",
        )
        CELERY_AVAILABLE = True
    else:
        celery_app = None
        CELERY_AVAILABLE = False
except ImportError:
    celery_app = None
    CELERY_AVAILABLE = False


def run_stale_detection_sync():
    """
    Detects shipments with no tracking updates for >48h (in_transit/customs).
    Can be called directly without Celery.
    """
    import asyncio
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.db.models import Shipment, ShipmentStatus, Notification, NotificationType
    from app.services.risk import update_shipment_risk

    async def _run():
        threshold = datetime.now(timezone.utc) - timedelta(hours=48)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Shipment).where(
                    Shipment.status.in_([ShipmentStatus.IN_TRANSIT, ShipmentStatus.CUSTOMS]),
                    Shipment.last_update_at < threshold,
                    Shipment.is_stale == False,
                )
            )
            stale = result.scalars().all()
            updated = 0
            for shipment in stale:
                shipment.is_stale = True
                update_shipment_risk(shipment)
                notif = Notification(
                    user_id=shipment.owner_id,
                    shipment_id=shipment.id,
                    type=NotificationType.STALE_UPDATE,
                    title="Stale Tracking Alert",
                    message=f"No updates for shipment {shipment.tracking_number} in 48+ hours",
                )
                db.add(notif)
                updated += 1
            if updated:
                await db.commit()
        return {"stale_updated": updated}

    return asyncio.run(_run())


def run_eta_conflict_check_sync():
    """Check all active shipments for ETA conflicts."""
    import asyncio
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.db.models import Shipment, ShipmentStatus, Notification, NotificationType
    from app.services.risk import check_eta_conflict, update_shipment_risk

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Shipment).where(
                    Shipment.status.notin_([ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED])
                )
            )
            shipments = result.scalars().all()
            conflicts_found = 0
            for shipment in shipments:
                had_conflict = shipment.has_eta_conflict
                has_conflict, reason = check_eta_conflict(shipment)
                if has_conflict and not had_conflict:
                    # New conflict — notify
                    notif = Notification(
                        user_id=shipment.owner_id,
                        shipment_id=shipment.id,
                        type=NotificationType.ETA_CONFLICT,
                        title="ETA Conflict Detected",
                        message=f"Shipment {shipment.tracking_number}: {reason}",
                    )
                    db.add(notif)
                    conflicts_found += 1
                shipment.has_eta_conflict = has_conflict
                shipment.eta_conflict_reason = reason
                update_shipment_risk(shipment)
            if shipments:
                await db.commit()
        return {"conflicts_found": conflicts_found, "checked": len(shipments)}

    return asyncio.run(_run())


# Register as Celery tasks if available
if CELERY_AVAILABLE and celery_app:
    @celery_app.task(name="tasks.stale_detection")
    def stale_detection_task():
        return run_stale_detection_sync()

    @celery_app.task(name="tasks.eta_conflict_check")
    def eta_conflict_check_task():
        return run_eta_conflict_check_sync()

    # Periodic schedule
    celery_app.conf.beat_schedule = {
        "stale-detection-every-hour": {
            "task": "tasks.stale_detection",
            "schedule": 3600.0,
        },
        "eta-conflict-check-every-30min": {
            "task": "tasks.eta_conflict_check",
            "schedule": 1800.0,
        },
    }
