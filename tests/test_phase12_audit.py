import unittest
import os
import json
import hashlib
import pandas as pd

class TestPhase12Audit(unittest.TestCase):
    def setUp(self):
        self.dataset_path = os.path.join("data", "processed", "road_risk_dataset_v7.csv")
        self.audit_json = os.path.join("models", "road_risk_v2", "phase12_audit_results.json")
        self.target_audit_md = os.path.join("docs", "phase12_target_generation_audit.md")
        self.gen_audit_md = os.path.join("docs", "phase12_generalization_audit.md")
        self.expected_checksum = "066d1e44445eb6b2eeecdd4cef7d611c2fcfe2eb573e8ffc0c9ecab1e1b74658"

    def test_01_dataset_unmodified(self):
        self.assertTrue(os.path.exists(self.dataset_path))
        with open(self.dataset_path, "rb") as f:
            actual_checksum = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(actual_checksum, self.expected_checksum, "Dataset must remain frozen")
        df = pd.read_csv(self.dataset_path)
        self.assertEqual(len(df), 68)

    def test_02_documentation_artifacts_exist(self):
        self.assertTrue(os.path.exists(self.target_audit_md))
        self.assertTrue(os.path.exists(self.gen_audit_md))
        self.assertTrue(os.path.exists(self.audit_json))

        with open(self.gen_audit_md, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ROAD_PROXY_DOMINATED", content)
        self.assertIn("Unseen-Road Evaluation Strategy", content)
        self.assertIn("Comprehensive Feature Ablation", content)

    def test_03_audit_metrics_verify_memorization(self):
        with open(self.audit_json, "r") as f:
            res = json.load(f)
        
        self.assertIn("unseen_road_metrics", res)
        self.assertIn("ablation_results", res)
        
        # On unseen roads, road only ROC-AUC should be significantly lower than in Phase 11
        road_only_auc = res["ablation_results"]["B. Road only"]["roc_auc"]
        weather_only_auc = res["ablation_results"]["A. Weather only"]["roc_auc"]
        self.assertLess(road_only_auc, 0.70)
        self.assertGreater(weather_only_auc, road_only_auc)

    def test_04_baselines_preserved(self):
        self.assertTrue(os.path.exists(os.path.join("models", "road_model.pkl")))
        self.assertTrue(os.path.exists(os.path.join("models", "baselines", "xgboost_synthetic")))
        self.assertTrue(os.path.exists(os.path.join("models", "road_risk_v2", "model.json")))

if __name__ == "__main__":
    unittest.main()
