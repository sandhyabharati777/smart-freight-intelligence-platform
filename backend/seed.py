"""
Seed script: populates the database with demo data.
Run: python seed.py

All seeded data is clearly marked as DEMO/SIMULATED.
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from app.db.session import AsyncSessionLocal, engine
from app.db.models import Base, User, Shipment, TrackingEvent, Notification, ShipmentStatus, ShipmentMode, RiskLevel, NotificationType
from app.core.security import get_password_hash
from app.services.risk import update_shipment_risk


DEMO_USERS = [
    {"email": "admin@smartfreight.demo", "username": "admin", "password": "Admin@123", "full_name": "Admin User", "is_admin": True},
    {"email": "ops@smartfreight.demo", "username": "ops_manager", "password": "Demo@1234", "full_name": "Operations Manager"},
]

now = datetime.now(timezone.utc)

DEMO_SHIPMENTS = [
    {
        "tracking_number": "SF-AIR-001",
        "title": "Electronics Components - PCBs",
        "origin_location": "Shenzhen, China",
        "destination_location": "Frankfurt, Germany",
        "origin_country": "China",
        "destination_country": "Germany",
        "carrier": "DHL Air Freight [SIMULATED]",
        "mode": ShipmentMode.AIR,
        "status": ShipmentStatus.IN_TRANSIT,
        "eta": now + timedelta(days=2),
        "etd": now - timedelta(days=1),
        "weight_kg": 450.0,
        "value_usd": 85000.0,
    },
    {
        "tracking_number": "SF-SEA-002",
        "title": "Industrial Machinery Parts",
        "origin_location": "Shanghai, China",
        "destination_location": "Rotterdam, Netherlands",
        "origin_country": "China",
        "destination_country": "Netherlands",
        "carrier": "COSCO Shipping [SIMULATED]",
        "mode": ShipmentMode.SEA,
        "status": ShipmentStatus.CUSTOMS,
        "eta": now + timedelta(days=5),
        "etd": now - timedelta(days=20),
        "weight_kg": 12000.0,
        "value_usd": 320000.0,
    },
    {
        "tracking_number": "SF-SEA-003",
        "title": "Automotive Components",
        "origin_location": "Busan, South Korea",
        "destination_location": "Los Angeles, USA",
        "origin_country": "South Korea",
        "destination_country": "USA",
        "carrier": "HMM [SIMULATED]",
        "mode": ShipmentMode.SEA,
        "status": ShipmentStatus.DELAYED,
        "eta": now - timedelta(days=3),  # overdue!
        "etd": now - timedelta(days=25),
        "weight_kg": 8500.0,
        "value_usd": 150000.0,
    },
    {
        "tracking_number": "SF-ROAD-004",
        "title": "Pharmaceutical Supplies",
        "origin_location": "Paris, France",
        "destination_location": "Warsaw, Poland",
        "origin_country": "France",
        "destination_country": "Poland",
        "carrier": "DB Schenker [SIMULATED]",
        "mode": ShipmentMode.ROAD,
        "status": ShipmentStatus.IN_TRANSIT,
        "eta": now + timedelta(days=1),
        "etd": now - timedelta(days=2),
        "weight_kg": 200.0,
        "value_usd": 45000.0,
    },
    {
        "tracking_number": "SF-AIR-005",
        "title": "Fashion Retail - Q4 Collection",
        "origin_location": "Mumbai, India",
        "destination_location": "Dubai, UAE",
        "origin_country": "India",
        "destination_country": "UAE",
        "carrier": "Emirates SkyCargo [SIMULATED]",
        "mode": ShipmentMode.AIR,
        "status": ShipmentStatus.DELIVERED,
        "eta": now - timedelta(days=2),
        "etd": now - timedelta(days=5),
        "actual_delivery": now - timedelta(days=2, hours=3),
        "weight_kg": 350.0,
        "value_usd": 22000.0,
    },
    {
        "tracking_number": "SF-RAIL-006",
        "title": "Raw Steel Coils",
        "origin_location": "Moscow, Russia",
        "destination_location": "Berlin, Germany",
        "origin_country": "Russia",
        "destination_country": "Germany",
        "carrier": "RZD Logistics [SIMULATED]",
        "mode": ShipmentMode.RAIL,
        "status": ShipmentStatus.PENDING,
        "eta": now + timedelta(days=14),
        "etd": now + timedelta(days=2),
        "weight_kg": 50000.0,
        "value_usd": 180000.0,
    },
    {
        "tracking_number": "SF-MULTI-007",
        "title": "Consumer Electronics - Mixed Cargo",
        "origin_location": "Taipei, Taiwan",
        "destination_location": "Chicago, USA",
        "origin_country": "Taiwan",
        "destination_country": "USA",
        "carrier": "Multimodal Alliance [SIMULATED]",
        "mode": ShipmentMode.MULTIMODAL,
        "status": ShipmentStatus.IN_TRANSIT,
        "eta": now + timedelta(days=8),
        "etd": now - timedelta(days=10),
        "weight_kg": 3200.0,
        "value_usd": 420000.0,
    },
    {
        "tracking_number": "SF-SEA-008",
        "title": "Agricultural Products - Soybeans",
        "origin_location": "Santos, Brazil",
        "destination_location": "Qingdao, China",
        "origin_country": "Brazil",
        "destination_country": "China",
        "carrier": "MSC [SIMULATED]",
        "mode": ShipmentMode.SEA,
        "status": ShipmentStatus.IN_TRANSIT,
        "eta": now + timedelta(days=18),
        "etd": now - timedelta(days=15),
        "weight_kg": 28000.0,
        "value_usd": 95000.0,
    },
]

TRACKING_EVENTS_TEMPLATE = {
    "SF-AIR-001": [
        {"status": ShipmentStatus.PENDING, "location": "Shenzhen, China", "description": "Shipment booked [SIMULATED]", "delta_days": -2},
        {"status": ShipmentStatus.IN_TRANSIT, "location": "Hong Kong Airport, China", "description": "Departed Hong Kong [SIMULATED]", "delta_days": -1},
        {"status": ShipmentStatus.IN_TRANSIT, "location": "Dubai, UAE", "description": "Transit stop - Dubai [SIMULATED]", "delta_days": 0},
    ],
    "SF-SEA-002": [
        {"status": ShipmentStatus.PENDING, "location": "Shanghai Port, China", "description": "Container loaded [SIMULATED]", "delta_days": -22},
        {"status": ShipmentStatus.IN_TRANSIT, "location": "Pacific Ocean", "description": "Departed Shanghai [SIMULATED]", "delta_days": -20},
        {"status": ShipmentStatus.IN_TRANSIT, "location": "Suez Canal", "description": "Passing Suez Canal [SIMULATED]", "delta_days": -8},
        {"status": ShipmentStatus.CUSTOMS, "location": "Rotterdam Port, Netherlands", "description": "Arrived — held for customs inspection [SIMULATED]", "delta_days": -1},
    ],
    "SF-SEA-003": [
        {"status": ShipmentStatus.PENDING, "location": "Busan Port, South Korea", "description": "Cargo loaded [SIMULATED]", "delta_days": -26},
        {"status": ShipmentStatus.IN_TRANSIT, "location": "Pacific Ocean", "description": "Vessel departed Busan [SIMULATED]", "delta_days": -25},
        {"status": ShipmentStatus.DELAYED, "location": "Pacific Ocean", "description": "Weather delay — vessel rerouted [SIMULATED]", "delta_days": -5},
    ],
}


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Create users
        users = {}
        for u in DEMO_USERS:
            from sqlalchemy import select
            existing = await db.execute(select(User).where(User.email == u["email"]))
            if not existing.scalar_one_or_none():
                user = User(
                    email=u["email"],
                    username=u["username"],
                    full_name=u.get("full_name"),
                    hashed_password=get_password_hash(u["password"]),
                    is_admin=u.get("is_admin", False),
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                users[u["username"]] = user
                print(f"  Created user: {u['email']}")
            else:
                result = await db.execute(select(User).where(User.email == u["email"]))
                users[u["username"]] = result.scalar_one()

        admin_user = users.get("admin")
        if not admin_user:
            print("Admin user not found, skipping shipment seeding")
            return

        # Create shipments
        for s_data in DEMO_SHIPMENTS:
            from sqlalchemy import select
            existing = await db.execute(
                select(Shipment).where(Shipment.tracking_number == s_data["tracking_number"])
            )
            if existing.scalar_one_or_none():
                print(f"  Shipment {s_data['tracking_number']} already exists, skipping")
                continue

            shipment = Shipment(**s_data, owner_id=admin_user.id)
            # Special: mark stale shipment
            if shipment.status == ShipmentStatus.DELAYED:
                shipment.last_update_at = now - timedelta(days=4)
                shipment.is_stale = True

            update_shipment_risk(shipment)
            db.add(shipment)
            await db.commit()
            await db.refresh(shipment)

            # Add tracking events
            events_data = TRACKING_EVENTS_TEMPLATE.get(shipment.tracking_number, [])
            if not events_data:
                # Default initial event
                events_data = [
                    {
                        "status": shipment.status,
                        "location": shipment.origin_location,
                        "description": f"Shipment created [SIMULATED]",
                        "delta_days": -1,
                    }
                ]
            for ev in events_data:
                event = TrackingEvent(
                    shipment_id=shipment.id,
                    status=ev["status"],
                    location=ev.get("location"),
                    description=ev.get("description"),
                    event_time=now + timedelta(days=ev.get("delta_days", 0)),
                    is_simulated=True,
                )
                db.add(event)
            await db.commit()
            print(f"  Created shipment: {shipment.tracking_number} [{shipment.status.value}]")

        # Create some notifications
        notifs = [
            Notification(
                user_id=admin_user.id,
                type=NotificationType.DELAY_RISK,
                title="High Risk Shipment Alert",
                message="Shipment SF-SEA-003 (Automotive Components) has a critical delay risk — ETA passed 3 days ago",
            ),
            Notification(
                user_id=admin_user.id,
                type=NotificationType.ETA_CONFLICT,
                title="ETA Conflict Detected",
                message="Shipment SF-SEA-003: ETA has passed but shipment is not yet delivered",
            ),
            Notification(
                user_id=admin_user.id,
                type=NotificationType.STALE_UPDATE,
                title="Stale Tracking Alert",
                message="No tracking updates for SF-SEA-003 in 4+ days",
            ),
            Notification(
                user_id=admin_user.id,
                type=NotificationType.SYSTEM,
                title="Welcome to Smart Freight Platform",
                message="Your account is configured with demo data. All carrier data is simulated.",
                is_read=True,
            ),
        ]
        for n in notifs:
            db.add(n)
        await db.commit()
        print(f"  Created {len(notifs)} demo notifications")

    print("\n✅ Seed complete!")
    print("  Demo login: admin@smartfreight.demo / Admin@123")
    print("  All carrier/tracking data is clearly labeled [SIMULATED]")


if __name__ == "__main__":
    asyncio.run(seed())
