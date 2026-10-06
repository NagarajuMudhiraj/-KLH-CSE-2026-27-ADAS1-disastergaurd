import csv
import json
import unittest
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent


class TestPhase7DatasetDiscovery(unittest.TestCase):
    def test_v5_has_no_unverified_rows(self):
        with (ROOT / "data/processed/road_risk_dataset_v5.csv").open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.assertIn("original_label", reader.fieldnames)
            self.assertIn("mapped_label", reader.fieldnames)
            self.assertEqual(list(reader), [])

    def test_v5_parquet_and_readiness_gate(self):
        self.assertEqual(pl.read_parquet(ROOT / "data/processed/road_risk_dataset_v5.parquet").height, 0)
        manifest = json.loads((ROOT / "data/manifests/road_risk_dataset_v5_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["training_readiness"]["status"], "NO_SUITABLE_REAL_TABULAR_DATASET_FOUND")
        self.assertEqual(manifest["training_readiness"]["model_training_status"], "NOT_READY_FOR_MODEL_TRAINING")


if __name__ == "__main__":
    unittest.main()
