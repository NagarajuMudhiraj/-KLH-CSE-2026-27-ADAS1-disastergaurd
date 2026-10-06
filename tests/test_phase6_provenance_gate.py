"""Regression tests for the Phase 6 no-fabrication provenance gate."""
import csv
import json
import unittest
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent


class TestPhase6ProvenanceGate(unittest.TestCase):
    def test_v4_has_no_unsupported_training_rows_or_traffic(self):
        with (ROOT / "data/processed/road_risk_dataset_v4.csv").open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.assertNotIn("traffic_level", reader.fieldnames)
            self.assertEqual(list(reader), [])

    def test_v4_parquet_matches_zero_row_csv(self):
        frame = pl.read_parquet(ROOT / "data/processed/road_risk_dataset_v4.parquet")
        self.assertEqual(frame.height, 0)
        self.assertNotIn("road_risk_status", frame.columns[:-1])

    def test_manifest_blocks_training_and_records_quarantine(self):
        manifest = json.loads((ROOT / "data/manifests/road_risk_dataset_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["training_readiness"]["status"], "NOT_READY_FOR_MODEL_TRAINING")
        self.assertEqual(manifest["total_records"], 0)
        self.assertGreater(manifest["source_records_quarantined"], 0)


if __name__ == "__main__":
    unittest.main()
