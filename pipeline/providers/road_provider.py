"""Road physical infrastructure and topographical feature provider.
Provides canonical features from config/road_risk_features.json:
- road_slope_pct (float, -35.0 to 35.0)
- elevation_m (float, -100.0 to 6000.0)
- road_type (int, 0:Urban, 1:Highway, 2:Rural, 3:Bridge, 4:Tunnel)
"""
from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pipeline.providers.base import BaseProvider, ProviderMode, ProviderResult, SourceClassification


class RoadProvider(BaseProvider):
    """Provides road infrastructure and terrain features."""

    SUPPORTED_FEATURES = [
        "road_slope_pct",
        "elevation_m",
        "road_type",
    ]

    def __init__(
        self,
        mode: ProviderMode = ProviderMode.SIMULATOR,
        fixture_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mode=mode, name="RoadProvider")
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
            return self._generate_simulated_road(scenario=scenario, now_utc=now_utc)

        # No DEM + road-geometry connector is configured. Do not manufacture
        # slope, elevation, or a road class from generic city defaults.
        return ProviderResult(
            provider_name=self.name,
            mode=self.mode,
            source_classification=SourceClassification.UNAVAILABLE,
            timestamp_utc=now_utc,
            data={},
            raw_payload=None,
            is_available=False,
            error_message="No verified DEM/road-geometry source is configured.",
            metadata={"source": "unavailable", "feature_status": "FUTURE"},
        )

    def _generate_simulated_road(self, scenario: Optional[str], now_utc: str) -> ProviderResult:
        scenario = scenario or random.choice(["urban_arterial", "highway", "mountain_pass", "low_lying_suburb"])

        if scenario == "urban_arterial":
            data = {"road_slope_pct": round(random.uniform(0.5, 3.0), 1), "elevation_m": round(random.uniform(50.0, 300.0), 1), "road_type": 0}
        elif scenario == "highway":
            data = {"road_slope_pct": round(random.uniform(0.0, 2.0), 1), "elevation_m": round(random.uniform(50.0, 400.0), 1), "road_type": 1}
        elif scenario == "mountain_pass":
            data = {"road_slope_pct": round(random.uniform(6.0, 22.0), 1), "elevation_m": round(random.uniform(800.0, 2400.0), 1), "road_type": 2}
        elif scenario == "low_lying_suburb":
            data = {"road_slope_pct": round(random.uniform(-1.0, 1.0), 1), "elevation_m": round(random.uniform(5.0, 35.0), 1), "road_type": 0}
        else:
            data = {"road_slope_pct": 0.0, "elevation_m": 200.0, "road_type": 0}

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
