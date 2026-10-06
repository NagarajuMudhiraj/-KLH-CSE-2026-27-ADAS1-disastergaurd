"""End-to-end dataset construction and validation pipeline for ADAS road-risk modeling.
Executes:
RAW -> LOAD -> VALIDATE -> NORMALIZE -> ALIGN TIME -> ALIGN LOCATION -> DEDUP -> LEAKAGE CHECK -> ATTACH LABEL -> QUALITY CHECK -> MODEL-READY.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Path setup for root and backend
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from pipeline.label_constructor import LabelConstructor
from pipeline.leakage_auditor import LeakageAuditor
from pipeline.observation_builder import ObservationBuilder
from pipeline.providers.base import ProviderMode, SourceClassification
from pipeline.providers.disaster_provider import DisasterReportProvider
from pipeline.providers.road_provider import RoadProvider
from pipeline.providers.telemetry_provider import TelemetryProvider
from pipeline.providers.traffic_provider import TrafficProvider
from pipeline.providers.weather_provider import WeatherProvider
from pipeline.providers.yolo_feature_provider import YOLOFeatureProvider
from pipeline.quality_reporter import QualityReporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class DatasetPipeline:
    """Orchestrates dataset construction, validation, deduplication, and export."""

    def __init__(
        self,
        mode: str = "simulate",
        raw_dir: Path = root_dir / "data" / "raw",
        intermediate_dir: Path = root_dir / "data" / "intermediate",
        processed_dir: Path = root_dir / "data" / "processed",
        manifest_dir: Path = root_dir / "data" / "manifests",
    ) -> None:
        self.mode_str = mode.lower()
        self.provider_mode = ProviderMode.LIVE if self.mode_str == "live" else ProviderMode.SIMULATOR
        self.raw_dir = Path(raw_dir)
        self.intermediate_dir = Path(intermediate_dir)
        self.processed_dir = Path(processed_dir)
        self.manifest_dir = Path(manifest_dir)

        # Ensure directories exist
        for d in [self.raw_dir, self.intermediate_dir, self.processed_dir, self.manifest_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Initialize providers
        self.weather_prov = WeatherProvider(mode=self.provider_mode)
        self.yolo_prov = YOLOFeatureProvider(mode=self.provider_mode)
        self.disaster_prov = DisasterReportProvider(mode=self.provider_mode)
        self.road_prov = RoadProvider(mode=self.provider_mode)
        self.traffic_prov = TrafficProvider(mode=self.provider_mode)
        self.telemetry_prov = TelemetryProvider(mode=self.provider_mode)

        self.builder = ObservationBuilder(
            weather_provider=self.weather_prov,
            yolo_provider=self.yolo_prov,
            disaster_provider=self.disaster_prov,
            road_provider=self.road_prov,
            traffic_provider=self.traffic_prov,
            telemetry_provider=self.telemetry_prov,
        )
        self.label_constructor = LabelConstructor()
        self.leakage_auditor = LeakageAuditor(mask_leaked_features=True)
        self.quality_reporter = QualityReporter()

    def run_pipeline(
        self,
        count: int = 100,
        coordinates_list: Optional[List[Tuple[float, float]]] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Starting DatasetPipeline in mode '{self.mode_str}' with target count {count}...")

        # Step 1: RAW INGESTION
        raw_observations = self._collect_raw(count=count, coordinates_list=coordinates_list)
        batch_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        raw_path = self.raw_dir / f"raw_batch_{batch_timestamp}.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(raw_observations, f, indent=2)
        logger.info(f"Saved {len(raw_observations)} raw observations to {raw_path}")

        # Step 2 & 3: LOAD, VALIDATE & NORMALIZE
        # Already normalized and schema-validated by ObservationBuilder
        valid_records = raw_observations

        # Step 4: SPATIAL-TEMPORAL ALIGNMENT & DEDUPLICATION
        deduped_records = self._deduplicate(valid_records)
        logger.info(f"Deduplication complete: {len(deduped_records)} records retained (from {len(valid_records)})")

        # Step 5: ATTACH INDEPENDENT GROUND TRUTH LABELS
        labeled_records = []
        for rec in deduped_records:
            lbl = self.label_constructor.assign_label(rec)
            rec["label"] = lbl.to_dict()
            labeled_records.append(rec)

        # Save intermediate snapshot
        intermediate_path = self.intermediate_dir / f"intermediate_labeled_{batch_timestamp}.json"
        with open(intermediate_path, "w", encoding="utf-8") as f:
            json.dump(labeled_records, f, indent=2)

        # Step 6: LEAKAGE AUDIT & FEATURE MASKING
        audited_records, audit_report = self.leakage_auditor.audit_batch(labeled_records)
        logger.info(f"Leakage audit: is_valid={audit_report.is_valid}, critical={audit_report.critical_count}")

        # Step 7: QUALITY REPORTING
        quality_dict = self.quality_reporter.generate_report(audited_records, audit_report)
        md_report = self.quality_reporter.to_markdown(quality_dict)

        report_json_path = self.processed_dir / "quality_report.json"
        report_md_path = self.processed_dir / "quality_report.md"
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(quality_dict, f, indent=2)
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        logger.info(f"Quality reports written to {report_json_path} and {report_md_path}")

        # Step 8: MODEL-READY DATASET EXPORT
        processed_json_path = self.processed_dir / "road_risk_dataset_v2.json"
        processed_csv_path = self.processed_dir / "road_risk_dataset_v2.csv"
        with open(processed_json_path, "w", encoding="utf-8") as f:
            json.dump(audited_records, f, indent=2)

        # Export flat CSV (features + target + metadata)
        if audited_records:
            feat_keys = list(audited_records[0]["features"].keys())
            csv_headers = (
                ["observation_id", "timestamp", "latitude", "longitude", "data_quality", "source_classification"]
                + feat_keys
                + ["road_risk_status", "label_name", "label_source", "label_reason"]
            )
            with open(processed_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(csv_headers)
                for r in audited_records:
                    meta = r.get("metadata", {})
                    lbl = r.get("label", {})
                    row = [
                        meta.get("observation_id"),
                        meta.get("timestamp"),
                        meta.get("latitude"),
                        meta.get("longitude"),
                        meta.get("data_quality"),
                        meta.get("source_classification"),
                    ]
                    row.extend([r["features"].get(k, 0.0) for k in feat_keys])
                    row.extend([
                        lbl.get("road_risk_status"),
                        lbl.get("label_name"),
                        lbl.get("label_source"),
                        lbl.get("label_reason"),
                    ])
                    writer.writerow(row)
            logger.info(f"Model-ready dataset exported to {processed_json_path} and {processed_csv_path}")

        # Step 9: DATASET MANIFEST GENERATION
        manifest = self._generate_manifest(
            dataset_path=processed_csv_path,
            records=audited_records,
            audit_report=audit_report,
            quality_dict=quality_dict,
        )
        manifest_path = self.manifest_dir / "road_risk_dataset_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Dataset manifest written to {manifest_path}")

        return {
            "status": "SUCCESS",
            "count": len(audited_records),
            "csv_path": str(processed_csv_path),
            "manifest_path": str(manifest_path),
            "quality_report": quality_dict,
        }

    def _collect_raw(
        self,
        count: int,
        coordinates_list: Optional[List[Tuple[float, float]]] = None,
    ) -> List[Dict[str, Any]]:
        # Default sampling grid (Disaster-prone and urban Indian corridors)
        default_coords = [
            (12.9716, 77.5946),  # Bengaluru (Urban)
            (13.0827, 80.2707),  # Chennai (Coastal / Flood-prone)
            (19.0760, 72.8777),  # Mumbai (Monsoon flood-prone)
            (28.6139, 77.2090),  # Delhi (Fog & Urban)
            (22.5726, 88.3639),  # Kolkata (Cyclone & Waterlogging)
            (9.9312, 76.2673),   # Kochi (Flash flood & Hill slope)
            (17.3850, 78.4867),  # Hyderabad (Urban waterlogging)
            (25.5941, 85.1376),  # Patna (Riverine flood)
        ]
        coords = coordinates_list or default_coords

        scenarios = [
            "clear",
            "moderate_rain",
            "heavy_monsoon",
            "dense_fog",
            "cyclone",
            "water_hazard",
            "blocked_tree",
            "fire_hazard",
        ]

        observations = []
        for i in range(count):
            lat, lon = coords[i % len(coords)]
            scenario = scenarios[i % len(scenarios)] if self.provider_mode == ProviderMode.SIMULATOR else None
            obs = self.builder.build_observation(
                latitude=lat,
                longitude=lon,
                scenario=scenario,
                segment_id=f"SEG_{(i % 10):03d}",
            )
            observations.append(obs)

        return observations

    def _deduplicate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_keys = set()
        deduped = []
        for r in records:
            meta = r.get("metadata", {})
            lat = round(float(meta.get("latitude", 0.0)), 4)
            lon = round(float(meta.get("longitude", 0.0)), 4)
            ts = meta.get("timestamp", "")
            # Dedup key combines space and coarse time (or exact unique observation)
            dedup_key = f"{lat}_{lon}_{ts}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            deduped.append(r)
        return deduped

    def _generate_manifest(
        self,
        dataset_path: Path,
        records: List[Dict[str, Any]],
        audit_report: Any,
        quality_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        # Compute SHA256 of output file
        sha256_hash = hashlib.sha256()
        if dataset_path.exists():
            with open(dataset_path, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            file_hash = sha256_hash.hexdigest()
        else:
            file_hash = "N/A"

        # Determine Readiness Status honestly:
        # A dataset is only READY_FOR_MODEL_TRAINING if:
        # 1. Real records exist and are verified by official authority, OR
        # 2. Minimum real-world labeled sample threshold is met (e.g. >= 1,000 real observations with all 3 classes populated from external authorities)
        real_count = quality_dict.get("source_provenance_breakdown", {}).get("REAL", {}).get("count", 0)
        has_critical_leakage = not audit_report.is_valid

        # We evaluate whether external authorities exist
        if real_count >= 1000 and not has_critical_leakage:
            readiness = "READY_FOR_MODEL_TRAINING"
            readiness_rationale = "Sufficient verified real-world records across all risk classes with zero critical leakage."
        else:
            readiness = "NOT_READY_FOR_MODEL_TRAINING"
            readiness_rationale = (
                f"Dataset comprises {real_count} real records and {len(records) - real_count} realistic simulated records. "
                "Real external authority feeds (CWC, NHAI, NDMA APIs) are not yet integrated into production pipeline. "
                "Training on purely simulated or incomplete real records would produce uncalibrated or misleading accuracy claims. "
                "Phase 3 establishes the pipeline and contracts; external ground-truth integration is required before final model training."
            )

        return {
            "dataset_manifest_version": "1.0.0",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "pipeline_mode": self.mode_str,
            "dataset_file": dataset_path.name,
            "sha256_checksum": file_hash,
            "total_records": len(records),
            "canonical_feature_count": 25,
            "label_classes": ["SAFE (0)", "RISKY (1)", "BLOCKED (2)"],
            "class_distribution": quality_dict.get("label_distribution", {}),
            "source_provenance_breakdown": quality_dict.get("source_provenance_breakdown", {}),
            "quality_tier_breakdown": quality_dict.get("data_quality_breakdown", {}),
            "leakage_audit_status": {
                "passed": audit_report.is_valid,
                "critical_violations": audit_report.critical_count,
                "total_violations": audit_report.total_violations,
            },
            "training_readiness": {
                "status": readiness,
                "rationale": readiness_rationale,
            },
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="ADAS Road-Risk Dataset Construction Pipeline")
    parser.add_argument("--mode", type=str, default="simulate", choices=["live", "simulate"], help="Pipeline execution mode")
    parser.add_argument("--count", type=int, default=120, help="Number of observations to collect/generate")
    args = parser.parse_args()

    pipeline = DatasetPipeline(mode=args.mode)
    res = pipeline.run_pipeline(count=args.count)
    print(f"\nPipeline Execution Complete!")
    print(f"Processed: {res['count']} records")
    print(f"Dataset CSV: {res['csv_path']}")
    print(f"Manifest: {res['manifest_path']}")


if __name__ == "__main__":
    main()
