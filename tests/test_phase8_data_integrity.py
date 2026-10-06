import unittest
from datetime import datetime, timezone

from pipeline.data_integrity_auditor import DataIntegrityAuditor
from pipeline.providers.base import ProviderMode, SourceClassification
from pipeline.providers.road_provider import RoadProvider
from pipeline.providers.traffic_provider import TrafficProvider
from pipeline.providers.weather_provider import WeatherProvider


class TestPhase8DataIntegrity(unittest.TestCase):
    def _real(self, features, provenance=None, **meta):
        return {"metadata": {"observation_id": "r1", "timestamp": "2017-08-28T10:00:00+00:00", "latitude": 1.0, "longitude": 2.0, "data_classification": "REAL", **meta}, "features": features, "provenance": provenance or {}}

    def test_generated_location_and_timestamp_rejected(self):
        row = self._real({}, validation_reasons=["MISSING_SOURCE_NATIVE_LOCATION", "MISSING_SOURCE_NATIVE_TIMESTAMP"])
        codes = {x.code for x in DataIntegrityAuditor().audit([row]).findings}
        self.assertIn("MISSING_SOURCE_NATIVE_LOCATION", codes)
        self.assertIn("MISSING_SOURCE_NATIVE_TIMESTAMP", codes)

    def test_hardcoded_and_reused_values_are_flagged(self):
        provenance = {name: {"source_classification": "REAL", "is_available": True} for name in ("traffic_level", "road_slope_pct", "road_type", "elevation_m")}
        row1 = self._real({"traffic_level": 2.0, "road_slope_pct": 0.5, "road_type": 1, "elevation_m": 18.33}, provenance)
        row2 = self._real({"traffic_level": 2.0, "road_slope_pct": 0.5, "road_type": 1, "elevation_m": 18.33}, provenance, observation_id="r2", latitude=3.0, longitude=4.0)
        codes = {x.code for x in DataIntegrityAuditor().audit([row1, row2]).findings}
        self.assertTrue({"HARDCODED_FEATURE_VALUE", "SUSPICIOUS_CONSTANT_FEATURE", "REUSED_ELEVATION_ACROSS_LOCATIONS"}.issubset(codes))

    def test_generated_coordinate_and_timestamp_patterns_flagged(self):
        rows = []
        for index in range(8):
            rows.append(self._real({}, observation_id=f"r{index}", latitude=1.0 + index * 0.01, longitude=2.0 + index * 0.01, timestamp=f"2017-08-28T{10 + (index % 2):02}:00:00+00:00"))
        codes = {x.code for x in DataIntegrityAuditor().audit(rows).findings}
        self.assertIn("GENERATED_COORDINATE_PATTERN", codes)
        self.assertIn("GENERATED_TIMESTAMP_PATTERN", codes)

    def test_weather_time_and_provider_classification_rejected(self):
        row = self._real({"rainfall_mm_h": 4.0}, {"rainfall_mm_h": {"source_classification": "REALISTIC_SIMULATION", "is_available": True, "observed_at": "2017-08-28T11:00:00+00:00", "retrieved_at": "2017-08-28T11:00:00+00:00", "location": {"latitude": 9.0, "longitude": 9.0}}})
        codes = {x.code for x in DataIntegrityAuditor().audit([row]).findings}
        self.assertIn("REAL_ROW_NONREAL_PROVIDER", codes)
        self.assertIn("WEATHER_AFTER_OBSERVATION", codes)
        self.assertIn("WEATHER_LOCATION_MISMATCH", codes)

    def test_live_stubs_fail_closed(self):
        traffic = TrafficProvider(mode=ProviderMode.LIVE).fetch(1.0, 2.0)
        road = RoadProvider(mode=ProviderMode.LIVE).fetch(1.0, 2.0)
        self.assertEqual(traffic.source_classification, SourceClassification.UNAVAILABLE)
        self.assertEqual(road.source_classification, SourceClassification.UNAVAILABLE)
        self.assertEqual(traffic.data, {})
        self.assertEqual(road.data, {})

    def test_provider_contract_and_fixture_classification(self):
        result = WeatherProvider(mode=ProviderMode.FIXTURE).fetch(1.0, 2.0)
        payload = result.to_dict()
        for key in ("source_classification", "source_name", "observed_at", "retrieved_at", "location", "provenance", "data_quality"):
            self.assertIn(key, payload)
        self.assertEqual(result.source_classification, SourceClassification.SYNTHETIC_BENCHMARK)

    def test_historical_live_weather_fails_closed(self):
        result = WeatherProvider(mode=ProviderMode.LIVE).fetch(1.0, 2.0, timestamp=datetime(2017, 8, 28, tzinfo=timezone.utc))
        self.assertEqual(result.source_classification, SourceClassification.UNAVAILABLE)
        self.assertEqual(result.data, {})


if __name__ == "__main__":
    unittest.main()
