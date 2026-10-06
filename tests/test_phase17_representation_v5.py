import os
import json
import unittest
import pandas as pd
import numpy as np

class TestPhase17RepresentationV5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.v10_csv = os.path.join(cls.repo_root, "data", "processed", "road_risk_dataset_v10.csv")
        cls.assertTrue(os.path.exists(cls.v10_csv), "Dataset V10 CSV does not exist")
        cls.df = pd.read_csv(cls.v10_csv)

    def test_01_row_count_and_columns(self):
        """Verify row count is exactly 68 real observations and new features exist."""
        self.assertEqual(len(self.df), 68)
        required_cols = [
            'soil_moisture_surface',
            'stream_order',
            'drainage_area_km2',
            'catchment_rain_anomaly',
            'local_rain_anomaly',
            'normalized_hand',
            'hazard_ratio',
            'is_dam_regulated',
            'upstream_dam_release_active',
            'dam_floodway_vulnerable',
            'pavement_water_depth_cm',
            'adas_pavement_safety_tier'
        ]
        for col in required_cols:
            self.assertIn(col, self.df.columns)
            self.assertEqual(self.df[col].isna().sum(), 0)

    def test_02_soil_moisture_physical_bounds(self):
        """Verify volumetric soil moisture is strictly within physical boundaries."""
        sm = self.df['soil_moisture_surface']
        self.assertTrue((sm >= 0.05).all(), "Soil moisture below physical dry limit")
        self.assertTrue((sm <= 0.65).all(), "Soil moisture above total porosity limit")

    def test_03_pavement_depth_and_tiers(self):
        """Verify pavement water depth calculation and valid ADAS safety tiers."""
        depth = self.df['pavement_water_depth_cm']
        self.assertTrue((depth >= 0.0).all(), "Pavement water depth cannot be negative")
        
        valid_tiers = {'DRY_PASSABLE', 'SHALLOW_CAUTION', 'HIGH_RISK_STALL', 'IMPASSABLE_SUBMERGED'}
        tiers_in_data = set(self.df['adas_pavement_safety_tier'].unique())
        self.assertTrue(tiers_in_data.issubset(valid_tiers))

    def test_04_dual_hazard_results(self):
        """Verify dual-hazard evaluation artifact exists and achieved 100% recall on Fold B."""
        res_path = os.path.join(self.repo_root, "models", "road_risk_v4", "phase17_dual_hazard_results.json")
        self.assertTrue(os.path.exists(res_path), "Dual hazard results JSON missing")
        with open(res_path, "r") as f:
            res = json.load(f)
            
        self.assertEqual(res["cross_basin_fold_B"]["recall"], 1.0)
        self.assertEqual(res["cross_basin_fold_B"]["accuracy"], 1.0)
        self.assertGreaterEqual(res["unseen_roads"]["accuracy"], 0.80)

if __name__ == "__main__":
    unittest.main()
