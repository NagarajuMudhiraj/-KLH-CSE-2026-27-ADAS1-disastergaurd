"""Traffic monitoring feature provider for ADAS road-risk pipeline.
Provides canonical features from config/road_risk_features.json:
- traffic_level (float, 1.0 to 10.0)
- vehicle_density (float, 0.0 to 200.0 vehicles/km/lane)
- congestion_change (float, -10.0 to 10.0 index/hour)
"""
from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pipeline.providers.base import BaseProvider, ProviderMode, ProviderResult, SourceClassification


class TrafficProvider(BaseProvider):
    """Provides traffic congestion and density features."""

    SUPPORTED_FEATURES = [
        "traffic_level",
        "vehicle_density",
        "congestion_change",
    ]

    def __init__(
        self,
        mode: ProviderMode = ProviderMode.SIMULATOR,
        fixture_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mode=mode, name="TrafficProvider")
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
            return self._generate_simulated_traffic(scenario=scenario, now_utc=now_utc)

        # There is no connected, verified traffic source. Never return a
        # plausible baseline under LIVE; callers must handle absence explicitly.
        return ProviderResult(
            provider_name=self.name,
            mode=self.mode,
            source_classification=SourceClassification.UNAVAILABLE,
            timestamp_utc=now_utc,
            data={},
            raw_payload=None,
            is_available=False,
            error_message="No verified live or historical traffic provider is configured.",
            metadata={"source": "unavailable", "feature_status": "FUTURE"},
        )

    def _generate_simulated_traffic(self, scenario: Optional[str], now_utc: str) -> ProviderResult:
        scenario = scenario or random.choice(["free_flow", "moderate", "congested", "standstill"])

        if scenario == "free_flow":
            data = {"traffic_level": round(random.uniform(1.0, 2.5), 1), "vehicle_density": round(random.uniform(5.0, 25.0), 1), "congestion_change": round(random.uniform(-1.0, 0.5), 1)}
        elif scenario == "moderate":
            data = {"traffic_level": round(random.uniform(3.0, 5.5), 1), "vehicle_density": round(random.uniform(25.0, 60.0), 1), "congestion_change": round(random.uniform(-0.5, 1.0), 1)}
        elif scenario == "congested":
            data = {"traffic_level": round(random.uniform(6.0, 8.0), 1), "vehicle_density": round(random.uniform(60.0, 110.0), 1), "congestion_change": round(random.uniform(0.5, 2.5), 1)}
        elif scenario == "standstill":
            data = {"traffic_level": round(random.uniform(8.5, 10.0), 1), "vehicle_density": round(random.uniform(110.0, 180.0), 1), "congestion_change": round(random.uniform(1.0, 4.0), 1)}
        else:
            # Simulator-only fallback; it is never a real observation.
            data = {"traffic_level": 3.0, "vehicle_density": 30.0, "congestion_change": 0.0}

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
