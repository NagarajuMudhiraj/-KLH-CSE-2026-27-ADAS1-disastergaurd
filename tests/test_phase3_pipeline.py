"""Comprehensive unit and integration tests for Phase 3 ADAS road-risk pipeline.
Uses standard library unittest for zero-dependency execution.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure repo root and backend are on sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.services.feature_builder import CANONICAL_FEATURE_ORDER
from pipeline.dataset_pipeline import DatasetPipeline
from pipeline.label_constructor import LabelAssignment, LabelConstructor
from pipeline.leakage_auditor import LeakageAuditor
from pipeline.observation_builder import ObservationBuilder
from pipeline.providers.base import ProviderMode, SourceClassification
from pipeline.providers.disaster_provider import DisasterReportProvider
from pipeline.providers.road_provider import RoadProvider
from pipeline.providers.telemetry_provider import TelemetryProvider
from pipeline.providers.traffic_provider import TrafficProvider
from pipeline.providers.weather_provider import WeatherProvider
from pipeline.providers.yolo_feature_provider import YOLOFeatureProvider
from pipeline.quality_reporter import QualityReporter


class TestProviders(unittest.TestCase):
    def test_weather_provider_simulation_bounds(self):
        wp = WeatherProvider(mode=ProviderMode.SIMULATOR)
        res = wp.fetch(12.97, 77.59, scenario="heavy_monsoon")
        self.assertTrue(res.is_available)
        self.assertEqual(res.source_classification, SourceClassification.REALISTIC_SIMULATION)
        self.assertTrue(0.0 <= res.data["rainfall_mm_h"] <= 300.0)
        self.assertTrue(0.0 <= res.data["visibility_m"] <= 10000.0)
        self.assertTrue(-40.0 <= res.data["temperature_c"] <= 60.0)

    def test_weather_provider_fixture_mode(self):
        fixture = {
            "rainfall_mm_h": 22.5,
            "rainfall_10min_mm": 3.75,
            "rainfall_1h_mm": 22.5,
            "visibility_m": 4500.0,
            "temperature_c": 21.0,
            "wind_speed_kmh": 40.0,
        }
        wp = WeatherProvider(mode=ProviderMode.FIXTURE, fixture_data=fixture)
        res = wp.fetch(0.0, 0.0)
        self.assertEqual(res.data, fixture)

    def test_yolo_provider_simulation(self):
        yp = YOLOFeatureProvider(mode=ProviderMode.SIMULATOR)
        res = yp.fetch(scenario="water_hazard")
        self.assertEqual(res.data["flood_detected"], 1)
        self.assertTrue(res.data["hazard_distance_m"] <= 500.0)

    def test_disaster_provider_simulation(self):
        dp = DisasterReportProvider(mode=ProviderMode.SIMULATOR)
        res = dp.fetch(scenario="blocked_route")
        self.assertEqual(res.data["road_closure_report"], 1)
        self.assertEqual(res.data["flood_report"], 1)

    def test_road_provider_features(self):
        rp = RoadProvider(mode=ProviderMode.SIMULATOR)
        res = rp.fetch(scenario="mountain_pass")
        self.assertIn(res.data["road_type"], [0, 1, 2, 3, 4])
        self.assertTrue(-35.0 <= res.data["road_slope_pct"] <= 35.0)
        self.assertTrue(-100.0 <= res.data["elevation_m"] <= 6000.0)

    def test_traffic_provider_features(self):
        tp = TrafficProvider(mode=ProviderMode.SIMULATOR)
        res = tp.fetch(scenario="congested")
        self.assertTrue(1.0 <= res.data["traffic_level"] <= 10.0)
        self.assertTrue(0.0 <= res.data["vehicle_density"] <= 200.0)

    def test_telemetry_provider_features(self):
        tel = TelemetryProvider(mode=ProviderMode.SIMULATOR)
        res = tel.fetch(scenario="emergency_stop")
        self.assertTrue(0.0 <= res.data["vehicle_speed_kmh"] <= 200.0)
        self.assertTrue(-12.0 <= res.data["acceleration_mps2"] <= 8.0)
        self.assertTrue(0.0 <= res.data["braking_intensity"] <= 1.0)


class TestObservationBuilder(unittest.TestCase):
    def test_observation_assembly_canonical_features(self):
        builder = ObservationBuilder()
        obs = builder.build_observation(latitude=13.0827, longitude=80.2707, scenario="clear")

        self.assertIn("observation_id", obs["metadata"])
        self.assertEqual(obs["metadata"]["latitude"], 13.0827)
        self.assertIn(obs["metadata"]["data_quality"], ["HIGH", "MODERATE", "DEGRADED"])

        features = obs["features"]
        self.assertEqual(len(features), 25)
        for feat in CANONICAL_FEATURE_ORDER:
            self.assertIn(feat, features, f"Missing canonical feature: {feat}")


class TestLabelConstructor(unittest.TestCase):
    def setUp(self):
        self.lc = LabelConstructor()

    def test_assign_blocked_on_closure_report(self):
        obs = {"features": {"road_closure_report": 1, "rainfall_mm_h": 0.0}}
        assignment = self.lc.assign_label(obs)
        self.assertEqual(assignment.road_risk_status, 2)
        self.assertEqual(assignment.label_name, "BLOCKED")
        self.assertIn("road_closure_report", assignment.leaked_features)

    def test_assign_blocked_on_severe_physical_hazard(self):
        obs = {"features": {"fire_detected": 1, "obstacle_count": 2}}
        assignment = self.lc.assign_label(obs)
        self.assertEqual(assignment.road_risk_status, 2)
        self.assertEqual(assignment.label_name, "BLOCKED")

    def test_assign_risky_on_flood_advisory(self):
        obs = {"features": {"flood_report": 1, "rainfall_mm_h": 5.0}}
        assignment = self.lc.assign_label(obs)
        self.assertEqual(assignment.road_risk_status, 1)
        self.assertEqual(assignment.label_name, "RISKY")
        self.assertIn("flood_report", assignment.leaked_features)

    def test_assign_risky_on_heavy_rain(self):
        obs = {"features": {"rainfall_mm_h": 25.0, "visibility_m": 6000.0}}
        assignment = self.lc.assign_label(obs)
        self.assertEqual(assignment.road_risk_status, 1)
        self.assertEqual(assignment.label_name, "RISKY")

    def test_assign_safe_under_mild_conditions(self):
        obs = {"features": {"rainfall_mm_h": 0.0, "visibility_m": 8000.0, "flood_detected": 0}}
        assignment = self.lc.assign_label(obs)
        self.assertEqual(assignment.road_risk_status, 0)
        self.assertEqual(assignment.label_name, "SAFE")


class TestLeakageAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = LeakageAuditor(mask_leaked_features=True)

    def test_rule1_target_in_features_detected_and_removed(self):
        feat = {"road_risk_status": 2, "rainfall_mm_h": 10.0}
        cleaned, violations = self.auditor.audit_record(feat, {}, {})
        self.assertNotIn("road_risk_status", cleaned)
        self.assertTrue(any(v.rule_number == 1 and v.severity == "CRITICAL" for v in violations))

    def test_rule2_direct_label_source_masked(self):
        feat = {"road_closure_report": 1, "rainfall_mm_h": 0.0}
        label_info = {"leaked_features": ["road_closure_report"]}
        cleaned, violations = self.auditor.audit_record(feat, label_info, {})
        self.assertEqual(cleaned["road_closure_report"], 0)
        self.assertTrue(any(v.rule_number == 2 for v in violations))

    def test_rule6_identifiers_in_features(self):
        feat = {"observation_id": "abc-123", "timestamp": "2026-09-30", "rainfall_mm_h": 5.0}
        cleaned, violations = self.auditor.audit_record(feat, {}, {})
        self.assertNotIn("observation_id", cleaned)
        self.assertNotIn("timestamp", cleaned)
        self.assertTrue(any(v.rule_number == 6 and v.severity == "CRITICAL" for v in violations))

    def test_rule10_invariant_violation(self):
        feat = {"rainfall_mm_h": -5.0, "visibility_m": 120000.0}
        cleaned, violations = self.auditor.audit_record(feat, {}, {})
        self.assertTrue(any(v.rule_number == 10 and v.severity == "CRITICAL" for v in violations))


class TestPipelineIntegration(unittest.TestCase):
    def test_end_to_end_pipeline_simulation_run(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pipeline = DatasetPipeline(
                mode="simulate",
                raw_dir=tmp_path / "raw",
                intermediate_dir=tmp_path / "intermediate",
                processed_dir=tmp_path / "processed",
                manifest_dir=tmp_path / "manifests",
            )
            res = pipeline.run_pipeline(count=20)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertTrue(res["count"] > 0)
            self.assertTrue(Path(res["csv_path"]).exists())
            self.assertTrue(Path(res["manifest_path"]).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
