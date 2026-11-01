from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.db.models import NotificationType


class NotificationRead(BaseModel):
    id: int
    user_id: int
    shipment_id: Optional[int]
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationUpdate(BaseModel):
    is_read: bool


class DashboardStats(BaseModel):
    total_shipments: int
    in_transit: int
    delivered: int
    delayed: int
    pending: int
    cancelled: int
    high_risk_count: int
    eta_conflict_count: int
    stale_count: int
    avg_risk_score: float
    on_time_rate: float  # percentage of delivered on time

    # By mode breakdown
    by_mode: dict
    # By status breakdown
    by_status: dict
    # Risk distribution
    by_risk: dict
    # Recent activity (last 7 days new shipments)
    recent_shipments_7d: int
