from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from app.db.models import ShipmentStatus, ShipmentMode, RiskLevel


class TrackingEventCreate(BaseModel):
    event_time: Optional[datetime] = None
    location: Optional[str] = None
    status: ShipmentStatus
    description: Optional[str] = None
    is_simulated: bool = True


class TrackingEventRead(BaseModel):
    id: int
    shipment_id: int
    event_time: datetime
    location: Optional[str]
    status: ShipmentStatus
    description: Optional[str]
    is_simulated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ShipmentCreate(BaseModel):
    tracking_number: str
    title: str
    description: Optional[str] = None
    origin_location: str
    destination_location: str
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    carrier: Optional[str] = None
    mode: ShipmentMode = ShipmentMode.SEA
    status: ShipmentStatus = ShipmentStatus.PENDING
    eta: Optional[datetime] = None
    etd: Optional[datetime] = None
    weight_kg: Optional[float] = None
    value_usd: Optional[float] = None

    @field_validator("tracking_number")
    @classmethod
    def tracking_number_valid(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) < 4:
            raise ValueError("Tracking number must be at least 4 characters")
        return v


class ShipmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    carrier: Optional[str] = None
    mode: Optional[ShipmentMode] = None
    status: Optional[ShipmentStatus] = None
    eta: Optional[datetime] = None
    etd: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    weight_kg: Optional[float] = None
    value_usd: Optional[float] = None


class ShipmentRead(BaseModel):
    id: int
    tracking_number: str
    title: str
    description: Optional[str]
    origin_location: str
    destination_location: str
    origin_country: Optional[str]
    destination_country: Optional[str]
    carrier: Optional[str]
    mode: ShipmentMode
    status: ShipmentStatus
    eta: Optional[datetime]
    etd: Optional[datetime]
    actual_delivery: Optional[datetime]
    risk_level: RiskLevel
    risk_score: float
    risk_factors: Optional[str]
    has_eta_conflict: bool
    eta_conflict_reason: Optional[str]
    last_update_at: datetime
    is_stale: bool
    weight_kg: Optional[float]
    value_usd: Optional[float]
    owner_id: int
    created_at: datetime
    updated_at: datetime
    tracking_events: List[TrackingEventRead] = []

    model_config = {"from_attributes": True}


class ShipmentListRead(BaseModel):
    """Lighter version for list views - no tracking events"""
    id: int
    tracking_number: str
    title: str
    origin_location: str
    destination_location: str
    carrier: Optional[str]
    mode: ShipmentMode
    status: ShipmentStatus
    eta: Optional[datetime]
    risk_level: RiskLevel
    risk_score: float
    has_eta_conflict: bool
    is_stale: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedShipments(BaseModel):
    items: List[ShipmentListRead]
    total: int
    page: int
    page_size: int
    pages: int
