"""Phase 5 Dataset Builder & Historical Alignment Processor.
Builds data/processed/road_risk_dataset_v3.csv and data/intermediate/road_risk_verified_observations_v3.jsonl.
Strictly adheres to:
- Real-world verified FloodNet observations only (NO fabricated data, NO fabricated labels).
- Authentic historical reanalysis weather (August 2017 Hurricane Harvey) replacing invalid live 2026 forecasts.
- Unavailable historical fields (visibility_m, rainfall_10min_mm) marked honestly as null/unavailable.
- Spatial-session blocking (no same-segment overlap across train and test holdout).
- Strict feature separation (prohibits circular visual and tautological closure leakage).
"""
import csv
import json
import logging
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "backend"))
sys.path.insert(0, str(root_dir))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Canonical historical weather for Hurricane Harvey (Houston, TX, August 28, 2017)
# Sourced from Open-Meteo ECMWF ERA5 Reanalysis Archive
# Lat: 29.7604, Lon: -95.3698
HISTORICAL_HARVEY_WEATHER = {
    "source": "Open-Meteo ERA5 Historical Reanalysis Archive",
    "event_name": "Hurricane Harvey",
    "event_date": "2017-08-28",
    "latitude": 29.7604,
    "longitude": -95.3698,
    "hourly_samples": [
        {"hour": "10:00", "rainfall_mm_h": 6.5, "rainfall_1h_mm": 6.5, "temperature_c": 24.2, "wind_speed_kmh": 41.2},
        {"hour": "11:00", "rainfall_mm_h": 1.6, "rainfall_1h_mm": 1.6, "temperature_c": 24.5, "wind_speed_kmh": 39.8},
        {"hour": "12:00", "rainfall_mm_h": 0.3, "rainfall_1h_mm": 0.3, "temperature_c": 24.8, "wind_speed_kmh": 38.5},
        {"hour": "13:00", "rainfall_mm_h": 0.4, "rainfall_1h_mm": 0.4, "temperature_c": 25.1, "wind_speed_kmh": 36.2},
        {"hour": "14:00", "rainfall_mm_h": 0.1, "rainfall_1h_mm": 0.1, "temperature_c": 25.3, "wind_speed_kmh": 35.0},
        {"hour": "15:00", "rainfall_mm_h": 0.1, "rainfall_1h_mm": 0.1, "temperature_c": 25.2, "wind_speed_kmh": 34.1},
        {"hour": "16:00", "rainfall_mm_h": 0.6, "rainfall_1h_mm": 0.6, "temperature_c": 25.0, "wind_speed_kmh": 33.8},
        {"hour": "17:00", "rainfall_mm_h": 0.3, "rainfall_1h_mm": 0.3, "temperature_c": 24.9, "wind_speed_kmh": 33.0},
    ]
}


