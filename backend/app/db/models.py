from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, Enum as SAEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ─── Enums ────────────────────────────────────────────────────────────────────

class ShipmentStatus(str, enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    CUSTOMS = "customs"
    DELAYED = "delayed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ShipmentMode(str, enum.Enum):
    AIR = "air"
    SEA = "sea"
    ROAD = "road"
    RAIL = "rail"
    MULTIMODAL = "multimodal"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, enum.Enum):
    ETA_CONFLICT = "eta_conflict"
    DELAY_RISK = "delay_risk"
    STATUS_CHANGE = "status_change"
    STALE_UPDATE = "stale_update"
    SYSTEM = "system"


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    shipments = relationship("Shipment", back_populates="owner", lazy="selectin")
    notifications = relationship("Notification", back_populates="user", lazy="selectin")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Origin / Destination
    origin_location = Column(String(255), nullable=False)
    destination_location = Column(String(255), nullable=False)
    origin_country = Column(String(100), nullable=True)
    destination_country = Column(String(100), nullable=True)

    # Carrier / Mode
    carrier = Column(String(255), nullable=True)
    mode = Column(SAEnum(ShipmentMode), default=ShipmentMode.SEA)

    # Status & Dates
    status = Column(SAEnum(ShipmentStatus), default=ShipmentStatus.PENDING, index=True)
    eta = Column(DateTime(timezone=True), nullable=True)
    etd = Column(DateTime(timezone=True), nullable=True)  # Estimated Time of Departure
    actual_delivery = Column(DateTime(timezone=True), nullable=True)

    # Risk scoring
    risk_level = Column(SAEnum(RiskLevel), default=RiskLevel.LOW)
    risk_score = Column(Float, default=0.0)  # 0.0 - 1.0
    risk_factors = Column(Text, nullable=True)  # JSON string of factors

    # ETA conflict flag
    has_eta_conflict = Column(Boolean, default=False)
    eta_conflict_reason = Column(Text, nullable=True)

    # Stale tracking detection
    last_update_at = Column(DateTime(timezone=True), default=utcnow)
    is_stale = Column(Boolean, default=False)

    # Weight / value
    weight_kg = Column(Float, nullable=True)
    value_usd = Column(Float, nullable=True)

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="shipments")
    tracking_events = relationship(
        "TrackingEvent", back_populates="shipment",
        order_by="TrackingEvent.event_time.desc()", lazy="selectin",
        cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="shipment", lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_shipments_status_owner", "status", "owner_id"),
        Index("ix_shipments_eta", "eta"),
    )


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    event_time = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    location = Column(String(255), nullable=True)
    status = Column(SAEnum(ShipmentStatus), nullable=False)
    description = Column(Text, nullable=True)
    # Simulated flag — marks data not from a real carrier integration
    is_simulated = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    shipment = relationship("Shipment", back_populates="tracking_events")

    __table_args__ = (
        Index("ix_tracking_events_shipment_time", "shipment_id", "event_time"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True, index=True)

    type = Column(SAEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="notifications")
    shipment = relationship("Shipment", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
    )
