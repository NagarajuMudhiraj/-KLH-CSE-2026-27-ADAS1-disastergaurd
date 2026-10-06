"""Unit and regression test suite for Phase 5 Historical Alignment and Dataset V3.
Verifies:
1. No live 2026 weather attached to historical 2017 observations.
2. Verified observation count is exactly 50 (no simulated/fabricated rows).
3. Zero spatial corridor overlap between train and test holdout.
4. Excluded circular visual and report features are purged from V3 CSV.
5. Training readiness gate properly evaluates to NOT_READY_FOR_MODEL_TRAINING.
"""
import unittest
from pathlib import Path
import polars as pl
import json

root_dir = Path(__file__).resolve().parent.parent

class TestPhase5HistoricalAlignment(unittest.TestCase):
    def setUp(self):
        self.v3_csv_path = root_dir / "data" / "processed" / "road_risk_dataset_v3.csv"
        self.v3_jsonl_path = root_dir / "data" / "intermediate" / "road_risk_verified_observations_v3.jsonl"
        self.manifest_path = root_dir / "data" / "manifests" / "road_risk_dataset_manifest.json"
        self.assertTrue(self.v3_csv_path.exists(), "road_risk_dataset_v3.csv must exist")

    def test_v3_row_count_and_real_classification(self):
        df = pl.read_csv(self.v3_csv_path)
        self.assertEqual(len(df), 50, "Verified dataset must contain exactly 50 real observations")
        classifications = df["data_classification"].unique().to_list()
        self.assertEqual(classifications, ["REAL"], "All observations must be classified as REAL")

    def test_no_live_2026_timestamp_in_historical_observations(self):
        df = pl.read_csv(self.v3_csv_path)
        timestamps = df["timestamp"].to_list()
        for ts in timestamps:
            self.assertTrue(ts.startswith("2017-08-28"), f"Expected 2017 disaster timestamp, got {ts}")

    def test_historical_weather_variation_and_no_zero_constant(self):
        df = pl.read_csv(self.v3_csv_path)
        rain_vals = df["rainfall_mm_h"].unique().to_list()
        self.assertGreater(len(rain_vals), 1, "Historical rainfall must exhibit natural meteorological variation")
        # Ensure not all rain is 0.0
        self.assertTrue(any(r > 0 for r in rain_vals), "Historical rainfall during Hurricane Harvey must not be all 0.0")

    def test_missingness_in_unavailable_historical_features(self):
        df = pl.read_csv(self.v3_csv_path)
        self.assertEqual(df["visibility_m"].null_count(), 50, "Visibility must be null/unavailable for ERA5 historical reanalysis")
        self.assertEqual(df["rainfall_10min_mm"].null_count(), 50, "10-min rain must be null/unavailable for hourly ERA5")

    def test_zero_spatial_segment_overlap_between_train_and_test(self):
        df = pl.read_csv(self.v3_csv_path)
        train_segs = set(df.filter(pl.col("split_candidate") == "TRAIN")["segment_id"].to_list())
        test_segs = set(df.filter(pl.col("split_candidate") == "TEST_HOLDOUT")["segment_id"].to_list())
        overlap = train_segs.intersection(test_segs)
        self.assertEqual(len(overlap), 0, f"Cross-partition corridor contamination detected: {overlap}")

    def test_circular_and_report_features_excluded(self):
        df = pl.read_csv(self.v3_csv_path)
        prohibited = ["flood_detected", "hazard_distance_m", "flood_report", "road_closure_report"]
        for p in prohibited:
            self.assertNotIn(p, df.columns, f"Feature '{p}' must be excluded from V3 CSV")

    def test_manifest_training_readiness_blocked(self):
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(
            manifest["training_readiness"]["status"],
            "NOT_READY_FOR_MODEL_TRAINING",
            "Model training must remain BLOCKED in Phase 5"
        )

if __name__ == "__main__":
    unittest.main()
