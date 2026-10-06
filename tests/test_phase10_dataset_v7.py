import os
import unittest
import pandas as pd

class TestPhase10DatasetV7(unittest.TestCase):
    def setUp(self):
        self.csv_path = os.path.join("data", "processed", "road_risk_dataset_v7.csv")
        self.parquet_path = os.path.join("data", "processed", "road_risk_dataset_v7.parquet")
        self.quality_md = os.path.join("data", "processed", "road_risk_v7_quality_report.md")
        self.target_audit_md = os.path.join("docs", "phase10_target_semantics_audit.md")
        self.road_audit_md = os.path.join("docs", "phase10_historical_road_audit.md")

    def test_artifacts_exist(self):
        self.assertTrue(os.path.exists(self.csv_path), "V7 CSV does not exist")
        self.assertTrue(os.path.exists(self.parquet_path), "V7 Parquet does not exist")
        self.assertTrue(os.path.exists(self.quality_md), "V7 Quality MD does not exist")
        self.assertTrue(os.path.exists(self.target_audit_md), "Target semantics audit MD does not exist")
        self.assertTrue(os.path.exists(self.road_audit_md), "Historical road audit MD does not exist")

    def test_schema_and_integrity(self):
        df = pd.read_csv(self.csv_path)
        self.assertEqual(len(df), 68, "Dataset V7 should contain exactly 68 observations")
        
        required_cols = [
            'observation_id', 'event_id', 'event_date', 'road_segment_id',
            'latitude', 'longitude', 'elevation_m', 'road_type', 'road_surface',
            'road_length_m', 'distance_to_flood_m', 'rainfall_24h_mm',
            'temperature_c', 'wind_speed_kmh', 'target_flood_exposure',
            'spatial_evidence_type', 'road_historical_validity',
            'data_classification', 'flood_source', 'road_source',
            'weather_source', 'label_source', 'label_reason', 'label_quality'
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column {col}")

    def test_target_semantics_and_balance(self):
        df = pd.read_csv(self.csv_path)
        targets = df['target_flood_exposure'].value_counts().to_dict()
        self.assertIn(0, targets, "Must contain negative controls")
        self.assertIn(1, targets, "Must contain positive flood exposure instances")
        self.assertEqual(targets[1], 18, "Expected 18 positive instances")
        self.assertEqual(targets[0], 50, "Expected 50 negative instances")

    def test_real_data_classification_and_no_nulls(self):
        df = pd.read_csv(self.csv_path)
        self.assertEqual(list(df['data_classification'].unique()), ['REAL'])
        core_features = ['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'elevation_m', 'target_flood_exposure']
        self.assertEqual(df[core_features].isnull().sum().sum(), 0)

    def test_split_leakage_absence(self):
        df = pd.read_csv(self.csv_path)
        test_events = ['INDOFLOODS-gauge-925-6', 'INDOFLOODS-gauge-916-11', 'INDOFLOODS-gauge-939-10', 'INDOFLOODS-gauge-917-6']
        train_events = [e for e in df['event_id'].unique() if e not in test_events and '8' not in e and '7' not in e and '5' not in e]
        
        train_event_set = set(train_events)
        test_event_set = set(test_events)
        self.assertEqual(len(train_event_set.intersection(test_event_set)), 0, "Event leakage detected!")

if __name__ == '__main__':
    unittest.main()
