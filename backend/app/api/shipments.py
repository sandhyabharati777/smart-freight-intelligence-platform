import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, asc, desc
from app.core.deps import get_db, get_current_user
from app.db.models import User, Shipment, TrackingEvent, Notification, NotificationType, ShipmentStatus
from app.schemas.shipment import (
    ShipmentCreate, ShipmentUpdate, ShipmentRead,
    ShipmentListRead, PaginatedShipments, TrackingEventCreate, TrackingEventRead,
)
from app.services.risk import update_shipment_risk
import secrets
import string

router = APIRouter(prefix="/api/shipments", tags=["shipments"])


def _generate_tracking_number() -> str:
    chars = string.ascii_uppercase + string.digits
    return "SF" + "".join(secrets.choice(chars) for _ in range(10))


async def _get_shipment_or_404(
    shipment_id: int, db: AsyncSession, user: User
) -> Shipment:
    result = await db.execute(
        select(Shipment).where(
            Shipment.id == shipment_id,
            Shipment.owner_id == user.id,
        )
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@router.post("", response_model=ShipmentRead, status_code=201)
async def create_shipment(
    data: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check unique tracking number
    existing = await db.execute(
        select(Shipment).where(Shipment.tracking_number == data.tracking_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tracking number already exists")

    shipment = Shipment(
        **data.model_dump(exclude_none=True),
        owner_id=current_user.id,
    )
    update_shipment_risk(shipment)
    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)

    # Create initial tracking event
    event = TrackingEvent(
        shipment_id=shipment.id,
        status=shipment.status,
        location=shipment.origin_location,
        description=f"Shipment created at {shipment.origin_location}",
        is_simulated=True,
    )
    db.add(event)
    await db.commit()
    await db.refresh(shipment)
    return shipment


@router.get("", response_model=PaginatedShipments)
async def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Shipment).where(Shipment.owner_id == current_user.id)

    if search:
        like = f"%{search}%"
        q = q.where(
            or_(
                Shipment.tracking_number.ilike(like),
                Shipment.title.ilike(like),
                Shipment.origin_location.ilike(like),
                Shipment.destination_location.ilike(like),
                Shipment.carrier.ilike(like),
            )
        )

    if status:
        q = q.where(Shipment.status == status)
    if mode:
        q = q.where(Shipment.mode == mode)
    if risk_level:
        q = q.where(Shipment.risk_level == risk_level)

    # Count
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Sort
    sort_col = getattr(Shipment, sort_by, Shipment.created_at)
    if sort_dir == "asc":
        q = q.order_by(asc(sort_col))
    else:
        q = q.order_by(desc(sort_col))

    # Paginate
    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)

    result = await db.execute(q)
    items = result.scalars().all()

    return PaginatedShipments(
        items=[ShipmentListRead.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 1,
    )


@router.get("/{shipment_id}", response_model=ShipmentRead)
async def get_shipment(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _get_shipment_or_404(shipment_id, db, current_user)


@router.patch("/{shipment_id}", response_model=ShipmentRead)
async def update_shipment(
    shipment_id: int,
    data: ShipmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shipment = await _get_shipment_or_404(shipment_id, db, current_user)

    prev_status = shipment.status
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(shipment, field, value)

    shipment.last_update_at = datetime.now(timezone.utc)
    shipment.is_stale = False
    update_shipment_risk(shipment)

    # Notification on status change
    if data.status and data.status != prev_status:
        notif = Notification(
            user_id=current_user.id,
            shipment_id=shipment.id,
            type=NotificationType.STATUS_CHANGE,
            title="Shipment Status Updated",
            message=f"Shipment {shipment.tracking_number} changed from {prev_status.value} to {data.status.value}",
        )
        db.add(notif)

    await db.commit()
    await db.refresh(shipment)
    return shipment


@router.delete("/{shipment_id}", status_code=204)
async def delete_shipment(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shipment = await _get_shipment_or_404(shipment_id, db, current_user)
    await db.delete(shipment)
    await db.commit()


@router.post("/{shipment_id}/events", response_model=TrackingEventRead, status_code=201)
async def add_tracking_event(
    shipment_id: int,
    data: TrackingEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shipment = await _get_shipment_or_404(shipment_id, db, current_user)

    event = TrackingEvent(
        shipment_id=shipment.id,
        status=data.status,
        location=data.location,
        description=data.description,
        is_simulated=data.is_simulated,
        event_time=data.event_time or datetime.now(timezone.utc),
    )
    db.add(event)

    # Update shipment status if event is newer
    shipment.status = data.status
    shipment.last_update_at = datetime.now(timezone.utc)
    shipment.is_stale = False
    update_shipment_risk(shipment)

    await db.commit()
    await db.refresh(event)
    return event


@router.get("/{shipment_id}/events", response_model=list[TrackingEventRead])
async def get_tracking_events(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shipment = await _get_shipment_or_404(shipment_id, db, current_user)
    result = await db.execute(
        select(TrackingEvent)
        .where(TrackingEvent.shipment_id == shipment.id)
        .order_by(desc(TrackingEvent.event_time))
    )
    return result.scalars().all()
