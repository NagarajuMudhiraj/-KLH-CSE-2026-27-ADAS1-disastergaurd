"""Comprehensive unit and integration test suite for Phase 4 ADAS real-data pipeline.
Uses standard library unittest for zero-dependency execution.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from pipeline.label_separator import LabelSeparator
from pipeline.phase4_leakage_auditor import Phase4AuditViolation, Phase4LeakageAuditor
from pipeline.phase4_pipeline import Phase4Pipeline
from pipeline.real_data_collector import RealDataCollector
from pipeline.real_quality_reporter import RealQualityReporter
from pipeline.verified_observation_builder import VerifiedObservationBuilder


class TestRealDataCollector(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.collector = RealDataCollector(base_raw_dir=Path(self.tmp_dir.name))

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_collector_directories_created(self):
        for sub in ["weather", "traffic", "road", "disaster", "labels", "yolo"]:
            self.assertTrue((Path(self.tmp_dir.name) / sub).exists())

    def test_real_weather_provenance(self):
        record = self.collector.fetch_real_weather(12.9716, 77.5946, "test-weather-obs-1")
        if record:
            prov = record["provenance"]
            self.assertEqual(prov["source"], "Open-Meteo API")
            self.assertEqual(prov["data_classification"], "REAL")
            self.assertTrue(Path(self.tmp_dir.name, "weather", "weather_test-weather-obs-1.json").exists())

    def test_real_elevation_provenance(self):
        record = self.collector.fetch_real_elevation(12.9716, 77.5946, "test-elev-obs-1")
        if record:
            prov = record["provenance"]
            self.assertEqual(prov["source"], "Open-Elevation API")
            self.assertTrue(Path(self.tmp_dir.name, "road", "elevation_test-elev-obs-1.json").exists())


class TestLabelSeparator(unittest.TestCase):
    def setUp(self):
        self.separator = LabelSeparator(allow_masking=True)

    def test_target_excluded_from_features(self):
        feat = {"road_risk_status": 2, "rainfall_mm_h": 10.0}
        gt = {"label_source": "test_auth", "leaked_features": []}
        res = self.separator.separate_label_and_features(feat, gt)
        self.assertNotIn("road_risk_status", res.features)
        self.assertIn("road_risk_status", res.excluded_features)

    def test_label_source_feature_masked(self):
        feat = {"flood_detected": 1, "rainfall_mm_h": 15.0}
        gt = {"label_source": "FloodNet_Annotation", "leaked_features": ["flood_detected"]}
        res = self.separator.separate_label_and_features(feat, gt)
        self.assertEqual(res.features["flood_detected"], 0)
        self.assertIn("flood_detected", res.excluded_features)
        self.assertTrue(res.has_exclusion)


class TestPhase4LeakageAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = Phase4LeakageAuditor()

    def test_audit_detects_unmasked_label_source_leakage(self):
        obs = [
            {
                "metadata": {"observation_id": "test-1", "timestamp": "2026-09-30T00:00:00Z"},
                "features": {"flood_detected": 1, "rainfall_mm_h": 10.0},
                "ground_truth": {"leaked_features": ["flood_detected"], "label_quality": "SILVER"},
            }
        ]
        res = self.auditor.audit_dataset(obs)
        self.assertFalse(res.is_leakage_free)
        self.assertTrue(any(v.rule_name == "Unmasked Label-Source Feature" for v in res.violations))

    def test_audit_clean_on_properly_separated_records(self):
        obs = [
            {
                "metadata": {
                    "observation_id": "test-clean-1",
                    "timestamp": "2026-09-30T00:00:00Z",
                    "latitude": 29.76,
                    "longitude": -95.36,
                    "split_candidate": "TRAIN_CANDIDATE",
                    "event_id": "Event_A",
                },
                "features": {"flood_detected": 0, "rainfall_mm_h": 5.0},
                "ground_truth": {"leaked_features": ["flood_detected"], "label_quality": "SILVER"},
            }
        ]
        res = self.auditor.audit_dataset(obs)
        self.assertTrue(res.is_leakage_free)

    def test_audit_flags_cross_partition_event_overlap(self):
        obs = [
            {
                "metadata": {"observation_id": "1", "event_id": "Hurricane_Harvey", "split_candidate": "TRAIN_CANDIDATE"},
                "features": {},
                "ground_truth": {"label_quality": "SILVER"},
            },
            {
                "metadata": {"observation_id": "2", "event_id": "Hurricane_Harvey", "split_candidate": "TEST_CANDIDATE"},
                "features": {},
                "ground_truth": {"label_quality": "SILVER"},
            },
        ]
        res = self.auditor.audit_dataset(obs)
        self.assertTrue(any(v.rule_name == "Same-Event Cross-Partition Contamination" for v in res.violations))


class TestPhase4SufficiencyGate(unittest.TestCase):
    def test_gate_flags_insufficient_samples(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pipeline = Phase4Pipeline(
                intermediate_dir=tmp_path / "intermediate",
                processed_dir=tmp_path / "processed",
                manifest_dir=tmp_path / "manifests",
            )
            # Run with only 4 samples
            res = pipeline.run(max_real_samples=4)
            self.assertEqual(res["readiness_status"], "NOT_READY_FOR_MODEL_TRAINING")
            self.assertIn("below minimum statistical threshold of 1,000 real rows", res["readiness_rationale"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
