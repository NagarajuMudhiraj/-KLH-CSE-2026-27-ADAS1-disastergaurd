"""Vehicle onboard telemetry feature provider for ADAS road-risk pipeline.
Provides canonical features from config/road_risk_features.json:
- vehicle_speed_kmh (float, 0.0 to 200.0 km/h)
- acceleration_mps2 (float, -12.0 to 8.0 m/s^2)
- braking_intensity (float, 0.0 to 1.0)
"""
from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pipeline.providers.base import BaseProvider, ProviderMode, ProviderResult, SourceClassification


class TelemetryProvider(BaseProvider):
    """Provides vehicle onboard CAN bus telemetry features."""

    SUPPORTED_FEATURES = [
        "vehicle_speed_kmh",
        "acceleration_mps2",
        "braking_intensity",
    ]

    def __init__(
        self,
        mode: ProviderMode = ProviderMode.SIMULATOR,
        fixture_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mode=mode, name="TelemetryProvider")
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
            return self._generate_simulated_telemetry(scenario=scenario, now_utc=now_utc)

        # A CAN/OBD adapter is not connected; fail closed rather than inventing
        # a speed, acceleration, or braking measurement.
        return ProviderResult(
            provider_name=self.name,
            mode=self.mode,
            source_classification=SourceClassification.UNAVAILABLE,
            timestamp_utc=now_utc,
            data={},
            raw_payload=None,
            is_available=False,
            error_message="No verified CAN/OBD telemetry source is configured.",
            metadata={"source": "unavailable", "feature_status": "FUTURE_SENSOR"},
        )

    def _generate_simulated_telemetry(self, scenario: Optional[str], now_utc: str) -> ProviderResult:
        scenario = scenario or random.choice(["cruising_dry", "rain_driving", "emergency_stop", "stopped"])

        if scenario == "cruising_dry":
            data = {"vehicle_speed_kmh": round(random.uniform(40.0, 80.0), 1), "acceleration_mps2": round(random.uniform(-0.5, 0.8), 2), "braking_intensity": 0.0}
        elif scenario == "rain_driving":
            data = {"vehicle_speed_kmh": round(random.uniform(25.0, 50.0), 1), "acceleration_mps2": round(random.uniform(-1.0, 0.4), 2), "braking_intensity": round(random.uniform(0.1, 0.3), 2)}
        elif scenario == "emergency_stop":
            data = {"vehicle_speed_kmh": round(random.uniform(5.0, 20.0), 1), "acceleration_mps2": round(random.uniform(-7.0, -3.5), 2), "braking_intensity": round(random.uniform(0.7, 1.0), 2)}
        elif scenario == "stopped":
            data = {"vehicle_speed_kmh": 0.0, "acceleration_mps2": 0.0, "braking_intensity": 0.5}
        else:
            data = {"vehicle_speed_kmh": 40.0, "acceleration_mps2": 0.0, "braking_intensity": 0.0}

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
