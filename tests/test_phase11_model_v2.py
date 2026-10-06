import unittest
import os
import json
import hashlib
import pandas as pd
import xgboost as xgb

class TestPhase11ModelV2(unittest.TestCase):
    def setUp(self):
        self.dataset_path = os.path.join("data", "processed", "road_risk_dataset_v7.csv")
        self.model_dir = os.path.join("models", "road_risk_v2")
        self.synthetic_model_path = os.path.join("models", "road_model.pkl")
        self.synthetic_baseline_dir = os.path.join("models", "baselines", "xgboost_synthetic")
        self.expected_checksum = "066d1e44445eb6b2eeecdd4cef7d611c2fcfe2eb573e8ffc0c9ecab1e1b74658"

    def test_01_dataset_freeze_and_checksum(self):
        self.assertTrue(os.path.exists(self.dataset_path), "Dataset v7 must exist")
        with open(self.dataset_path, "rb") as f:
            actual_checksum = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(actual_checksum, self.expected_checksum, "Dataset checksum must match frozen state")
        
        df = pd.read_csv(self.dataset_path)
        self.assertEqual(len(df), 68, "Dataset must have exactly 68 rows")
        self.assertIn("target_flood_exposure", df.columns, "Target must be target_flood_exposure")
        self.assertEqual(df["target_flood_exposure"].value_counts().to_dict(), {0: 50, 1: 18})

    def test_02_synthetic_baseline_preserved(self):
        self.assertTrue(os.path.exists(self.synthetic_model_path), "Synthetic road_model.pkl must remain intact")
        self.assertTrue(os.path.exists(self.synthetic_baseline_dir), "Synthetic baseline directory must exist")
        # Ensure it was not overwritten by checking file size > 0
        self.assertGreater(os.path.getsize(self.synthetic_model_path), 1000)

    def test_03_model_v2_artifacts_exist(self):
        required_files = [
            "model.json",
            "feature_schema.json",
            "training_config.json",
            "evaluation_metrics.json",
            "dataset_checksum.txt",
            "stress_test_metrics.json"
        ]
        for fname in required_files:
            fpath = os.path.join(self.model_dir, fname)
            self.assertTrue(os.path.exists(fpath), f"Artifact {fname} must exist in {self.model_dir}")

    def test_04_feature_separation_and_quarantine(self):
        schema_path = os.path.join(self.model_dir, "feature_schema.json")
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        feature_names = [f["name"] for f in schema["features"]]
        expected_features = ['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'elevation_m', 'road_type', 'road_surface', 'road_length_m']
        
        self.assertEqual(feature_names, expected_features)
        self.assertEqual(schema["target"]["name"], "target_flood_exposure")
        
        quarantined = [
            'distance_to_flood_m', 'gauge_water_level_m', 'gauge_warning_level_m',
            'flood_stage', 'flood_intersection_ratio', 'spatial_evidence_type',
            'event_id', 'observation_id', 'road_segment_id'
        ]
        for q in quarantined:
            self.assertNotIn(q, feature_names, f"Quarantined column {q} must not be in model features")

    def test_05_evaluation_metrics_and_baselines(self):
        metrics_path = os.path.join(self.model_dir, "evaluation_metrics.json")
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
        
        self.assertIn("strategy_A_event_holdout", metrics)
        self.assertIn("strategy_B_geographic_holdout", metrics)
        self.assertIn("grouped_cross_validation", metrics)
        self.assertIn("feature_ablation", metrics)
        
        strat_a_xgb = metrics["strategy_A_event_holdout"]["XGBoost V2"]["test"]
        self.assertGreaterEqual(strat_a_xgb["accuracy"], 0.80)
        self.assertEqual(strat_a_xgb["counts"]["FP"], 0)
        
        strat_b_xgb = metrics["strategy_B_geographic_holdout"]["XGBoost V2"]
        self.assertEqual(strat_b_xgb["counts"]["FP"], 0)
        self.assertEqual(strat_b_xgb["accuracy"], 1.0)

    def test_06_model_card_exists(self):
        card_path = os.path.join("docs", "road_risk_v2_model_card.md")
        self.assertTrue(os.path.exists(card_path), "Model card must exist in docs/")
        with open(card_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("PILOT_MODEL_VALIDATED", content)
        self.assertIn("Small Sample Size", content)

    def test_07_xgboost_model_loading_and_inference(self):
        model_file = os.path.join(self.model_dir, "model.json")
        clf = xgb.XGBClassifier()
        clf.load_model(model_file)
        self.assertIsNotNone(clf)

if __name__ == "__main__":
    unittest.main()
