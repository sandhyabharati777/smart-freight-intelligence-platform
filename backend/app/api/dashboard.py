from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.deps import get_db, get_current_user
from app.db.models import (
    User, Shipment, Notification, ShipmentStatus, ShipmentMode, RiskLevel
)
from app.schemas.notification import DashboardStats, NotificationRead, NotificationUpdate

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = select(Shipment).where(Shipment.owner_id == current_user.id)

    result = await db.execute(base)
    all_shipments = result.scalars().all()

    total = len(all_shipments)
    by_status = {}
    by_mode = {}
    by_risk = {}
    risk_sum = 0.0
    delivered_on_time = 0
    delivered_total = 0

    for s in all_shipments:
        # Status counts
        sv = s.status.value
        by_status[sv] = by_status.get(sv, 0) + 1

        # Mode counts
        mv = s.mode.value
        by_mode[mv] = by_mode.get(mv, 0) + 1

        # Risk distribution
        rv = s.risk_level.value
        by_risk[rv] = by_risk.get(rv, 0) + 1

        # Risk sum
        risk_sum += s.risk_score

        # On-time delivery check
        if s.status == ShipmentStatus.DELIVERED:
            delivered_total += 1
            if s.actual_delivery and s.eta:
                ad = s.actual_delivery
                eta = s.eta
                if ad.tzinfo is None:
                    ad = ad.replace(tzinfo=timezone.utc)
                if eta.tzinfo is None:
                    eta = eta.replace(tzinfo=timezone.utc)
                if ad <= eta:
                    delivered_on_time += 1

    in_transit = by_status.get(ShipmentStatus.IN_TRANSIT.value, 0)
    delivered = by_status.get(ShipmentStatus.DELIVERED.value, 0)
    delayed = by_status.get(ShipmentStatus.DELAYED.value, 0)
    pending = by_status.get(ShipmentStatus.PENDING.value, 0)
    cancelled = by_status.get(ShipmentStatus.CANCELLED.value, 0)

    high_risk_count = sum(
        1 for s in all_shipments
        if s.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    )
    eta_conflict_count = sum(1 for s in all_shipments if s.has_eta_conflict)
    stale_count = sum(1 for s in all_shipments if s.is_stale)

    avg_risk = round(risk_sum / total, 4) if total else 0.0
    on_time_rate = round(delivered_on_time / delivered_total * 100, 1) if delivered_total else 0.0

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = sum(
        1 for s in all_shipments
        if s.created_at and (
            s.created_at.replace(tzinfo=timezone.utc) if s.created_at.tzinfo is None else s.created_at
        ) >= seven_days_ago
    )

    return DashboardStats(
        total_shipments=total,
        in_transit=in_transit,
        delivered=delivered,
        delayed=delayed,
        pending=pending,
        cancelled=cancelled,
        high_risk_count=high_risk_count,
        eta_conflict_count=eta_conflict_count,
        stale_count=stale_count,
        avg_risk_score=avg_risk,
        on_time_rate=on_time_rate,
        by_mode=by_mode,
        by_status=by_status,
        by_risk=by_risk,
        recent_shipments_7d=recent,
    )