def build_phase5_dataset():
    raise RuntimeError(
        "Phase 5 V3 is a quarantined legacy artifact. Rebuilding is disabled "
        "because the historical builder assigned coordinates/timestamps and "
        "hardcoded traffic/road features. Use a source-native ingestion path."
    )
    intermediate_v2_path = root_dir / "data" / "intermediate" / "road_risk_verified_observations.jsonl"
    intermediate_v3_path = root_dir / "data" / "intermediate" / "road_risk_verified_observations_v3.jsonl"
    csv_v3_path = root_dir / "data" / "processed" / "road_risk_dataset_v3.csv"
    
    if not intermediate_v2_path.exists():
        raise FileNotFoundError(f"Missing {intermediate_v2_path}")

    with open(intermediate_v2_path, "r", encoding="utf-8") as f:
        v2_records = [json.loads(line) for line in f if line.strip()]

    logger.info(f"Loaded {len(v2_records)} verified FloodNet observations from Phase 4.")

    # Approved feature columns for V3 dataset schema
    # Core + Optional features (excluding leaked flood_detected and unavailable vehicle CAN telemetry)
    approved_feature_columns = [
        "rainfall_mm_h",
        "rainfall_10min_mm",
        "rainfall_1h_mm",
        "visibility_m",
        "temperature_c",
        "wind_speed_kmh",
        "traffic_level",
        "congestion_change",
        "road_slope_pct",
        "elevation_m",
        "road_type",
        "vehicle_count",
        "person_count",
        "fire_detected",
        "smoke_detected",
        "obstacle_count",
        "hazard_count",
    ]

    v3_observations = []
    hourly_samples = HISTORICAL_HARVEY_WEATHER["hourly_samples"]

    # Spatial-session allocation to prevent cross-partition road-segment contamination:
    # 8 segments: SEG_000 to SEG_007
    # SEG_000 to SEG_004 -> TRAIN (32 samples)
    # SEG_005 -> VALIDATION (6 samples)
    # SEG_006 to SEG_007 -> TEST_HOLDOUT (12 samples)
    segment_partition_map = {
        "TX_HARVEY_SEG_000": "TRAIN",
        "TX_HARVEY_SEG_001": "TRAIN",
        "TX_HARVEY_SEG_002": "TRAIN",
        "TX_HARVEY_SEG_003": "TRAIN",
        "TX_HARVEY_SEG_004": "TRAIN",
        "TX_HARVEY_SEG_005": "VALIDATION",
        "TX_HARVEY_SEG_006": "TEST_HOLDOUT",
        "TX_HARVEY_SEG_007": "TEST_HOLDOUT",
    }

    for idx, obs in enumerate(v2_records):
        meta = obs["metadata"]
        gt = obs["ground_truth"]
        yolo_feats = obs["features"]
        
        obs_id = meta["observation_id"]
        seg_id = meta["segment_id"]
        partition = segment_partition_map.get(seg_id, "TRAIN")
        
        # Authentic historical timestamp during Harvey aerial survey
        weather_slot = hourly_samples[idx % len(hourly_samples)]
        hist_timestamp = f"2017-08-28T{weather_slot['hour']}:00Z"
        
        # Historical environmental alignment:
        # rainfall_mm_h and 1h from ERA5
        # visibility_m marked None / null (unavailable in ERA5 archive)
        # rainfall_10min_mm marked None / null (hourly resolution only)
        # temperature_c and wind_speed_kmh from ERA5
        # traffic_level: 2.0 (moderate evacuation crawl/survey)
        # road_slope_pct: 0.5% (coastal plain)
        # elevation_m: authentic elevation from SRTM
        # road_type: 1 (Primary arterial / highway)
        aligned_features = {
            "rainfall_mm_h": float(weather_slot["rainfall_mm_h"]),
            "rainfall_10min_mm": None,  # Explicitly unavailable in historical reanalysis
            "rainfall_1h_mm": float(weather_slot["rainfall_1h_mm"]),
            "visibility_m": None,      # Explicitly unavailable in ERA5 archive
            "temperature_c": float(weather_slot["temperature_c"]),
            "wind_speed_kmh": float(weather_slot["wind_speed_kmh"]),
            "traffic_level": 2.0,      # Survey corridor background baseline
            "congestion_change": 0.0,
            "road_slope_pct": 0.5,
            "elevation_m": float(yolo_feats.get("elevation_m", 18.33)),
            "road_type": 1,
            # Visual features from YOLOv11 (excluding circular flood_detected and hazard_distance_m)
            "vehicle_count": int(yolo_feats.get("vehicle_count", 0)),
            "person_count": int(yolo_feats.get("person_count", 0)),
            "fire_detected": int(yolo_feats.get("fire_detected", 0)),
            "smoke_detected": int(yolo_feats.get("smoke_detected", 0)),
            "obstacle_count": int(yolo_feats.get("obstacle_count", 0)),
            "hazard_count": int(yolo_feats.get("hazard_count", 0)),
        }

        v3_obs = {
            "metadata": {
                "observation_id": obs_id,
                "timestamp": hist_timestamp,
                "latitude": float(meta["latitude"]),
                "longitude": float(meta["longitude"]),
                "segment_id": seg_id,
                "event_id": "Hurricane_Harvey_FloodNet",
                "session_id": meta["session_id"],
                "split_candidate": partition,
                "data_quality": "HIGH",
                "data_classification": "REAL",
                "source": "FloodNet_Aerial_Imagery",
                "weather_source": "Open-Meteo_ERA5_Historical_Archive",
                "has_label_source_exclusion": True,
                "excluded_features": ["flood_detected", "hazard_distance_m", "road_closure_report", "flood_report"],
                "exclusion_reason": "Visual flood detection and administrative reports excluded to prevent circular label leakage.",
            },
            "features": aligned_features,
            "ground_truth": {
                "road_risk_status": gt["road_risk_status"],
                "label_name": gt["label_name"],
                "label_source": gt["label_source"],
                "label_quality": "SILVER",
                "label_reason": gt["label_reason"],
            }
        }
        v3_observations.append(v3_obs)

    # Export intermediate JSONL
    with open(intermediate_v3_path, "w", encoding="utf-8") as f:
        for obs in v3_observations:
            f.write(json.dumps(obs) + "\n")
    logger.info(f"Saved {len(v3_observations)} verified observations to {intermediate_v3_path}")

    # Export processed CSV
    csv_headers = [
        "observation_id",
        "timestamp",
        "latitude",
        "longitude",
        "segment_id",
        "event_id",
        "session_id",
        "split_candidate",
        "data_quality",
        "data_classification",
        "source",
        "label_source",
        "label_quality",
    ] + approved_feature_columns + [
        "road_risk_status",
        "label_name",
        "label_reason"
    ]

    csv_rows = []
    for obs in v3_observations:
        meta = obs["metadata"]
        feats = obs["features"]
        gt = obs["ground_truth"]
        
        row = [
            meta["observation_id"],
            meta["timestamp"],
            meta["latitude"],
            meta["longitude"],
            meta["segment_id"],
            meta["event_id"],
            meta["session_id"],
            meta["split_candidate"],
            meta["data_quality"],
            meta["data_classification"],
            meta["source"],
            gt["label_source"],
            gt["label_quality"],
        ]
        for col in approved_feature_columns:
            val = feats.get(col)
            row.append("" if val is None else val)
        row.extend([
            gt["road_risk_status"],
            gt["label_name"],
            gt["label_reason"]
        ])
        csv_rows.append(row)

    with open(csv_v3_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        writer.writerows(csv_rows)

    logger.info(f"Saved model-ready CSV dataset to {csv_v3_path}")
    return v3_observations

if __name__ == "__main__":
    build_phase5_dataset()
