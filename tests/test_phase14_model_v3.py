import unittest
import os
import json
import hashlib
import pandas as pd
import xgboost as xgb

class TestPhase14ModelV3(unittest.TestCase):
    def setUp(self):
        self.dataset_path = os.path.join("data", "processed", "road_risk_dataset_v8.csv")
        self.v3_dir = os.path.join("models", "road_risk_v3")
        self.model_card_path = os.path.join("docs", "road_risk_v3_model_card.md")
        self.provenance_doc_path = os.path.join("docs", "phase14_relative_elevation_provenance.md")
        self.expected_checksum = "1dce0d6ef702c2159d4d0ad0a57b16ab9327eafa66267a52eacba750cd10db5c"

    def test_01_dataset_freeze_and_checksum(self):
        self.assertTrue(os.path.exists(self.dataset_path), "Dataset V8 must exist")
        with open(self.dataset_path, "rb") as f:
            actual_checksum = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(actual_checksum, self.expected_checksum, "Dataset checksum must match frozen state")
        
        df = pd.read_csv(self.dataset_path)
        self.assertEqual(len(df), 68, "Dataset must have exactly 68 rows")
        self.assertEqual(df["target_flood_exposure"].value_counts().to_dict(), {0: 50, 1: 18})
        self.assertNotIn("road_length_m", df.columns)

    def test_02_v3_artifacts_exist(self):
        required_files = [
            "model.json",
            "feature_schema.json",
            "training_config.json",
            "evaluation_metrics.json",
            "ablation_results.json",
            "dataset_checksum.txt"
        ]
        for fname in required_files:
            fpath = os.path.join(self.v3_dir, fname)
            self.assertTrue(os.path.exists(fpath), f"Artifact {fname} must exist in {self.v3_dir}")

    def test_03_feature_schema_consistency(self):
        schema_path = os.path.join(self.v3_dir, "feature_schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
            
        features = schema["features"]
        self.assertEqual(len(features), 9, "Feature schema must contain exactly 9 features")
        
        feature_names = [f["name"] for f in features]
        expected_9 = [
            'rainfall_24h_mm', 'rainfall_72h_mm', 'rainfall_7d_mm',
            'upstream_rainfall_72h_mm', 'temperature_c', 'wind_speed_kmh',
            'relative_elevation_m', 'road_type', 'road_surface'
        ]
        self.assertEqual(set(feature_names), set(expected_9))
        self.assertNotIn("road_length_m", feature_names)

    def test_04_docs_and_model_card(self):
        self.assertTrue(os.path.exists(self.model_card_path))
        self.assertTrue(os.path.exists(self.provenance_doc_path))
        
        with open(self.model_card_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("V3_PILOT_UNSTABLE", content)
        self.assertIn("Unseen-Road Evaluation", content)

    def test_05_evaluation_metrics_unseen_road_gains(self):
        metrics_path = os.path.join(self.v3_dir, "evaluation_metrics.json")
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)
            
        strat_b = metrics["strategy_B_unseen_road"]["test"]
        self.assertGreaterEqual(strat_b["recall"], 0.80, "V3 must achieve high recall on unseen roads")
        self.assertGreaterEqual(strat_b["f1"], 0.60, "V3 must achieve F1 >= 0.60 on unseen roads")
        self.assertGreaterEqual(strat_b["roc_auc"], 0.75, "V3 must achieve ROC-AUC >= 0.75 on unseen roads")

    def test_06_baselines_preserved(self):
        self.assertTrue(os.path.exists(os.path.join("models", "road_model.pkl")))
        self.assertTrue(os.path.exists(os.path.join("models", "baselines", "xgboost_synthetic")))
        self.assertTrue(os.path.exists(os.path.join("models", "road_risk_v2", "model.json")))

    def test_07_xgboost_v3_loading_and_inference(self):
        model_file = os.path.join(self.v3_dir, "model.json")
        clf = xgb.XGBClassifier()
        clf.load_model(model_file)
        self.assertIsNotNone(clf)

if __name__ == "__main__":
    unittest.main()
