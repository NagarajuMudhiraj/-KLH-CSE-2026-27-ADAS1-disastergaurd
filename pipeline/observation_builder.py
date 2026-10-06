"""Observation record builder for ADAS road-risk pipeline.
Combines outputs across all data providers, validates through canonical schemas,
and packages rich provenance metadata.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to sys.path to access app.services.feature_builder and app.models.schemas
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.schemas import RoadRiskFeatures
from app.services.feature_builder import (
    CANONICAL_FEATURE_ORDER,
    assess_data_quality,
    build_canonical_feature_dict,
)
from pipeline.providers.base import (
    BaseProvider,
    ProviderMode,
    ProviderResult,
    SourceClassification,
)
from pipeline.providers.disaster_provider import DisasterReportProvider
from pipeline.providers.road_provider import RoadProvider
from pipeline.providers.telemetry_provider import TelemetryProvider
from pipeline.providers.traffic_provider import TrafficProvider
from pipeline.providers.weather_provider import WeatherProvider
from pipeline.providers.yolo_feature_provider import YOLOFeatureProvider


class ObservationBuilder:
    """Assembles a canonical 25-feature observation vector with full spatial-temporal metadata."""

    def __init__(
        self,
        weather_provider: Optional[WeatherProvider] = None,
        yolo_provider: Optional[YOLOFeatureProvider] = None,
        disaster_provider: Optional[DisasterReportProvider] = None,
        road_provider: Optional[RoadProvider] = None,
        traffic_provider: Optional[TrafficProvider] = None,
        telemetry_provider: Optional[TelemetryProvider] = None,
    ) -> None:
        self.weather = weather_provider or WeatherProvider(mode=ProviderMode.SIMULATOR)
        self.yolo = yolo_provider or YOLOFeatureProvider(mode=ProviderMode.SIMULATOR)
        self.disaster = disaster_provider or DisasterReportProvider(mode=ProviderMode.SIMULATOR)
        self.road = road_provider or RoadProvider(mode=ProviderMode.SIMULATOR)
        self.traffic = traffic_provider or TrafficProvider(mode=ProviderMode.SIMULATOR)
        self.telemetry = telemetry_provider or TelemetryProvider(mode=ProviderMode.SIMULATOR)

        self.providers: List[BaseProvider] = [
            self.weather,
            self.yolo,
            self.disaster,
            self.road,
            self.traffic,
            self.telemetry,
        ]

    def build_observation(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
        segment_id: Optional[str] = None,
        event_id: Optional[str] = None,
        session_id: Optional[str] = None,
        scenario: Optional[str] = None,
        image_input: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Collects from all providers and produces a validated observation record."""
        ts = timestamp or datetime.now(timezone.utc)
        obs_id = str(uuid.uuid4())

        combined_raw: Dict[str, Any] = {}
        provenance: Dict[str, Any] = {}
        classifications: List[SourceClassification] = []
        unavailable_features: List[str] = []

        # 1. Fetch from all providers
        provider_calls = [
            (self.weather, {"scenario": scenario}),
            (self.yolo, {"scenario": scenario, "image_input": image_input}),
            (self.disaster, {"scenario": scenario}),
            (self.road, {"scenario": scenario}),
            (self.traffic, {"scenario": scenario}),
            (self.telemetry, {"scenario": scenario}),
        ]

        for prov, extra_args in provider_calls:
            res: ProviderResult = prov.fetch(
                latitude=latitude,
                longitude=longitude,
                timestamp=ts,
                **extra_args,
                **kwargs,
            )
            combined_raw.update(res.data)
            classifications.append(res.source_classification)
            for feat_name in prov.supported_features:
                provenance[feat_name] = {
                    "provider": res.provider_name,
                    "source_name": res.source_name,
                    "mode": res.mode.value,
                    "source_classification": res.source_classification.value,
                    "is_available": res.is_available,
                    "observed_at": res.observed_at,
                    "retrieved_at": res.retrieved_at,
                    "location": res.location,
                    "provenance": res.provenance,
                    "data_quality": res.data_quality,
                }
                if not res.is_available or feat_name not in res.data:
                    unavailable_features.append(feat_name)

        # 2. Canonical feature normalization through feature_builder
        canonical_dict = build_canonical_feature_dict(combined_raw)

        # 3. Pydantic validation
        validated_schema = RoadRiskFeatures(**canonical_dict)
        features_dict = validated_schema.model_dump()

        # 4. Determine overall source classification
        # If any component is simulated, classify entire observation as REALISTIC_SIMULATION
        if any(c == SourceClassification.UNAVAILABLE for c in classifications):
            overall_source = SourceClassification.UNAVAILABLE.value
        elif any(c == SourceClassification.REALISTIC_SIMULATION for c in classifications):
            overall_source = SourceClassification.REALISTIC_SIMULATION.value
        elif all(c == SourceClassification.REAL for c in classifications):
            overall_source = SourceClassification.REAL.value
        else:
            overall_source = SourceClassification.SYNTHETIC_BENCHMARK.value

        # 5. Assess data quality
        quality = assess_data_quality(features_dict)

        return {
            "metadata": {
                "observation_id": obs_id,
                "timestamp": ts.isoformat(),
                "latitude": float(latitude),
                "longitude": float(longitude),
                "segment_id": segment_id,
                "event_id": event_id,
                "session_id": session_id,
                "data_quality": quality,
                "source_classification": overall_source,
                "excluded_from_real_training": bool(unavailable_features),
                "validation_reasons": (["UNAVAILABLE_PROVIDER_FEATURES"] if unavailable_features else []),
            },
            "features": features_dict,
            "provenance": provenance,
        }
