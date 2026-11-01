"""
Neo4j supply-chain relationship service.

Provides graph-based queries for supply chain relationships.
Falls back gracefully when Neo4j is unavailable.

NOTE: Data labeled [SIMULATED] when using the fallback.
"""
from typing import Optional, List, Dict, Any
from app.core.config import settings


class Neo4jService:
    def __init__(self):
        self.driver = None
        self._available = False
        self._connect()

    def _connect(self):
        if not settings.NEO4J_URI:
            return
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER or "neo4j", settings.NEO4J_PASSWORD or ""),
            )
            self.driver.verify_connectivity()
            self._available = True
        except Exception as e:
            self._available = False
            self.driver = None

    @property
    def is_available(self) -> bool:
        return self._available

    def get_supplier_chain(self, origin_country: str) -> Dict[str, Any]:
        """Get supply chain relationships for an origin country."""
        if not self._available:
            return {
                "available": False,
                "note": "Neo4j not configured. Set NEO4J_URI in .env to enable graph queries.",
                "simulated": True,
                "data": {
                    "origin": origin_country,
                    "suppliers": [
                        {"name": f"Supplier A [{origin_country}]", "type": "manufacturer", "risk": "low"},
                        {"name": f"Supplier B [{origin_country}]", "type": "logistics", "risk": "medium"},
                    ],
                    "routes": [
                        f"{origin_country} → Transit Hub → Destination"
                    ]
                }
            }

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (c:Country {name: $country})-[:HAS_SUPPLIER]->(s:Supplier)
                    OPTIONAL MATCH (s)-[:USES_ROUTE]->(r:Route)
                    RETURN s.name as supplier, s.type as type, s.risk_level as risk,
                           collect(r.name) as routes
                    LIMIT 10
                    """,
                    country=origin_country,
                )
                records = [dict(r) for r in result]
                return {"available": True, "data": records}
        except Exception as e:
            return {"available": False, "error": str(e), "note": "Neo4j query failed"}

    def close(self):
        if self.driver:
            self.driver.close()


# Singleton
neo4j_service = Neo4jService()
