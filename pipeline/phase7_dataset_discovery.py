"""Phase 7 dataset-discovery output gate.

No external rows are downloaded or invented here.  V5 is emitted only when a
candidate has been independently inspected at row/schema level and satisfies
the project provenance contract.  The current research produces no such rows.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "processed" / "road_risk_dataset_v5.csv"
PARQUET_PATH = ROOT / "data" / "processed" / "road_risk_dataset_v5.parquet"
REPORT_PATH = ROOT / "data" / "processed" / "road_risk_v5_quality_report.md"
MANIFEST_PATH = ROOT / "data" / "manifests" / "road_risk_dataset_v5_manifest.json"

COLUMNS = [
    "observation_id", "timestamp", "latitude", "longitude", "segment_id",
    "event_id", "source", "label_source", "label_quality", "data_quality",
    "data_classification", "original_label", "mapped_label", "rainfall_mm_h",
    "rainfall_1h_mm", "temperature_c", "wind_speed_kmh", "road_risk_status",
]


def quality_report() -> str:
    return """# ADAS Phase 7 — V5 Dataset Quality Report

**Status:** **NO_SUITABLE_REAL_TABULAR_DATASET_FOUND**  
**Training readiness:** **NOT_READY_FOR_MODEL_TRAINING**

## V5 profile

| Check | Result |
|---|---:|
| Rows | 0 |
| REAL / simulation / synthetic | 0 / 0 / 0 |
| Events / regions / road segments | 0 / 0 / 0 |
| Temporal coverage | None |
| SAFE / RISKY / BLOCKED | 0 / 0 / 0 |
| Original labels / mapped labels | 0 / 0 |
| Duplicate rows / duplicate observations | 0 / 0 |

## Integrity checks

No missing values, temporal leakage, spatial leakage, or target leakage can be
measured because no row was admitted.  This is intentional: current candidates
lack either an inspectable historical extract, compatible independent target
semantics, or a validated feature-at-time-of-label join.  V5 includes the
canonical metadata and original/mapped-label columns for a future source, but
contains no model features or target rows.

## Admission requirements

A future row must supply a source observation timestamp, WGS84 (or documented
transformable) location/geometry, independently recorded road-state label,
source identity, and a documented feature join where each value existed at or
before the label time.  Closure notices may map only `ROAD_CLOSED -> BLOCKED`;
they do not create SAFE or RISKY observations.
"""


def build_phase7_v5() -> dict:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=COLUMNS).writeheader()
    pl.DataFrame(schema={column: pl.String for column in COLUMNS}).write_parquet(PARQUET_PATH)
    REPORT_PATH.write_text(quality_report(), encoding="utf-8")
    manifest = {
        "dataset_manifest_version": "5.0.0",
        "phase": "PHASE_7_DATASET_DISCOVERY",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_files": {"csv": CSV_PATH.name, "parquet": PARQUET_PATH.name},
        "sha256_checksum_csv": hashlib.sha256(CSV_PATH.read_bytes()).hexdigest(),
        "total_records": 0,
        "real_records": 0,
        "candidate_datasets_selected": [],
        "training_readiness": {
            "status": "NO_SUITABLE_REAL_TABULAR_DATASET_FOUND",
            "model_training_status": "NOT_READY_FOR_MODEL_TRAINING",
            "rationale": "No public candidate was verified as an accessible historical tabular extract with compatible independent road-state labels, source-native times/locations, and valid inference-compatible feature joins.",
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    build_phase7_v5()
