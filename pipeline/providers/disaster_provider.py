"""Disaster hazard report provider for ADAS road-risk pipeline.
Queries MongoDB hazards or produces verified realistic simulation reports.
Provides:
- flood_report (0 or 1)
- road_closure_report (0 or 1)
"""
from __future__ import annotations

import logging
import os
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pipeline.providers.base import BaseProvider, ProviderMode, ProviderResult, SourceClassification

logger = logging.getLogger(__name__)


class DisasterReportProvider(BaseProvider):
    """Provides community and emergency disaster hazard report features:
    - flood_report (0 or 1)
    - road_closure_report (0 or 1)
    """

    SUPPORTED_FEATURES = [
        "flood_report",
        "road_closure_report",
    ]

    def __init__(
        self,
        mode: ProviderMode = ProviderMode.SIMULATOR,
        mongo_uri: Optional[str] = None,
        fixture_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mode=mode, name="DisasterReportProvider")
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.fixture_data = fixture_data or {}

    @property
    def supported_features(self) -> List[str]:
        return self.SUPPORTED_FEATURES

    def fetch(
        self,
        latitude: float = 0.0,
        longitude: float = 0.0,
        timestamp: Optional[datetime] = None,
        scenario: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        now_utc = (timestamp or datetime.now(timezone.utc)).isoformat()

        if self.mode == ProviderMode.FIXTURE:
            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.SYNTHETIC_BENCHMARK,
                timestamp_utc=now_utc,
                data={feat: self.fixture_data.get(feat, 0) for feat in self.SUPPORTED_FEATURES},
                raw_payload=self.fixture_data,
                is_available=True,
                metadata={"source": "fixture"},
            )

        if self.mode == ProviderMode.SIMULATOR:
            return self._generate_simulated_reports(scenario=scenario, now_utc=now_utc)

        # LIVE MODE: Attempt to query MongoDB
        return self._fetch_live_mongo(latitude=latitude, longitude=longitude, now_utc=now_utc)

    def _fetch_live_mongo(self, latitude: float, longitude: float, now_utc: str) -> ProviderResult:
        try:
            from pymongo import MongoClient

            client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=1000)
            db = client["adas_db"]
            # Look for active hazards within ~2km (approx 0.02 deg)
            query = {
                "latitude": {"$gte": latitude - 0.02, "$lte": latitude + 0.02},
                "longitude": {"$gte": longitude - 0.02, "$lte": longitude + 0.02},
                "is_active": True,
            }
            records = list(db["hazards"].find(query))

            has_flood = 1 if any("flood" in str(r.get("type", "")).lower() for r in records) else 0
            has_closure = 1 if any("closure" in str(r.get("type", "")).lower() or r.get("blocked", False) for r in records) else 0

            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.REAL,
                timestamp_utc=now_utc,
                data={"flood_report": has_flood, "road_closure_report": has_closure},
                raw_payload={"record_count": len(records)},
                is_available=True,
                metadata={"matched_hazards": len(records)},
            )
        except Exception as e:
            logger.info(f"MongoDB not reachable ({e}); disaster reports are unavailable")
            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.UNAVAILABLE,
                timestamp_utc=now_utc,
                data={},
                raw_payload=None,
                is_available=False,
                error_message=str(e),
                metadata={"status": "unavailable", "note": str(e)},
            )

    def _generate_simulated_reports(self, scenario: Optional[str], now_utc: str) -> ProviderResult:
        scenario = scenario or random.choice(["normal", "flood_zone", "blocked_route"])

        if scenario == "flood_zone":
            data = {"flood_report": 1, "road_closure_report": 0}
        elif scenario == "blocked_route":
            data = {"flood_report": 1, "road_closure_report": 1}
        else:
            data = {"flood_report": 0, "road_closure_report": 0}

        return ProviderResult(
            provider_name=self.name,
            mode=self.mode,
            source_classification=SourceClassification.REALISTIC_SIMULATION,
            timestamp_utc=now_utc,
            data=data,
            raw_payload={"scenario": scenario},
            is_available=True,
            metadata={"scenario": scenario},
        )
