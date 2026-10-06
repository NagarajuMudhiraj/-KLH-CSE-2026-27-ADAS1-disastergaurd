import os
import json
import unittest

class TestPhase18Calibration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.v4_dir = os.path.join(cls.repo_root, "models", "road_risk_v4")
        cls.cal_params_file = os.path.join(cls.v4_dir, "calibration_params.json")
        cls.cal_results_file = os.path.join(cls.v4_dir, "calibrated_model_results.json")

    def test_01_artifacts_exist(self):
        """Verify calibration artifacts are saved."""
        self.assertTrue(os.path.exists(self.cal_params_file), "calibration_params.json missing")
        self.assertTrue(os.path.exists(self.cal_results_file), "calibrated_model_results.json missing")

    def test_02_temperature_scaling_bounds(self):
        """Verify optimal temperature scalar is well-conditioned."""
        with open(self.cal_params_file, "r") as f:
            params = json.load(f)
            
        T = params["temperature_T"]
        self.assertGreater(T, 0.5)
        self.assertLess(T, 3.0)

    def test_03_calibration_improves_brier_and_loss(self):
        """Verify Temperature Scaling strictly reduces Brier score and Log-Loss."""
        with open(self.cal_params_file, "r") as f:
            params = json.load(f)
            
        brier_raw = params["brier_score_raw"]
        brier_cal = params["brier_score_calibrated"]
        self.assertLess(brier_cal, brier_raw, "Calibration failed to reduce Brier score loss")
        
        logloss_raw = params["log_loss_raw"]
        logloss_cal = params["log_loss_calibrated"]
        self.assertLess(logloss_cal, logloss_raw, "Calibration failed to reduce Negative Log-Loss")

    def test_04_cross_validation_performance(self):
        """Verify 5-Fold GroupKFold performance standards."""
        with open(self.cal_results_file, "r") as f:
            res = json.load(f)
            
        self.assertGreaterEqual(res["calibrated_overall_accuracy"], 0.70)
        self.assertGreaterEqual(res["calibrated_overall_recall"], 0.70)
        self.assertGreaterEqual(res["calibrated_overall_roc_auc"], 0.70)

if __name__ == "__main__":
    unittest.main()
