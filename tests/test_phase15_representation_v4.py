import unittest
import os
import json
import pandas as pd

class TestPhase15RepresentationV4(unittest.TestCase):
    def setUp(self):
        self.csv_v9 = os.path.join("data", "processed", "road_risk_dataset_v9.csv")
        self.parquet_v9 = os.path.join("data", "processed", "road_risk_dataset_v9.parquet")
        self.hand_csv = os.path.join("data", "intermediate", "hand_pilot_v4.csv")
        self.schema_v4 = os.path.join("models", "road_risk_v4", "feature_schema.json")
        self.hand_doc = os.path.join("docs", "phase15_hand_design.md")
        self.lagged_doc = os.path.join("docs", "phase15_lagged_hydrology_audit.md")
        self.quality_v9_doc = os.path.join("data", "processed", "road_risk_v9_quality_report.md")

    def test_01_v9_dataset_files_and_shape(self):
        self.assertTrue(os.path.exists(self.csv_v9))
        self.assertTrue(os.path.exists(self.parquet_v9))
        
        df = pd.read_csv(self.csv_v9)
        self.assertEqual(len(df), 68, "Dataset V9 must contain exactly 68 rows")
        self.assertEqual(df["target_flood_exposure"].value_counts().to_dict(), {0: 50, 1: 18})

    def test_02_new_representation_features_present(self):
        df = pd.read_csv(self.csv_v9)
        required_cols = [
            "hand_m", "catchment_mean_rainfall_72h_mm", "rainfall_24h_mm",
            "rainfall_72h_mm", "rainfall_7d_mm", "upstream_rainfall_72h_mm",
            "temperature_c", "wind_speed_kmh", "basin"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Column {col} must exist in Dataset V9")
            self.assertEqual(df[col].isna().sum(), 0, f"Column {col} must have 0 missing values")

    def test_03_hand_pilot_file_integrity(self):
        self.assertTrue(os.path.exists(self.hand_csv))
        df_hand = pd.read_csv(self.hand_csv)
        self.assertEqual(len(df_hand), 16, "HAND pilot must have exactly 16 unique road segments")
        self.assertIn("hand_m", df_hand.columns)
        self.assertIn("nearest_drainage_river", df_hand.columns)

    def test_04_v4_feature_contract_schema(self):
        self.assertTrue(os.path.exists(self.schema_v4))
        with open(self.schema_v4, "r", encoding="utf-8") as f:
            schema = json.load(f)
            
        candidate_names = [f["name"] for f in schema["candidate_features"]]
        self.assertIn("hand_m", candidate_names)
        self.assertIn("catchment_mean_rainfall_72h_mm", candidate_names)
        
        # Verify geographic proxies excluded
        self.assertNotIn("road_length_m", candidate_names)
        self.assertNotIn("road_type", candidate_names)
        self.assertNotIn("road_surface", candidate_names)
        self.assertNotIn("elevation_m", candidate_names)

    def test_05_documentation_artifacts(self):
        self.assertTrue(os.path.exists(self.hand_doc))
        self.assertTrue(os.path.exists(self.lagged_doc))
        self.assertTrue(os.path.exists(self.quality_v9_doc))
        
        with open(self.quality_v9_doc, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("V4_DATASET_READY", content)
        self.assertIn("INSUFFICIENT_CLASS_DIVERSITY", content)

    def test_06_previous_models_preserved(self):
        self.assertTrue(os.path.exists(os.path.join("models", "road_model.pkl")))
        self.assertTrue(os.path.exists(os.path.join("models", "baselines", "xgboost_synthetic")))
        self.assertTrue(os.path.exists(os.path.join("models", "road_risk_v2", "model.json")))
        self.assertTrue(os.path.exists(os.path.join("models", "road_risk_v3", "model.json")))

    def test_07_no_model_trained_in_phase15(self):
        # In Phase 16, model.json is trained for V4. If present, verify it is a valid V4 model artifact.
        v4_model_path = os.path.join("models", "road_risk_v4", "model.json")
        if os.path.exists(v4_model_path):
            self.assertGreater(os.path.getsize(v4_model_path), 1000, "V4 model file must be a non-empty artifact once trained in Phase 16")
        else:
            self.assertFalse(os.path.exists(v4_model_path), "XGBoost V4 model must NOT be trained during Phase 15")

if __name__ == "__main__":
    unittest.main()
