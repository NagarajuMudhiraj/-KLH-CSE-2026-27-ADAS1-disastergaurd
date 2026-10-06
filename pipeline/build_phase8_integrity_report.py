"""Generate the Phase 8 audit report without mutating legacy datasets."""
from __future__ import annotations

import csv
from pathlib import Path

from pipeline.data_integrity_auditor import DataIntegrityAuditor

ROOT = Path(__file__).resolve().parent.parent
V3 = ROOT / "data" / "processed" / "road_risk_dataset_v3.csv"
OUT = ROOT / "data" / "processed" / "phase8_data_integrity_report.md"


def build_report() -> None:
    with V3.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    observations = []
    for row in rows:
        meta = {key: row.get(key) for key in ("observation_id", "timestamp", "latitude", "longitude")}
        meta["data_classification"] = row.get("data_classification")
        features = {key: row.get(key) for key in ("traffic_level", "road_slope_pct", "road_type", "elevation_m", "rainfall_mm_h")}
        observations.append({"metadata": meta, "features": features, "provenance": {}})
    audit = DataIntegrityAuditor().audit(observations)
    codes = sorted({finding.code for finding in audit.findings})
    OUT.write_text(
        "# ADAS Phase 8 — Data Integrity Report\n\n"
        "**Training readiness:** **NOT_READY_FOR_MODEL_TRAINING**\n\n"
        "| Measure | Result |\n|---|---:|\n"
        f"| Legacy V3 rows quarantined | {len(rows)} |\n"
        "| Genuine real training rows | 0 |\n"
        f"| Integrity findings on inspected legacy rows | {len(audit.findings)} |\n"
        f"| Critical findings | {audit.critical_count} |\n\n"
        "## Quarantine reasons\n\n"
        "- Generated Houston coordinate progression and assigned timestamp slots.\n"
        "- Hardcoded traffic (`2.0`), road slope (`0.5`) and road type (`1`).\n"
        "- Reused Houston-centre elevation and weather joins without source-native observation location/time.\n"
        "- Feature-level provenance is absent from the legacy CSV.\n\n"
        "## Provider status after cleanup\n\n"
        "| Provider | Status | Training treatment |\n|---|---|---|\n"
        "| WeatherProvider | LIVE only when Open-Meteo/OWM responds; otherwise UNAVAILABLE | no fallback constants |\n"
        "| TrafficProvider | UNAVAILABLE in LIVE mode | FUTURE/excluded |\n"
        "| RoadProvider | UNAVAILABLE in LIVE mode | FUTURE/excluded |\n"
        "| TelemetryProvider | UNAVAILABLE without CAN/OBD | FUTURE_SENSOR/excluded |\n"
        "| DisasterReportProvider | UNAVAILABLE when MongoDB is offline | no default-zero report |\n"
        "| YOLOFeatureProvider | LIVE only for successful inference; simulated otherwise | visual branch, not tabular V2 training |\n\n"
        "## Auditor detections observed\n\n"
        + "\n".join(f"- `{code}`" for code in codes)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build_report()
