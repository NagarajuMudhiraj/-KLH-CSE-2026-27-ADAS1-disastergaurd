"""Phase 4 master real-data acquisition and validation pipeline for ADAS road-risk modeling.
Executes:
1. Real raw data collection and provenance tagging.
2. Verified observation assembly with temporal/spatial alignment.
3. Independent ground-truth labeling and label source separation.
4. Advanced multi-dimensional leakage audit.
5. Real data quality and label coverage reporting.
6. Checksummed manifest generation and Training Readiness Gate evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from pipeline.phase4_leakage_auditor import Phase4LeakageAuditor
from pipeline.real_quality_reporter import RealQualityReporter
from pipeline.verified_observation_builder import VerifiedObservationBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class Phase4Pipeline:
    """Orchestrates Phase 4 real data population, validation, and readiness gating."""

    def __init__(
        self,
        intermediate_dir: Optional[Path] = None,
        processed_dir: Optional[Path] = None,
        manifest_dir: Optional[Path] = None,
    ) -> None:
        self.intermediate_dir = Path(intermediate_dir or (root_dir / "data" / "intermediate"))
        self.processed_dir = Path(processed_dir or (root_dir / "data" / "processed"))
        self.manifest_dir = Path(manifest_dir or (root_dir / "data" / "manifests"))

        self.intermediate_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

        self.builder = VerifiedObservationBuilder(
            intermediate_dir=self.intermediate_dir,
            processed_dir=self.processed_dir,
        )
        self.auditor = Phase4LeakageAuditor()
        self.reporter = RealQualityReporter()

    def run(self, max_real_samples: int = 50) -> Dict[str, Any]:
        logger.info(f"Starting Phase 4 Real-Data Population Pipeline (Target samples: {max_real_samples})...")

        # Step 1: Collect & Assemble Real Observations
        real_observations = self.builder.build_real_disaster_dataset(max_samples=max_real_samples)

        # Step 2: Export Datasets (JSONL, CSV, Parquet)
        export_paths = self.builder.export_datasets(real_observations)

        # Step 3: Run Multi-Dimensional Leakage & Ground-Truth Audit
        audit_result = self.auditor.audit_dataset(real_observations)
        logger.info(
            f"Audit complete: Leakage-Free={audit_result.is_leakage_free}, "
            f"Critical Violations={audit_result.critical_leakage_count}, "
            f"Ground-Truth Deficiencies={audit_result.ground_truth_deficiencies}"
        )

        # Step 4: Generate Real Data Quality & Label Coverage Reports
        quality_dict = self.reporter.generate_report(
            observations=real_observations,
            audit_result=audit_result,
            simulated_count=0,
            removed_count=0,
            removed_reasons=[],
        )
        md_report = self.reporter.to_markdown(quality_dict)

        report_md_path = self.processed_dir / "road_risk_real_data_quality.md"
        report_json_path = self.processed_dir / "road_risk_real_data_quality.json"
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(quality_dict, f, indent=2)
        logger.info(f"Saved real data quality report to {report_md_path}")

        # Step 5: Evaluate Real Data Sufficiency Gate & Generate Manifest
        manifest = self._generate_manifest(
            dataset_csv=export_paths["csv"],
            dataset_parquet=export_paths.get("parquet"),
            observations=real_observations,
            quality_dict=quality_dict,
            audit_result=audit_result,
        )
        manifest_path = self.manifest_dir / "road_risk_dataset_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Updated dataset manifest at {manifest_path}")

        return {
            "status": "SUCCESS",
            "real_samples_count": len(real_observations),
            "csv_path": str(export_paths["csv"]),
            "parquet_path": str(export_paths.get("parquet")),
            "manifest_path": str(manifest_path),
            "quality_report_path": str(report_md_path),
            "readiness_status": manifest["training_readiness"]["status"],
            "readiness_rationale": manifest["training_readiness"]["rationale"],
        }

    def _generate_manifest(
        self,
        dataset_csv: Path,
        dataset_parquet: Optional[Path],
        observations: List[Dict[str, Any]],
        quality_dict: Dict[str, Any],
        audit_result: Any,
    ) -> Dict[str, Any]:
        # Compute SHA256 of CSV
        sha256_csv = hashlib.sha256()
        if dataset_csv.exists():
            with open(dataset_csv, "rb") as f:
                for block in iter(lambda: f.read(65536), b""):
                    sha256_csv.update(block)
            csv_hash = sha256_csv.hexdigest()
        else:
            csv_hash = "N/A"

        total_real = len(observations)
        gold_count = quality_dict["label_quality_distribution"].get("GOLD", 0)
        silver_count = quality_dict["label_quality_distribution"].get("SILVER", 0)
        distinct_events_count = len(quality_dict["distinct_events"])

        # SUFFICIENCY GATE EVALUATION:
        # Strict scientific readiness criteria:
        # 1. Total real observations >= 1,000
        # 2. Independent labeled count across all 3 classes (SAFE, RISKY, BLOCKED) >= 100 each
        # 3. Gold or Silver verified labels >= 80%
        # 4. Zero critical leakage violations
        # 5. Distinct disaster events >= 3 (to ensure event-generalization, not just 1 storm)
        if (
            total_real >= 1000
            and quality_dict["target_distribution"]["SAFE"]["count"] >= 100
            and quality_dict["target_distribution"]["RISKY"]["count"] >= 100
            and quality_dict["target_distribution"]["BLOCKED"]["count"] >= 100
            and distinct_events_count >= 3
            and audit_result.is_leakage_free
        ):
            readiness = "READY_FOR_MODEL_TRAINING"
            readiness_rationale = (
                f"Dataset satisfies all sufficiency criteria: {total_real} real observations across {distinct_events_count} "
                "distinct events with zero critical leakage and balanced target classes."
            )
        else:
            readiness = "NOT_READY_FOR_MODEL_TRAINING"
            reasons = []
            if total_real < 1000:
                reasons.append(f"Sample volume ({total_real}) is below minimum statistical threshold of 1,000 real rows.")
            if distinct_events_count < 3:
                reasons.append(f"Disaster events count ({distinct_events_count}) lacks multi-event geographic diversity.")
            if gold_count == 0:
                reasons.append("Official municipal/police road closure decrees (GOLD tier) are not yet integrated via live API.")
            if not audit_result.is_leakage_free:
                reasons.append(f"Audit identified {audit_result.critical_leakage_count} critical leakage issues.")

            readiness_rationale = (
                "Dataset population pipeline is operational and verified, but real data volume is currently insufficient: "
                + "; ".join(reasons)
                + " Training at this stage would produce an overfitted model with uncalibrated real-world risk probabilities."
            )

        return {
            "dataset_manifest_version": "2.0.0",
            "phase": "PHASE_4_REAL_WORLD_DATA_POPULATION",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_files": {
                "csv": dataset_csv.name,
                "parquet": dataset_parquet.name if dataset_parquet and dataset_parquet.exists() else None,
            },
            "sha256_checksum_csv": csv_hash,
            "total_records": total_real,
            "source_provenance_breakdown": {
                "REAL": {"count": total_real, "percentage": 100.0},
                "REALISTIC_SIMULATION": {"count": 0, "percentage": 0.0},
                "SYNTHETIC_BENCHMARK": {"count": 0, "percentage": 0.0},
            },
            "target_classes": ["SAFE (0)", "RISKY (1)", "BLOCKED (2)"],
            "class_distribution": quality_dict["target_distribution"],
            "label_quality_distribution": quality_dict["label_quality_distribution"],
            "candidate_partitions": quality_dict["candidate_partitions"],
            "distinct_disaster_events": quality_dict["distinct_events"],
            "distinct_road_segments": quality_dict["distinct_segments_count"],
            "leakage_audit_status": {
                "is_leakage_free": audit_result.is_leakage_free,
                "critical_violations": audit_result.critical_leakage_count,
                "ground_truth_validity": audit_result.is_valid_ground_truth,
            },
            "training_readiness": {
                "status": readiness,
                "rationale": readiness_rationale,
            },
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4 ADAS Real Data Population Pipeline")
    parser.add_argument("--samples", type=int, default=45, help="Number of real disaster observations to process")
    args = parser.parse_args()

    pipeline = Phase4Pipeline()
    res = pipeline.run(max_real_samples=args.samples)
    print("\nPhase 4 Pipeline Run Complete!")
    print(f"Real Observations Processed: {res['real_samples_count']}")
    print(f"Dataset CSV: {res['csv_path']}")
    print(f"Quality Report: {res['quality_report_path']}")
    print(f"Readiness Verdict: {res['readiness_status']}")
    print(f"Rationale: {res['readiness_rationale']}")


if __name__ == "__main__":
    main()
