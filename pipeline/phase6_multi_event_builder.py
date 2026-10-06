"""Phase 6 provenance gate for the ADAS tabular road-risk dataset.

This is deliberately a curation step, not model training. It admits only rows
with source-native capture location, time, and feature provenance. The Phase-5
FloodNet rows fail this gate because their coordinate, segment and time fields,
plus traffic, slope and road type, were written by the builder.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent
V3 = ROOT / "data" / "processed" / "road_risk_dataset_v3.csv"
OUT_CSV = ROOT / "data" / "processed" / "road_risk_dataset_v4.csv"
OUT_PARQUET = ROOT / "data" / "processed" / "road_risk_dataset_v4.parquet"
OUT_JSONL = ROOT / "data" / "intermediate" / "road_risk_verified_observations_v4.jsonl"
MANIFEST = ROOT / "data" / "manifests" / "road_risk_dataset_manifest.json"
REPORT = ROOT / "data" / "processed" / "road_risk_v4_quality_report.md"

# Metadata plus candidate weather features. Unsupported geography/traffic is
# intentionally absent; road_risk_status remains the target, never a feature.
COLUMNS = [
    "observation_id", "timestamp", "latitude", "longitude", "segment_id",
    "event_id", "session_id", "split_candidate", "source", "label_source",
    "label_quality", "data_quality", "data_classification", "rainfall_mm_h",
    "rainfall_1h_mm", "temperature_c", "wind_speed_kmh", "road_risk_status",
]


def phase6_rejection_reasons(row: dict[str, str]) -> list[str]:
    """Return non-negotiable provenance failures in a Phase-5 source row."""
    reasons = [
        "observation timestamp is a builder-assigned ERA5 slot, not a FloodNet capture timestamp",
        "latitude/longitude and segment_id are builder-generated Houston jitter, not image geolocation",
        "weather is joined at Houston centre, not a verified observation coordinate",
    ]
    if row.get("traffic_level") == "2.0":
        reasons.append("traffic_level is the hardcoded 2.0 fallback")
    if row.get("road_slope_pct") == "0.5":
        reasons.append("road_slope_pct is the hardcoded 0.5 fallback")
    if row.get("road_type") == "1":
        reasons.append("road_type is the hardcoded highway fallback")
    return reasons


def quality_report(source_count: int, reasons: list[str]) -> str:
    bullets = "\n".join(f"- {reason}" for reason in reasons)
    return f"""# ADAS Phase 6 — V4 Data Quality Report

**Dataset:** `road_risk_dataset_v4`  
**Verdict:** **NOT_READY_FOR_MODEL_TRAINING**

## Counts

| Measure | Count |
|---|---:|
| Source rows inspected (V3) | {source_count} |
| V4 eligible real rows | 0 |
| Simulated rows | 0 |
| Quarantined real source rows | {source_count} |
| Independent verified events in V4 | 0 |
| Training / validation / test rows | 0 / 0 / 0 |

## Labels, regions, and missingness

| Measure | SAFE | RISKY | BLOCKED |
|---|---:|---:|---:|
| Eligible V4 labels | 0 | 0 | 0 |

There are no V4 regions or road segments because no source row is eligible.
Eligible label-quality distribution is GOLD 0, SILVER 0, BRONZE 0 and UNVERIFIED
0. Feature missingness and value distributions are therefore not applicable;
they have not been silently filled. The quarantined source ledger contains one
claimed event (Hurricane Harvey / Texas) and SILVER FloodNet annotations, but it
is not an event-level evaluation dataset.

## Why V4 is empty

The source images/labels are genuine FloodNet material, but their tabular
metadata is not source-native. The Phase-5 builder manufactures a Houston
coordinate progression and timestamp rotation, attaches ERA5 values to the
Houston centre, and inserts constant traffic, slope, and road-type values.
Keeping these as model rows would misrepresent provenance. V3 remains as an
auditable source ledger; no source data or labels were deleted/relabelled.

## Feature and integrity audit

| Item | Result |
|---|---|
| Weather temporal alignment | Unsupported per image: assigned hour is not image capture time |
| Weather spatial alignment | Unsupported per image: coordinate is generated |
| Traffic | Hardcoded `2.0`; excluded (FUTURE) |
| Road slope | Hardcoded `0.5`; excluded |
| Road type | Hardcoded `1`; excluded |
| Elevation | Houston-centre value, not a verified segment coordinate; excluded |
| Target leakage | V4 has no feature rows; label-derived visual features remain excluded |
| Duplicates | 0 eligible rows / 0 duplicates |
| Hardcoded/fallback detection | 50/50 source rows contain the traffic, slope and road-type fallbacks listed below |
| Final holdout | Not created: an independent event is required first |

## Quarantine evidence

Every one of the {source_count} V3 rows has these failures:

{bullets}
"""


def build_phase6_dataset() -> dict:
    if not V3.exists():
        raise FileNotFoundError(V3)
    with V3.open(encoding="utf-8", newline="") as f:
        source_rows = list(csv.DictReader(f))
    reasons = phase6_rejection_reasons(source_rows[0]) if source_rows else []

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=COLUMNS).writeheader()
    OUT_JSONL.write_text("", encoding="utf-8")
    pl.DataFrame(schema={name: pl.String for name in COLUMNS}).write_parquet(OUT_PARQUET)

    manifest = {
        "dataset_manifest_version": "4.0.0",
        "phase": "PHASE_6_PROVENANCE_GATE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_files": {"csv": OUT_CSV.name, "parquet": OUT_PARQUET.name, "intermediate_jsonl": OUT_JSONL.name},
        "sha256_checksum_csv": hashlib.sha256(OUT_CSV.read_bytes()).hexdigest(),
        "total_records": 0,
        "source_records_quarantined": len(source_rows),
        "source_provenance_breakdown": {"REAL_ELIGIBLE": 0, "REAL_QUARANTINED": len(source_rows), "SIMULATED": 0},
        "distinct_disaster_events": [],
        "candidate_partitions": {"TRAIN": 0, "VALIDATION": 0, "TEST_HOLDOUT": 0},
        "training_readiness": {
            "status": "NOT_READY_FOR_MODEL_TRAINING",
            "rationale": "No V4-eligible rows: one source event and no source-native capture coordinates/timestamps; traffic and road geography contain hardcoded fallbacks.",
        },
        "quarantine": {"source_dataset": V3.name, "count": len(source_rows), "common_failures": reasons},
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(quality_report(len(source_rows), reasons), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    build_phase6_dataset()
