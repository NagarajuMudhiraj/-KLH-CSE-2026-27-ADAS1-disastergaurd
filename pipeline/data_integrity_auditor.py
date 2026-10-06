"""Fail-closed provenance checks for candidate REAL training observations."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable


@dataclass
class IntegrityFinding:
    code: str
    severity: str
    observation_id: str | None
    detail: str


@dataclass
class IntegrityAuditResult:
    findings: list[IntegrityFinding] = field(default_factory=list)
    inspected_rows: int = 0

    @property
    def critical_count(self) -> int:
        return sum(item.severity == "CRITICAL" for item in self.findings)

    @property
    def is_valid(self) -> bool:
        return self.critical_count == 0


class DataIntegrityAuditor:
    """Audits evidence, not plausibility; missing evidence excludes REAL rows."""

    HARD_CODED_FEATURES = {
        "traffic_level": {2.0, 3.0},
        "road_slope_pct": {0.5, 1.0},
        "road_type": {1},
    }

    def audit(self, observations: Iterable[dict[str, Any]]) -> IntegrityAuditResult:
        rows = list(observations)
        result = IntegrityAuditResult(inspected_rows=len(rows))
        feature_values: dict[str, list[tuple[Any, tuple[Any, Any]]]] = defaultdict(list)
        real_locations: list[tuple[float, float]] = []
        real_times: list[str] = []

        for row in rows:
            meta = row.get("metadata", row)
            features = row.get("features", row)
            provenance = row.get("provenance", {})
            obs_id = meta.get("observation_id")
            classification = meta.get("data_classification") or meta.get("source_classification")
            is_real = classification == "REAL"
            location = (meta.get("latitude"), meta.get("longitude"))
            observed_at = meta.get("timestamp")
            reasons = set(meta.get("validation_reasons") or [])

            if is_real and (location[0] is None or location[1] is None):
                self._add(result, "MISSING_SOURCE_NATIVE_LOCATION", obs_id, "REAL row has no source-native location")
            if is_real and not observed_at:
                self._add(result, "MISSING_SOURCE_NATIVE_TIMESTAMP", obs_id, "REAL row has no source-native timestamp")
            if is_real and ("generated" in str(meta).lower() or "jitter" in str(meta).lower()):
                self._add(result, "GENERATED_COORDINATE_OR_TIMESTAMP", obs_id, "REAL metadata indicates generated spatial or temporal values")
            for reason in reasons:
                if reason in {"MISSING_SOURCE_NATIVE_LOCATION", "MISSING_SOURCE_NATIVE_TIMESTAMP"}:
                    self._add(result, reason, obs_id, "row was already rejected by source validation")
            if is_real and location[0] is not None and location[1] is not None:
                real_locations.append((float(location[0]), float(location[1])))
            if is_real and observed_at:
                real_times.append(str(observed_at))

            for feature, value in features.items():
                if value is None:
                    continue
                feature_values[feature].append((value, location))
                feature_prov = provenance.get(feature, {})
                source_class = feature_prov.get("source_classification")
                if is_real and source_class in {"REALISTIC_SIMULATION", "SYNTHETIC_BENCHMARK", "UNAVAILABLE"}:
                    self._add(result, "REAL_ROW_NONREAL_PROVIDER", obs_id, f"{feature} came from {source_class}")
                if is_real and not feature_prov:
                    self._add(result, "MISSING_FEATURE_PROVENANCE", obs_id, f"{feature} has no source evidence")
                if is_real and feature_prov and not feature_prov.get("is_available", True):
                    self._add(result, "UNAVAILABLE_FEATURE_POPULATED", obs_id, f"{feature} has a value from an unavailable provider")
                if is_real and feature in self.HARD_CODED_FEATURES and value in self.HARD_CODED_FEATURES[feature]:
                    self._add(result, "HARDCODED_FEATURE_VALUE", obs_id, f"{feature}={value} matches prohibited fallback")
                if is_real and feature.startswith("rainfall") or (is_real and feature in {"temperature_c", "wind_speed_kmh"}):
                    self._check_weather_alignment(result, obs_id, observed_at, location, feature, feature_prov)

        self._check_suspicious_constants(result, feature_values)
        self._check_generated_patterns(result, real_locations, real_times)
        return result

    @staticmethod
    def _add(result: IntegrityAuditResult, code: str, obs_id: str | None, detail: str, severity: str = "CRITICAL") -> None:
        result.findings.append(IntegrityFinding(code, severity, obs_id, detail))

    def _check_weather_alignment(self, result: IntegrityAuditResult, obs_id: str | None, observed_at: Any, location: tuple[Any, Any], feature: str, prov: dict[str, Any]) -> None:
        if not prov:
            return
        source_time = prov.get("observed_at") or prov.get("source_timestamp")
        source_location = prov.get("location") or {}
        if source_time and observed_at and self._parse(source_time) > self._parse(observed_at):
            self._add(result, "WEATHER_AFTER_OBSERVATION", obs_id, f"{feature} source time is after observation time")
        if source_time and prov.get("retrieved_at") == observed_at and source_time == observed_at:
            self._add(result, "RETRIEVAL_TIME_USED_AS_OBSERVATION_TIME", obs_id, f"{feature} uses retrieval time as observation time")
        if source_location and (source_location.get("latitude"), source_location.get("longitude")) != location:
            self._add(result, "WEATHER_LOCATION_MISMATCH", obs_id, f"{feature} source location differs from observation location")

    def _check_suspicious_constants(self, result: IntegrityAuditResult, values: dict[str, list[tuple[Any, tuple[Any, Any]]]]) -> None:
        for feature in ("traffic_level", "road_slope_pct", "road_type"):
            entries = values.get(feature, [])
            if len(entries) > 1 and len({value for value, _ in entries}) == 1:
                self._add(result, "SUSPICIOUS_CONSTANT_FEATURE", None, f"{feature} is identical across {len(entries)} rows", "HIGH")
        elevations = values.get("elevation_m", [])
        if len(elevations) > 1:
            by_value = defaultdict(set)
            for value, location in elevations:
                by_value[value].add(location)
            for value, locations in by_value.items():
                if len(locations) > 1:
                    self._add(result, "REUSED_ELEVATION_ACROSS_LOCATIONS", None, f"elevation_m={value} occurs at {len(locations)} locations", "HIGH")

    def _check_generated_patterns(self, result: IntegrityAuditResult, locations: list[tuple[float, float]], times: list[str]) -> None:
        if len(locations) >= 4:
            lat_steps = {round(locations[i + 1][0] - locations[i][0], 6) for i in range(len(locations) - 1)}
            lon_steps = {round(locations[i + 1][1] - locations[i][1], 6) for i in range(len(locations) - 1)}
            if len(lat_steps) == 1 and len(lon_steps) == 1 and (lat_steps != {0.0} or lon_steps != {0.0}):
                self._add(result, "GENERATED_COORDINATE_PATTERN", None, "coordinates form a constant-step interpolation", "HIGH")
        if len(times) >= 8 and len(set(times)) < len(times) and len(set(times)) <= 8:
            self._add(result, "GENERATED_TIMESTAMP_PATTERN", None, "timestamps repeat a short cycle across observations", "HIGH")

    @staticmethod
    def _parse(value: Any) -> datetime:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
