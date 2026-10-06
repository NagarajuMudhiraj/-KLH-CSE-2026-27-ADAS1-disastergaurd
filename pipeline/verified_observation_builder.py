"""Verified observation dataset builder for Phase 4 ADAS road-risk pipeline.
Implements temporal and spatial alignment, label source separation, event-based partitioning,
and exports intermediate JSONL, CSV, and Parquet datasets.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import polars as pl
from app.models.schemas import RoadRiskFeatures
from app.services.feature_builder import (
    CANONICAL_FEATURE_ORDER,
    assess_data_quality,
    build_canonical_feature_dict,
)
from pipeline.label_separator import LabelSeparator, SeparationResult
from pipeline.real_data_collector import RealDataCollector

logger = logging.getLogger(__name__)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class VerifiedObservationBuilder:
    """Constructs, validates, and partitions verified real-world road-risk observations."""

    def __init__(
        self,
        intermediate_dir: Optional[Path] = None,
        processed_dir: Optional[Path] = None,
    ) -> None:
        self.intermediate_dir = Path(intermediate_dir or (root_dir / "data" / "intermediate"))
        self.processed_dir = Path(processed_dir or (root_dir / "data" / "processed"))
        self.intermediate_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.collector = RealDataCollector()
        self.separator = LabelSeparator(allow_masking=True)

    def assemble_real_observation(
        self,
        obs_id: str,
        lat: float,
        lon: float,
        timestamp_utc: str,
        event_id: str,
        segment_id: str,
        session_id: str,
        raw_weather: Dict[str, Any],
        raw_elevation: float,
        raw_yolo: Dict[str, Any],
        ground_truth: Dict[str, Any],
        split_candidate: str = "TRAIN_CANDIDATE",
        data_classification: str = "REAL",
    ) -> Dict[str, Any]:
        """Assembles a verified observation with temporal consistency and strict schema validation."""

        # 1. Temporal consistency check
        # Feature retrieval timestamp must be <= observation timestamp t
        obs_dt = datetime.fromisoformat(timestamp_utc)
        weather_time = raw_weather.get("time") or timestamp_utc
        # Verify no future leakage
        try:
            w_dt = datetime.fromisoformat(weather_time)
            if w_dt.tzinfo is None:
                w_dt = w_dt.replace(tzinfo=timezone.utc)
            if obs_dt.tzinfo is None:
                obs_dt = obs_dt.replace(tzinfo=timezone.utc)
            if w_dt > obs_dt:
                logger.warning(f"Temporal violation: weather ({w_dt}) is in future of observation ({obs_dt})")
        except Exception:
            pass

        # 2. Extract features into raw dictionary
        combined_raw: Dict[str, Any] = {
            "rainfall_mm_h": float(raw_weather.get("precipitation", 0.0)),
            "rainfall_10min_mm": round(float(raw_weather.get("precipitation", 0.0)) / 6.0, 2),
            "rainfall_1h_mm": float(raw_weather.get("rain_1h", raw_weather.get("precipitation", 0.0))),
            "visibility_m": min(10000.0, max(0.0, float(raw_weather.get("visibility", 10000.0)))),
            "temperature_c": float(raw_weather.get("temperature_2m", raw_weather.get("temp", 25.0))),
            "wind_speed_kmh": float(raw_weather.get("wind_speed_10m", raw_weather.get("wind_speed", 10.0))),
            "traffic_level": float(raw_weather.get("traffic_level", 2.0)),
            "vehicle_density": float(raw_weather.get("vehicle_density", 20.0)),
            "congestion_change": 0.0,
            "vehicle_speed_kmh": 40.0,
            "acceleration_mps2": 0.0,
            "braking_intensity": 0.0,
            "road_slope_pct": 0.5,
            "elevation_m": float(raw_elevation),
            "road_type": 1,  # Highway default in disaster zones
            "vehicle_count": int(raw_yolo.get("vehicle_count", 0)),
            "person_count": int(raw_yolo.get("person_count", 0)),
            "fire_detected": int(raw_yolo.get("fire_detected", 0)),
            "smoke_detected": int(raw_yolo.get("smoke_detected", 0)),
            "flood_detected": int(raw_yolo.get("flood_detected", 0)),
            "obstacle_count": int(raw_yolo.get("obstacle_count", 0)),
            "hazard_count": int(raw_yolo.get("hazard_count", 0)),
            "hazard_distance_m": float(raw_yolo.get("hazard_distance_m", 500.0)),
            "flood_report": int(raw_weather.get("flood_report", 0)),
            "road_closure_report": int(raw_weather.get("road_closure_report", 0)),
        }

        # 3. Canonical feature formatting
        canonical_features = build_canonical_feature_dict(combined_raw)

        # 4. Label source separation to prevent leakage
        separation: SeparationResult = self.separator.separate_label_and_features(
            canonical_features, ground_truth
        )

        # 5. Pydantic validation
        validated_schema = RoadRiskFeatures(**separation.features)
        feature_dict = validated_schema.model_dump()

        # 6. Quality tier assessment
        data_quality = assess_data_quality(feature_dict)

        return {
            "metadata": {
                "observation_id": obs_id,
                "timestamp": timestamp_utc,
                "latitude": float(lat),
                "longitude": float(lon),
                "segment_id": segment_id,
                "event_id": event_id,
                "session_id": session_id,
                "split_candidate": split_candidate,
                "data_quality": data_quality,
                "source_classification": data_classification,
                "has_label_source_exclusion": separation.has_exclusion,
                "excluded_features": separation.excluded_features,
                "exclusion_reason": separation.exclusion_reason,
            },
            "features": feature_dict,
            "ground_truth": separation.label_info,
        }

    def build_real_disaster_dataset(
        self,
        max_samples: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return no rows until FloodNet supplies capture time and geolocation.

        Earlier versions generated Houston offsets and used retrieval time as the
        observation time.  Those rows remain in legacy artifacts for audit, but
        this method must never recreate them as REAL records.
        """
        logger.warning(
            "FloodNet tabular collection is fail-closed: source-native image "
            "coordinates and capture timestamps are unavailable. Returning no REAL observations."
        )
        return []

        # Legacy implementation retained below only for historical context and
        # is intentionally unreachable.
        logger.info(f"Building real verified observations (target: {max_samples})...")
        images_dir = root_dir / "datasets" / "floodnet_yolo" / "images" / "val"
        labels_dir = root_dir / "datasets" / "floodnet_yolo" / "labels" / "val"

        if not images_dir.exists():
            images_dir = root_dir / "datasets" / "floodnet_yolo" / "images" / "train"
            labels_dir = root_dir / "datasets" / "floodnet_yolo" / "labels" / "train"

        # Hurricane Harvey geographic center (Houston / Coastal Texas)
        houston_coords = (29.7604, -95.3698)

        # Fetch real live weather for Houston disaster center
        temp_obs_id = str(uuid.uuid4())
        weather_payload = self.collector.fetch_real_weather(houston_coords[0], houston_coords[1], temp_obs_id)
        current_w = weather_payload.get("raw_payload", {}).get("current", {}) if weather_payload else {}

        # Fetch real live elevation for Houston
        elevation_payload = self.collector.fetch_real_elevation(houston_coords[0], houston_coords[1], temp_obs_id)
        elevation_val = elevation_payload.get("provenance", {}).get("elevation_m", 15.0) if elevation_payload else 15.0

        # Query USGS water services for Texas/Gulf stream gauge
        self.collector.fetch_real_hydrology_usgs("08074000", temp_obs_id)  # Buffalo Bayou at Houston, TX

        image_files = sorted(list(images_dir.glob("*.jpg")))[:max_samples]
        observations: List[Dict[str, Any]] = []

        for idx, img_path in enumerate(image_files):
            stem = img_path.stem
            label_file = labels_dir / f"{stem}.txt"
            label_path = label_file if label_file.exists() else None

            # Spatial jitter within disaster zone
            sample_lat = round(houston_coords[0] + (idx * 0.002), 4)
            sample_lon = round(houston_coords[1] + (idx * 0.002), 4)
            obs_id = str(uuid.uuid4())
            ts_str = datetime.now(timezone.utc).isoformat()

            # Process real sample
            processed = self.collector.process_real_floodnet_sample(
                image_path=img_path,
                label_path=label_path,
                lat=sample_lat,
                lon=sample_lon,
                event_name="Hurricane_Harvey_FloodNet",
            )
            if not processed:
                continue

            # Assign candidate partition by event & index to avoid same-event contamination
            # 70% Train, 15% Val, 15% Test
            if idx % 6 == 0:
                partition = "TEST_CANDIDATE"
            elif idx % 6 == 1:
                partition = "VALIDATION_CANDIDATE"
            else:
                partition = "TRAIN_CANDIDATE"

            obs = self.assemble_real_observation(
                obs_id=obs_id,
                lat=sample_lat,
                lon=sample_lon,
                timestamp_utc=ts_str,
                event_id="Hurricane_Harvey_FloodNet",
                segment_id=f"TX_HARVEY_SEG_{(idx % 8):03d}",
                session_id=f"FLIGHT_SESSION_{(idx // 15):02d}",
                raw_weather=current_w,
                raw_elevation=elevation_val,
                raw_yolo=processed["yolo_data"],
                ground_truth=processed["ground_truth"],
                split_candidate=partition,
                data_classification="REAL",
            )
            observations.append(obs)

        logger.info(f"Successfully assembled {len(observations)} real verified observations.")
        return observations

    def export_datasets(self, observations: List[Dict[str, Any]]) -> Dict[str, Path]:
        """Exports verified observations to intermediate JSONL, processed CSV, and Parquet."""
        jsonl_path = self.intermediate_dir / "road_risk_verified_observations.jsonl"
        csv_path = self.processed_dir / "road_risk_dataset_v2.csv"
        parquet_path = self.processed_dir / "road_risk_dataset_v2.parquet"

        # 1. Export JSONL (Intermediate)
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for obs in observations:
                f.write(json.dumps(obs) + "\n")
        logger.info(f"Exported intermediate JSONL to {jsonl_path}")

        # 2. Export CSV (Model-Ready)
        if observations:
            feat_keys = list(observations[0]["features"].keys())
            csv_headers = (
                [
                    "observation_id",
                    "timestamp",
                    "latitude",
                    "longitude",
                    "segment_id",
                    "event_id",
                    "session_id",
                    "split_candidate",
                    "data_quality",
                    "source_classification",
                    "label_source",
                    "label_quality",
                    "has_label_source_exclusion",
                ]
                + feat_keys
                + ["road_risk_status", "label_name", "label_reason"]
            )

            csv_rows = []
            for obs in observations:
                meta = obs.get("metadata", {})
                gt = obs.get("ground_truth", {})
                row = [
                    meta.get("observation_id"),
                    meta.get("timestamp"),
                    meta.get("latitude"),
                    meta.get("longitude"),
                    meta.get("segment_id"),
                    meta.get("event_id"),
                    meta.get("session_id"),
                    meta.get("split_candidate"),
                    meta.get("data_quality"),
                    meta.get("source_classification"),
                    gt.get("label_source"),
                    gt.get("label_quality"),
                    meta.get("has_label_source_exclusion"),
                ]
                row.extend([obs["features"].get(k, 0.0) for k in feat_keys])
                row.extend([
                    gt.get("road_risk_status"),
                    gt.get("label_name"),
                    gt.get("label_reason"),
                ])
                csv_rows.append(row)

            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(csv_headers)
                writer.writerows(csv_rows)
            logger.info(f"Exported model-ready CSV to {csv_path}")

            # 3. Export Parquet (Optimized for XGBoost / Polars)
            try:
                df = pl.read_csv(csv_path)
                df.write_parquet(parquet_path)
                logger.info(f"Exported model-ready Parquet to {parquet_path}")
            except Exception as e:
                logger.warning(f"Parquet export failed ({e}); CSV remains valid.")

        return {
            "jsonl": jsonl_path,
            "csv": csv_path,
            "parquet": parquet_path,
        }
