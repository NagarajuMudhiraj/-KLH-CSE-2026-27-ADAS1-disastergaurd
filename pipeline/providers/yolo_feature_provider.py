"""YOLO visual hazard detection feature provider for ADAS road-risk pipeline.
Extracts canonical visual hazard counts and indicators consistent with config/road_risk_features.json:
- vehicle_count
- person_count
- fire_detected
- smoke_detected
- flood_detected
- obstacle_count
- hazard_count
- hazard_distance_m
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pipeline.providers.base import BaseProvider, ProviderMode, ProviderResult, SourceClassification

logger = logging.getLogger(__name__)


class YOLOFeatureProvider(BaseProvider):
    """Provides visual hazard features from camera frame inference or realistic simulation."""

    SUPPORTED_FEATURES = [
        "vehicle_count",
        "person_count",
        "fire_detected",
        "smoke_detected",
        "flood_detected",
        "obstacle_count",
        "hazard_count",
        "hazard_distance_m",
    ]

    def __init__(
        self,
        mode: ProviderMode = ProviderMode.SIMULATOR,
        model_path: Optional[str] = None,
        fixture_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mode=mode, name="YOLOFeatureProvider")
        self.model_path = model_path
        self.fixture_data = fixture_data or {}
        self._yolo_model = None

    @property
    def supported_features(self) -> List[str]:
        return self.SUPPORTED_FEATURES

    def _ensure_model_loaded(self) -> Any:
        if self._yolo_model is None:
            from ultralytics import YOLO

            path = self.model_path or "models/best.pt"
            if not Path(path).exists():
                path = "backend/models/best.pt"
            self._yolo_model = YOLO(path)
        return self._yolo_model

    def fetch(
        self,
        latitude: float = 0.0,
        longitude: float = 0.0,
        timestamp: Optional[datetime] = None,
        image_input: Optional[Union[str, bytes, Any]] = None,
        scenario: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        now_utc = (timestamp or datetime.now(timezone.utc)).isoformat()

        if self.mode == ProviderMode.FIXTURE:
            data = {feat: self.fixture_data.get(feat, 0) for feat in self.SUPPORTED_FEATURES}
            return ProviderResult(
                provider_name=self.name,
                mode=self.mode,
                source_classification=SourceClassification.SYNTHETIC_BENCHMARK,
                timestamp_utc=now_utc,
                data=data,
                raw_payload=self.fixture_data,
                is_available=True,
                metadata={"source": "fixture"},
            )

        if self.mode == ProviderMode.SIMULATOR or image_input is None:
            return self._generate_simulated_detections(scenario=scenario, now_utc=now_utc)

        # LIVE MODE with image_input
        return self._infer_from_image(image_input=image_input, now_utc=now_utc)

    def _infer_from_image(self, image_input: Any, now_utc: str) -> ProviderResult:
        try:
            model = self._ensure_model_loaded()
            results = model(image_input, verbose=False)

            counts = {
                "vehicle_count": 0,
                "person_count": 0,
                "fire_detected": 0,
                "smoke_detected": 0,
                "flood_detected": 0,
                "obstacle_count": 0,
                "hazard_count": 0,
                "hazard_distance_m": 500.0,
            }

            raw_detections = []
            for r in results:
                names = r.names
                for box in r.boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    label = names.get(cls_id, "").lower()
                    raw_detections.append({"label": label, "confidence": conf})

                    if conf < 0.35:
                        continue

                    if any(w in label for w in ["car", "truck", "bus", "motorcycle", "vehicle"]):
                        counts["vehicle_count"] += 1
                    elif any(w in label for w in ["person", "pedestrian", "victim"]):
                        counts["person_count"] += 1
                    elif "fire" in label:
                        counts["fire_detected"] = 1
                    elif "smoke" in label:
                        counts["smoke_detected"] = 1
                    elif any(w in label for w in ["flood", "water"]):
                        counts["flood_detected"] = 1
                    elif any(w in label for w in ["tree", "pole", "wire", "debris", "rubble", "rock"]):
                        counts["obstacle_count"] += 1

            hazard_total = (
                counts["fire_detected"]
                + counts["smoke_detected"]
                + counts["flood_detected"]
                + counts["obstacle_count"]
            )
            counts["hazard_count"] = hazard_total
            if hazard_total > 0:
                counts["hazard_distance_m"] = 25.0

            return ProviderResult(
                provider_name=self.name,
                mode=ProviderMode.LIVE,
                source_classification=SourceClassification.REAL,
                timestamp_utc=now_utc,
                data=counts,
                raw_payload={"detections": raw_detections},
                is_available=True,
                metadata={"detection_count": len(raw_detections)},
            )
        except Exception as e:
            logger.error(f"Live YOLO inference error: {e}")
            return ProviderResult(
                provider_name=self.name,
                mode=ProviderMode.LIVE,
                source_classification=SourceClassification.REAL,
                timestamp_utc=now_utc,
                data={
                    "vehicle_count": 0,
                    "person_count": 0,
                    "fire_detected": 0,
                    "smoke_detected": 0,
                    "flood_detected": 0,
                    "obstacle_count": 0,
                    "hazard_count": 0,
                    "hazard_distance_m": 500.0,
                },
                raw_payload=None,
                is_available=False,
                error_message=str(e),
            )

    def _generate_simulated_detections(self, scenario: Optional[str], now_utc: str) -> ProviderResult:
        scenario = scenario or random.choice(["clear", "water_hazard", "blocked_tree", "urban_crowd", "fire_hazard"])

        data = {
            "vehicle_count": 0,
            "person_count": 0,
            "fire_detected": 0,
            "smoke_detected": 0,
            "flood_detected": 0,
            "obstacle_count": 0,
            "hazard_count": 0,
            "hazard_distance_m": 500.0,
        }

        if scenario == "clear":
            data["vehicle_count"] = random.randint(1, 5)
            data["person_count"] = random.randint(0, 2)
        elif scenario == "water_hazard":
            data["flood_detected"] = 1
            data["vehicle_count"] = random.randint(0, 2)
            data["hazard_count"] = 1
            data["hazard_distance_m"] = round(random.uniform(15.0, 60.0), 1)
        elif scenario == "blocked_tree":
            data["obstacle_count"] = random.randint(1, 3)
            data["hazard_count"] = data["obstacle_count"]
            data["hazard_distance_m"] = round(random.uniform(10.0, 30.0), 1)
            data["vehicle_count"] = random.randint(0, 2)
        elif scenario == "urban_crowd":
            data["vehicle_count"] = random.randint(8, 25)
            data["person_count"] = random.randint(4, 15)
        elif scenario == "fire_hazard":
            data["fire_detected"] = 1
            data["smoke_detected"] = 1
            data["hazard_count"] = 2
            data["hazard_distance_m"] = round(random.uniform(20.0, 50.0), 1)
            data["vehicle_count"] = random.randint(0, 2)

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
