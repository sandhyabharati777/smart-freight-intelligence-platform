"""Tests for risk scoring service."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from app.db.models import Shipment, ShipmentStatus, ShipmentMode, RiskLevel
from app.services.risk import compute_risk, check_eta_conflict, update_shipment_risk


def make_shipment(**kwargs):
    s = MagicMock(spec=Shipment)
    s.status = kwargs.get("status", ShipmentStatus.IN_TRANSIT)
    s.mode = kwargs.get("mode", ShipmentMode.SEA)
    s.eta = kwargs.get("eta", None)
    s.etd = kwargs.get("etd", None)
    s.has_eta_conflict = kwargs.get("has_eta_conflict", False)
    s.eta_conflict_reason = kwargs.get("eta_conflict_reason", None)
    s.is_stale = kwargs.get("is_stale", False)
    s.value_usd = kwargs.get("value_usd", None)
    s.tracking_events = kwargs.get("tracking_events", [])
    return s


def test_delivered_shipment_low_risk():
    # AIR mode has 0 mode risk, so total risk for a delivered shipment should be 0.0
    s = make_shipment(status=ShipmentStatus.DELIVERED, mode=ShipmentMode.AIR)
    score, level, factors = compute_risk(s)
    assert score == 0.0
    assert level == RiskLevel.LOW


def test_delayed_shipment_high_risk():
    now = datetime.now(timezone.utc)
    s = make_shipment(
        status=ShipmentStatus.DELAYED,
        eta=now - timedelta(days=2),  # overdue
    )
    score, level, factors = compute_risk(s)
    assert score > 0.4
    assert level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert any("delayed" in f.lower() for f in factors)


def test_stale_shipment_adds_risk():
    s = make_shipment(is_stale=True)
    score_no_stale, _, _ = compute_risk(make_shipment(is_stale=False))
    score_stale, _, _ = compute_risk(s)
    assert score_stale > score_no_stale


def test_eta_conflict_detection_past_eta():
    now = datetime.now(timezone.utc)
    s = make_shipment(
        status=ShipmentStatus.IN_TRANSIT,
        eta=now - timedelta(days=1),
    )
    has_conflict, reason = check_eta_conflict(s)
    assert has_conflict
    assert "passed" in reason.lower()


def test_no_conflict_valid_schedule():
    now = datetime.now(timezone.utc)
    s = make_shipment(
        status=ShipmentStatus.IN_TRANSIT,
        mode=ShipmentMode.AIR,
        etd=now - timedelta(days=1),
        eta=now + timedelta(days=2),
    )
    has_conflict, reason = check_eta_conflict(s)
    assert not has_conflict


def test_eta_before_etd_conflict():
    now = datetime.now(timezone.utc)
    s = make_shipment(
        etd=now + timedelta(days=3),
        eta=now + timedelta(days=1),  # eta before etd!
    )
    has_conflict, reason = check_eta_conflict(s)
    assert has_conflict
    assert "not after" in reason.lower()
