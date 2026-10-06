import unittest
import os
import json
import pandas as pd

class TestPhase13DatasetV8(unittest.TestCase):
    def setUp(self):
        self.csv_v8 = os.path.join("data", "processed", "road_risk_dataset_v8.csv")
        self.parquet_v8 = os.path.join("data", "processed", "road_risk_dataset_v8.parquet")
        self.schema_v3 = os.path.join("models", "road_risk_v3", "feature_schema.json")
        self.rel_hydro_doc = os.path.join("docs", "phase13_relative_hydrology_design.md")
        self.quality_v8_doc = os.path.join("data", "processed", "road_risk_v8_quality_report.md")

    def test_01_v8_dataset_files_exist_and_row_count(self):
        self.assertTrue(os.path.exists(self.csv_v8), "V8 CSV must exist")
        self.assertTrue(os.path.exists(self.parquet_v8), "V8 Parquet must exist")
        
        df_csv = pd.read_csv(self.csv_v8)
        df_pq = pd.read_parquet(self.parquet_v8)
        
        self.assertEqual(len(df_csv), 68, "Dataset V8 must have exactly 68 rows")
        self.assertEqual(len(df_pq), 68, "Parquet V8 must have exactly 68 rows")

    def test_02_road_length_removed(self):
        df = pd.read_csv(self.csv_v8)
        self.assertNotIn("road_length_m", df.columns, "road_length_m must NOT be present in Dataset V8")

    def test_03_relative_elevation_and_antecedent_rainfall_present(self):
        df = pd.read_csv(self.csv_v8)
        required_cols = [
            "relative_elevation_m", "rainfall_24h_mm", "rainfall_72h_mm",
            "rainfall_7d_mm", "upstream_rainfall_72h_mm", "temperature_c", "wind_speed_kmh"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Column {col} must exist in V8")
            self.assertEqual(df[col].isna().sum(), 0, f"Column {col} must have no missing values")
            
        # Verify precipitation monotonicity (7d >= 72h >= 24h roughly)
        self.assertTrue((df['rainfall_7d_mm'] >= df['rainfall_72h_mm'] - 0.01).all(), "7-day rain must be >= 72h rain")
        self.assertTrue((df['rainfall_72h_mm'] >= df['rainfall_24h_mm'] - 0.01).all(), "72h rain must be >= 24h rain")

    def test_04_target_distribution_and_semantics(self):
        df = pd.read_csv(self.csv_v8)
        self.assertIn("target_flood_exposure", df.columns)
        counts = df["target_flood_exposure"].value_counts().to_dict()
        self.assertEqual(counts, {0: 50, 1: 18}, "Target distribution must match 50 unexposed, 18 exposed")

    def test_05_feature_schema_v3_contract(self):
        self.assertTrue(os.path.exists(self.schema_v3), "Feature schema v3 must exist")
        with open(self.schema_v3, "r", encoding="utf-8") as f:
            schema = json.load(f)
            
        feature_names = [f["name"] for f in schema["features"]]
        self.assertIn("relative_elevation_m", feature_names)
        self.assertIn("rainfall_72h_mm", feature_names)
        self.assertIn("rainfall_7d_mm", feature_names)
        self.assertIn("upstream_rainfall_72h_mm", feature_names)
        self.assertNotIn("road_length_m", feature_names)
        
        excluded_names = [e["name"] for e in schema["excluded_and_quarantined_variables"]]
        self.assertIn("road_length_m", excluded_names)
        self.assertIn("elevation_m", excluded_names)
        self.assertIn("distance_to_flood_m", excluded_names)

    def test_06_docs_and_quality_reports_exist(self):
        self.assertTrue(os.path.exists(self.rel_hydro_doc))
        self.assertTrue(os.path.exists(self.quality_v8_doc))
        
        with open(self.quality_v8_doc, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("READY_FOR_V3_MODEL_TRAINING", content)
        self.assertIn("Unseen-Road Evaluation", content)

    def test_07_historical_baselines_preserved(self):
        # Verify previous models preserved
        self.assertTrue(os.path.exists(os.path.join("models", "road_model.pkl")))
        self.assertTrue(os.path.exists(os.path.join("models", "baselines", "xgboost_synthetic")))
        self.assertTrue(os.path.exists(os.path.join("models", "road_risk_v2", "model.json")))

if __name__ == "__main__":
    unittest.main()
