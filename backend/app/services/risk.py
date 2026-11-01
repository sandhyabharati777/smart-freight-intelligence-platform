"""
Risk scoring service.

Computes an explainable delay-risk score (0.0–1.0) and risk level
for a shipment based on observable factors. No ML model required —
uses a transparent weighted scoring approach.
"""
from datetime import datetime, timezone, timedelta
from typing import Tuple, List, Optional
import json
from app.db.models import Shipment, ShipmentStatus, ShipmentMode, RiskLevel


def _days_until_eta(eta: Optional[datetime]) -> Optional[float]:
    if eta is None:
        return None
    now = datetime.now(timezone.utc)
    if eta.tzinfo is None:
        eta = eta.replace(tzinfo=timezone.utc)
    return (eta - now).total_seconds() / 86400


def compute_risk(shipment: Shipment) -> Tuple[float, RiskLevel, List[str]]:
    """
    Returns (score: float 0-1, level: RiskLevel, factors: list[str])
    """
    score = 0.0
    factors: List[str] = []

    # Factor 1: Status risk
    status_weights = {
        ShipmentStatus.PENDING: 0.05,
        ShipmentStatus.IN_TRANSIT: 0.10,
        ShipmentStatus.CUSTOMS: 0.30,
        ShipmentStatus.DELAYED: 0.60,
        ShipmentStatus.CANCELLED: 0.70,
        ShipmentStatus.DELIVERED: 0.00,
    }
    status_risk = status_weights.get(shipment.status, 0.0)
    if status_risk > 0:
        score += status_risk * 0.35
        if shipment.status == ShipmentStatus.DELAYED:
            factors.append("Shipment is currently marked as delayed")
        elif shipment.status == ShipmentStatus.CUSTOMS:
            factors.append("Shipment held at customs — delays common")
        elif shipment.status == ShipmentStatus.CANCELLED:
            factors.append("Shipment has been cancelled")

    # Factor 2: ETA proximity (if ETA is very soon and not delivered)
    if shipment.status not in (ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED):
        days_left = _days_until_eta(shipment.eta)
        if days_left is not None:
            if days_left < 0:
                score += 0.25
                factors.append(f"ETA already passed by {abs(days_left):.1f} days")
            elif days_left < 1:
                score += 0.15
                factors.append("ETA is within 24 hours — high urgency")
            elif days_left < 3:
                score += 0.05
                factors.append("ETA is within 3 days")

    # Factor 3: ETA conflict
    if shipment.has_eta_conflict:
        score += 0.20
        factors.append(f"ETA conflict detected: {shipment.eta_conflict_reason or 'inconsistent dates'}")

    # Factor 4: Stale updates
    if shipment.is_stale:
        score += 0.15
        factors.append("No tracking updates received recently (stale)")

    # Factor 5: Mode risk (sea shipping has higher inherent variability)
    mode_risks = {
        ShipmentMode.AIR: 0.0,
        ShipmentMode.ROAD: 0.02,
        ShipmentMode.RAIL: 0.03,
        ShipmentMode.SEA: 0.05,
        ShipmentMode.MULTIMODAL: 0.07,
    }
    mode_risk = mode_risks.get(shipment.mode, 0.0)
    if mode_risk > 0:
        score += mode_risk
        if shipment.mode in (ShipmentMode.SEA, ShipmentMode.MULTIMODAL):
            factors.append(f"Mode '{shipment.mode.value}' has higher schedule variability")

    # Factor 6: High-value cargo
    if shipment.value_usd and shipment.value_usd > 100_000:
        score += 0.05
        factors.append(f"High-value cargo (${shipment.value_usd:,.0f}) — extra monitoring needed")

    # Cap at 1.0
    score = min(score, 1.0)

    if not factors:
        factors.append("No significant risk factors detected")

    # Determine level
    if score >= 0.70:
        level = RiskLevel.CRITICAL
    elif score >= 0.45:
        level = RiskLevel.HIGH
    elif score >= 0.20:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    return round(score, 4), level, factors


def check_eta_conflict(shipment: Shipment) -> Tuple[bool, Optional[str]]:
    """
    Detects ETA/ETD conflicts.
    Returns (has_conflict: bool, reason: Optional[str])
    """
    reasons = []

    if shipment.etd and shipment.eta:
        etd = shipment.etd
        eta = shipment.eta
        if etd.tzinfo is None:
            etd = etd.replace(tzinfo=timezone.utc)
        if eta.tzinfo is None:
            eta = eta.replace(tzinfo=timezone.utc)

        if eta <= etd:
            reasons.append("ETA is not after ETD — impossible schedule")

        transit_days = (eta - etd).total_seconds() / 86400
        # Mode-based expected transit time sanity checks
        max_transit = {
            ShipmentMode.AIR: 5,
            ShipmentMode.ROAD: 14,
            ShipmentMode.RAIL: 21,
            ShipmentMode.SEA: 60,
            ShipmentMode.MULTIMODAL: 45,
        }
        limit = max_transit.get(shipment.mode, 90)
        if transit_days > limit:
            reasons.append(
                f"Transit time {transit_days:.0f} days exceeds typical max {limit} days for {shipment.mode.value} mode"
            )

    # Check if ETA is already passed but status not delivered
    if shipment.eta and shipment.status not in (ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED):
        eta = shipment.eta
        if eta.tzinfo is None:
            eta = eta.replace(tzinfo=timezone.utc)
        if eta < datetime.now(timezone.utc):
            reasons.append("ETA has passed but shipment is not yet delivered")

    # Check last tracking event vs current status conflict
    if shipment.tracking_events:
        last_event = shipment.tracking_events[0]  # ordered desc
        if last_event.status == ShipmentStatus.DELIVERED and shipment.status != ShipmentStatus.DELIVERED:
            reasons.append("Last tracking event shows delivered but shipment status is not delivered")
        if shipment.status == ShipmentStatus.DELIVERED and last_event.status != ShipmentStatus.DELIVERED:
            reasons.append("Shipment marked delivered but latest tracking event disagrees")

    if reasons:
        return True, "; ".join(reasons)
    return False, None


def update_shipment_risk(shipment: Shipment) -> None:
    """Mutates shipment in-place with updated risk data."""
    has_conflict, conflict_reason = check_eta_conflict(shipment)
    shipment.has_eta_conflict = has_conflict
    shipment.eta_conflict_reason = conflict_reason

    score, level, factors = compute_risk(shipment)
    shipment.risk_score = score
    shipment.risk_level = level
    shipment.risk_factors = json.dumps(factors)
