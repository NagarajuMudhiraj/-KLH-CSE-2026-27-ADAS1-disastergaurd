import os
import unittest
import pandas as pd

class TestPhase9GeospatialPilot(unittest.TestCase):
    def setUp(self):
        self.pilot_csv = os.path.join("data", "processed", "road_risk_geospatial_pilot.csv")
        self.quality_md = os.path.join("data", "processed", "road_risk_geospatial_pilot_quality.md")
        self.target_decision_md = os.path.join("docs", "road_risk_target_decision_v6.md")

    def test_artifacts_exist(self):
        self.assertTrue(os.path.exists(self.pilot_csv), "Pilot CSV does not exist")
        self.assertTrue(os.path.exists(self.quality_md), "Quality report MD does not exist")
        self.assertTrue(os.path.exists(self.target_decision_md), "Target decision MD does not exist")

    def test_pilot_schema_and_size(self):
        df = pd.read_csv(self.pilot_csv)
        self.assertGreaterEqual(len(df), 10, "Pilot must have at least 10 observations")
        self.assertLessEqual(len(df), 50, "Pilot should not exceed 50 observations")
        
        required_cols = [
            'observation_id', 'event_id', 'event_date', 'road_segment_id',
            'latitude', 'longitude', 'elevation_m', 'road_type', 'road_surface',
            'road_length_m', 'distance_to_flood_m', 'rainfall_24h_mm',
            'temperature_c', 'wind_speed_kmh', 'target_flooded',
            'data_classification', 'flood_source', 'road_source',
            'weather_source', 'label_source', 'label_reason', 'label_quality'
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing column {col} in pilot CSV")

    def test_real_data_classification_only(self):
        df = pd.read_csv(self.pilot_csv)
        unique_classifications = df['data_classification'].unique()
        self.assertEqual(list(unique_classifications), ['REAL'], "All pilot rows must be REAL")

    def test_target_distribution(self):
        df = pd.read_csv(self.pilot_csv)
        targets = df['target_flooded'].value_counts().to_dict()
        self.assertIn(0, targets, "Pilot must contain negative instances")
        self.assertIn(1, targets, "Pilot must contain positive instances")
        self.assertGreater(targets[0], 0)
        self.assertGreater(targets[1], 0)

    def test_no_leakage(self):
        df = pd.read_csv(self.pilot_csv)
        # Verify no duplicate observations
        self.assertEqual(df.duplicated(subset=['observation_id']).sum(), 0)
        # Verify no duplicate (event, road) observations
        self.assertEqual(df.duplicated(subset=['event_id', 'road_segment_id']).sum(), 0)
        # Verify no nulls in core features
        self.assertEqual(df[['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'elevation_m', 'target_flooded']].isnull().sum().sum(), 0)

if __name__ == '__main__':
    unittest.main()
