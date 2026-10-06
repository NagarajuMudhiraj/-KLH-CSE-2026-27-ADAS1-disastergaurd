import os
import json
import hashlib
import unittest
import numpy as np
import pandas as pd
import xgboost as xgb

class TestPhase16V4Evaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.v9_csv = os.path.join(cls.repo_root, "data", "processed", "road_risk_dataset_v9.csv")
        cls.v4_dir = os.path.join(cls.repo_root, "models", "road_risk_v4")
        cls.docs_dir = os.path.join(cls.repo_root, "docs")

    def test_01_dataset_checksum_and_frozen_integrity(self):
        """Verify Dataset V9 matches the frozen checksum."""
        chk_file = os.path.join(self.v4_dir, "dataset_checksum.txt")
        self.assertTrue(os.path.exists(chk_file), "Checksum file missing")
        with open(chk_file, "r") as f:
            expected_chk = f.read().strip()
            
        with open(self.v9_csv, "rb") as f:
            actual_chk = hashlib.sha256(f.read()).hexdigest()
            
        self.assertEqual(actual_chk, expected_chk)
        self.assertEqual(expected_chk, "6c9ade7817fefa95f0afd6f2170e5773ba40a2d18754e9327510683dd0652ce2")

    def test_02_v4_artifacts_exist(self):
        """Verify all 7 V4 model artifacts are generated."""
        expected_files = [
            "model.json",
            "feature_schema.json",
            "training_config.json",
            "evaluation_metrics.json",
            "ablation_results.json",
            "generalization_results.json",
            "dataset_checksum.txt"
        ]
        for fname in expected_files:
            p = os.path.join(self.v4_dir, fname)
            self.assertTrue(os.path.exists(p), f"Artifact missing: {fname}")

    def test_03_v4_feature_contract(self):
        """Verify exactly 8 features and zero forbidden proxies."""
        with open(os.path.join(self.v4_dir, "training_config.json"), "r") as f:
            cfg = json.load(f)
            
        features = cfg["features"]
        self.assertEqual(len(features), 8)
        expected_features = [
            "rainfall_24h_mm",
            "rainfall_72h_mm",
            "rainfall_7d_mm",
            "temperature_c",
            "wind_speed_kmh",
            "upstream_rainfall_72h_mm",
            "catchment_mean_rainfall_72h_mm",
            "hand_m"
        ]
        self.assertEqual(features, expected_features)
        
        forbidden = [
            "road_length_m", "road_type", "road_surface", "elevation_m",
            "relative_elevation_m", "distance_to_flood_m", "gauge_water_level_m"
        ]
        for feat in forbidden:
            self.assertNotIn(feat, features)

    def test_04_unseen_road_metrics(self):
        """Verify unseen road benchmark results meet Phase 16 standards."""
        with open(os.path.join(self.v4_dir, "generalization_results.json"), "r") as f:
            gen = json.load(f)
            
        unseen = gen["unseen_road"]
        self.assertGreaterEqual(unseen["test_accuracy"], 0.80)
        self.assertEqual(unseen["test_recall"], 1.0)
        self.assertEqual(unseen["counts"]["FN"], 0)
        self.assertEqual(unseen["counts"]["TP"], 7)
        self.assertEqual(unseen["counts"]["TN"], 8)
        self.assertEqual(unseen["counts"]["FP"], 3)

    def test_05_model_loading_and_inference(self):
        """Verify trained model.json loads and runs inference without errors."""
        model_path = os.path.join(self.v4_dir, "model.json")
        clf = xgb.XGBClassifier()
        clf.load_model(model_path)
        
        # Test input of 8 features
        sample = np.array([[10.0, 25.0, 50.0, 28.0, 15.0, 30.0, 25.0, 5.0]])
        prob = clf.predict_proba(sample)
        self.assertEqual(prob.shape, (1, 2))
        self.assertTrue(0.0 <= prob[0, 1] <= 1.0)

    def test_06_model_card_and_hand_doc(self):
        """Verify documentation files exist."""
        mc_path = os.path.join(self.docs_dir, "road_risk_v4_model_card.md")
        hand_path = os.path.join(self.docs_dir, "phase16_hand_validation.md")
        self.assertTrue(os.path.exists(mc_path))
        self.assertTrue(os.path.exists(hand_path))

if __name__ == "__main__":
    unittest.main()
