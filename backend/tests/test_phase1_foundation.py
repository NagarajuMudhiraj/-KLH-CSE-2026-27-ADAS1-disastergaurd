"""
Phase 1 Validation Tests — ADAS Road-Risk Foundation
Tests for:
  - Valid feature inputs
  - Boundary violations (negative rainfall, visibility, speed, etc.)
  - Invalid traffic level
  - Invalid probability values / probability sum
  - Missing required fields
  - Optional fields (present and absent)
  - Canonical feature ordering matches config
  - Configuration / schema consistency
  - Existing POST /api/predict-road backward compatibility
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import hashlib
import numpy as np
from pydantic import ValidationError

from app.models.schemas import (
    RoadPredictionInput,
    RoadRiskFeatures,
    RoadRiskPrediction,
)
from app.services.feature_builder import (
    build_canonical_feature_dict,
    build_canonical_feature_vector,
    get_canonical_feature_order,
    get_feature_contract_version,
    get_feature_metadata,
    assess_data_quality,
    CANONICAL_FEATURE_ORDER,
    FEATURE_METADATA_MAP,
)

_PASS = "\033[92m  PASS\033[0m"
_FAIL = "\033[91m  FAIL\033[0m"
_RESULTS = {"passed": 0, "failed": 0}

def _report(name: str, passed: bool, note: str = ""):
    status = _PASS if passed else _FAIL
    print(f"{status}  {name}" + (f" — {note}" if note else ""))
    _RESULTS["passed" if passed else "failed"] += 1


# ============================================================
# Section 1: Valid Feature Inputs
# ============================================================
print("\n── Section 1: Valid Feature Inputs ──")

try:
    f = RoadRiskFeatures(rainfall_mm_h=20.0, traffic_level=5.0)
    _report("Minimal required fields (rainfall_mm_h + traffic_level)", True)
except Exception as e:
    _report("Minimal required fields (rainfall_mm_h + traffic_level)", False, str(e))

try:
    f = RoadRiskFeatures(
        rainfall_mm_h=0.0, traffic_level=1.0,
        visibility_m=10000.0, temperature_c=-10.0, wind_speed_kmh=0.0
    )
    _report("Zero edge values (rainfall=0, traffic=1, vis=10000)", True)
except Exception as e:
    _report("Zero edge values", False, str(e))

try:
    f = RoadRiskFeatures(
        rainfall_mm_h=300.0, traffic_level=10.0,
        vehicle_speed_kmh=200.0, acceleration_mps2=8.0,
        braking_intensity=1.0, road_slope_pct=35.0,
        elevation_m=6000.0, road_type=4,
        vehicle_count=100, person_count=100,
        fire_detected=1, smoke_detected=1, flood_detected=1,
        obstacle_count=50, hazard_count=100, hazard_distance_m=0.0,
        flood_report=1, road_closure_report=1
    )
    _report("Maximum boundary values for all fields", True)
except Exception as e:
    _report("Maximum boundary values for all fields", False, str(e))

try:
    f = RoadRiskFeatures(
        rainfall_mm_h=45.0, traffic_level=7.5,
        rainfall_10min_mm=7.5, rainfall_1h_mm=45.0,
        visibility_m=500.0, temperature_c=35.0, wind_speed_kmh=80.0,
        vehicle_density=80.0, congestion_change=2.5,
        vehicle_speed_kmh=30.0, acceleration_mps2=-3.0, braking_intensity=0.6,
        road_slope_pct=-5.0, elevation_m=420.0, road_type=0,
        vehicle_count=12, person_count=3, fire_detected=0, smoke_detected=1,
        flood_detected=1, obstacle_count=2, hazard_count=15, hazard_distance_m=45.0,
        flood_report=1, road_closure_report=0
    )
    _report("Full feature input (all 25 features provided)", True)
except Exception as e:
    _report("Full feature input (all 25 features provided)", False, str(e))


# ============================================================
# Section 2: Negative/Invalid Values
# ============================================================
print("\n── Section 2: Boundary Violation Rejection ──")

def _expect_validation_error(name, **kwargs):
    try:
        RoadRiskFeatures(**kwargs)
        _report(name, False, "Expected ValidationError but none was raised")
    except ValidationError:
        _report(name, True)
    except Exception as e:
        _report(name, False, f"Unexpected error type: {type(e).__name__}: {e}")

_expect_validation_error(
    "Reject negative rainfall_mm_h",
    rainfall_mm_h=-1.0, traffic_level=5.0
)
_expect_validation_error(
    "Reject rainfall_mm_h > 300",
    rainfall_mm_h=301.0, traffic_level=5.0
)
_expect_validation_error(
    "Reject negative visibility_m",
    rainfall_mm_h=20.0, traffic_level=5.0, visibility_m=-1.0
)
_expect_validation_error(
    "Reject visibility_m > 10000",
    rainfall_mm_h=20.0, traffic_level=5.0, visibility_m=10001.0
)
_expect_validation_error(
    "Reject negative vehicle_speed_kmh",
    rainfall_mm_h=20.0, traffic_level=5.0, vehicle_speed_kmh=-5.0
)
_expect_validation_error(
    "Reject vehicle_speed_kmh > 200",
    rainfall_mm_h=20.0, traffic_level=5.0, vehicle_speed_kmh=201.0
)
_expect_validation_error(
    "Reject traffic_level < 1 (0.5)",
    rainfall_mm_h=20.0, traffic_level=0.5
)
_expect_validation_error(
    "Reject traffic_level > 10 (10.1)",
    rainfall_mm_h=20.0, traffic_level=10.1
)
_expect_validation_error(
    "Reject acceleration_mps2 < -12",
    rainfall_mm_h=20.0, traffic_level=5.0, acceleration_mps2=-13.0
)
_expect_validation_error(
    "Reject braking_intensity > 1.0",
    rainfall_mm_h=20.0, traffic_level=5.0, braking_intensity=1.1
)
_expect_validation_error(
    "Reject temperature_c > 60",
    rainfall_mm_h=20.0, traffic_level=5.0, temperature_c=61.0
)
_expect_validation_error(
    "Reject fire_detected=2 (must be 0 or 1)",
    rainfall_mm_h=20.0, traffic_level=5.0, fire_detected=2
)
_expect_validation_error(
    "Reject road_type=5 (max is 4)",
    rainfall_mm_h=20.0, traffic_level=5.0, road_type=5
)
_expect_validation_error(
    "Reject hazard_distance_m > 500",
    rainfall_mm_h=20.0, traffic_level=5.0, hazard_distance_m=501.0
)


# ============================================================
# Section 3: Missing Required Fields
# ============================================================
print("\n── Section 3: Missing Required Fields ──")

try:
    RoadRiskFeatures(traffic_level=5.0)  # Missing rainfall_mm_h
    _report("Reject missing rainfall_mm_h", False, "Expected ValidationError but none raised")
except ValidationError:
    _report("Reject missing rainfall_mm_h", True)

try:
    RoadRiskFeatures(rainfall_mm_h=20.0)  # Missing traffic_level
    _report("Reject missing traffic_level", False, "Expected ValidationError but none raised")
except ValidationError:
    _report("Reject missing traffic_level", True)

try:
    RoadRiskFeatures()  # Both required missing
    _report("Reject entirely empty input", False, "Expected ValidationError but none raised")
except ValidationError:
    _report("Reject entirely empty input", True)


# ============================================================
# Section 4: Optional Fields Behavior
# ============================================================
print("\n── Section 4: Optional Fields ──")

try:
    f = RoadRiskFeatures(rainfall_mm_h=10.0, traffic_level=3.0)
    assert f.visibility_m is None
    assert f.vehicle_speed_kmh is None
    assert f.fire_detected is None
    _report("Optional fields default to None when not provided", True)
except Exception as e:
    _report("Optional fields default to None when not provided", False, str(e))

try:
    f = RoadRiskFeatures(rainfall_mm_h=10.0, traffic_level=3.0,
                          visibility_m=None, vehicle_speed_kmh=None)
    assert f.visibility_m is None
    assert f.vehicle_speed_kmh is None
    _report("Explicit None accepted for optional fields", True)
except Exception as e:
    _report("Explicit None accepted for optional fields", False, str(e))


# ============================================================
# Section 5: RoadRiskPrediction Probability Validation
# ============================================================
print("\n── Section 5: RoadRiskPrediction Probability Constraints ──")

try:
    p = RoadRiskPrediction(
        predicted_class="Risky",
        safe_probability=0.12, risky_probability=0.73, blocked_probability=0.15,
        model_version="synthetic-baseline-v1", data_quality="HIGH"
    )
    _report("Valid probability triplet (0.12+0.73+0.15=1.00)", True)
except Exception as e:
    _report("Valid probability triplet (0.12+0.73+0.15=1.00)", False, str(e))

try:
    RoadRiskPrediction(
        predicted_class="Safe",
        safe_probability=0.50, risky_probability=0.50, blocked_probability=0.50  # Sum=1.50
    )
    _report("Reject probabilities that sum > 1.02", False, "Expected ValidationError")
except ValidationError:
    _report("Reject probabilities that sum > 1.02 (sum=1.50)", True)
except Exception as e:
    _report("Reject probabilities sum > 1.02", False, str(e))

try:
    RoadRiskPrediction(
        predicted_class="Safe",
        safe_probability=0.1, risky_probability=0.1, blocked_probability=0.1  # Sum=0.30
    )
    _report("Reject probabilities that sum < 0.98 (sum=0.30)", False, "Expected ValidationError")
except ValidationError:
    _report("Reject probabilities that sum < 0.98 (sum=0.30)", True)
except Exception as e:
    _report("Reject probabilities sum < 0.98", False, str(e))

try:
    RoadRiskPrediction(
        predicted_class="Safe",
        safe_probability=-0.1, risky_probability=0.7, blocked_probability=0.4  # Negative prob
    )
    _report("Reject negative probability", False, "Expected ValidationError")
except ValidationError:
    _report("Reject negative probability (safe_prob=-0.1)", True)
except Exception as e:
    _report("Reject negative probability", False, str(e))

try:
    RoadRiskPrediction(
        predicted_class="Blocked",
        safe_probability=0.0, risky_probability=0.02, blocked_probability=0.98  # Sum=1.00
    )
    _report("Valid edge case: probabilities with zeros (sum=1.00)", True)
except Exception as e:
    _report("Valid edge case: probabilities with zeros", False, str(e))


# ============================================================
# Section 6: Canonical Feature Ordering
# ============================================================
print("\n── Section 6: Canonical Feature Ordering ──")

config_path = None
for cp in [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "road_risk_features.json")),
    os.path.abspath(os.path.join("..", "..", "config", "road_risk_features.json")),
    os.path.abspath(os.path.join("config", "road_risk_features.json")),
]:
    if os.path.exists(cp):
        config_path = cp
        break

try:
    assert config_path is not None, "config/road_risk_features.json not found"
    with open(config_path) as f:
        config = json.load(f)
    config_order = config["canonical_feature_order"]
    builder_order = get_canonical_feature_order()
    assert config_order == builder_order, f"Mismatch:\n  config={config_order}\n  builder={builder_order}"
    _report("Feature order in config matches feature builder module", True)
except Exception as e:
    _report("Feature order in config matches feature builder module", False, str(e))

try:
    f = RoadRiskFeatures(rainfall_mm_h=10.0, traffic_level=3.0)
    vec = build_canonical_feature_vector(f, as_2d=False)
    order = get_canonical_feature_order()
    assert vec.shape == (25,), f"Expected (25,), got {vec.shape}"
    # First feature in order should be rainfall_mm_h
    assert order[0] == "rainfall_mm_h"
    assert vec[0] == 10.0, f"Expected 10.0 at index 0, got {vec[0]}"
    # traffic_level is at position 6
    assert order[6] == "traffic_level"
    assert vec[6] == 3.0, f"Expected 3.0 at index 6, got {vec[6]}"
    _report("Vector positional encoding matches canonical order", True)
except Exception as e:
    _report("Vector positional encoding matches canonical order", False, str(e))

try:
    f = RoadRiskFeatures(rainfall_mm_h=10.0, traffic_level=3.0)
    vec_2d = build_canonical_feature_vector(f, as_2d=True)
    assert vec_2d.shape == (1, 25), f"Expected (1,25), got {vec_2d.shape}"
    _report("2D feature vector shape = (1, 25) for model.predict()", True)
except Exception as e:
    _report("2D feature vector shape", False, str(e))


# ============================================================
# Section 7: Config/Schema Consistency
# ============================================================
print("\n── Section 7: Config / Schema Consistency ──")

try:
    assert config_path is not None
    with open(config_path) as f:
        config = json.load(f)
    config_features = {feat["name"] for feat in config["features"]}
    schema_fields = set(RoadRiskFeatures.model_fields.keys())
    missing_in_schema = config_features - schema_fields
    extra_in_schema = schema_fields - config_features
    assert not missing_in_schema, f"Config features not in schema: {missing_in_schema}"
    assert not extra_in_schema, f"Schema fields not in config: {extra_in_schema}"
    _report("All 25 config features present in RoadRiskFeatures schema (bijective)", True)
except Exception as e:
    _report("Config/Schema feature bijection check", False, str(e))

try:
    version = get_feature_contract_version()
    assert version == "1.0.0", f"Unexpected version: {version}"
    _report(f"Feature contract version = '{version}'", True)
except Exception as e:
    _report("Feature contract version check", False, str(e))

try:
    meta = get_feature_metadata()
    for fname in CANONICAL_FEATURE_ORDER:
        assert fname in meta, f"Feature '{fname}' missing from metadata"
        assert "unit" in meta[fname], f"Feature '{fname}' missing 'unit'"
        assert "minimum" in meta[fname], f"Feature '{fname}' missing 'minimum'"
        assert "maximum" in meta[fname], f"Feature '{fname}' missing 'maximum'"
    _report("All 25 features have unit, minimum, maximum metadata", True)
except Exception as e:
    _report("Feature metadata completeness check", False, str(e))


# ============================================================
# Section 8: Data Quality Assessment
# ============================================================
print("\n── Section 8: Data Quality Assessment ──")

try:
    full_dict = {name: 1.0 for name in CANONICAL_FEATURE_ORDER}
    full_dict.update({"rainfall_mm_h": 20.0, "traffic_level": 5.0})
    q = assess_data_quality(full_dict)
    assert q == "HIGH", f"Expected HIGH, got {q}"
    _report("Data quality HIGH when all 25 features provided", True)
except Exception as e:
    _report("Data quality HIGH assessment", False, str(e))

try:
    sparse_dict = {"rainfall_mm_h": 20.0, "traffic_level": 5.0}
    q = assess_data_quality(sparse_dict)
    assert q == "DEGRADED", f"Expected DEGRADED, got {q}"
    _report("Data quality DEGRADED when only 2/25 features provided", True)
except Exception as e:
    _report("Data quality DEGRADED assessment", False, str(e))

try:
    partial = {name: 1.0 for name in CANONICAL_FEATURE_ORDER[:12]}
    q = assess_data_quality(partial)
    assert q == "MODERATE", f"Expected MODERATE, got {q}"
    _report("Data quality MODERATE when 12/25 features provided", True)
except Exception as e:
    _report("Data quality MODERATE assessment", False, str(e))


# ============================================================
# Section 9: Baseline Archive Integrity
# ============================================================
print("\n── Section 9: Baseline Archive Integrity ──")

_EXPECTED_HASHES = {
    "road_model.pkl": "FA2658F878B5D2B802CAFF01E84C9FE5BB093C07096E5544805CF347AD39B3A8",
    "train_xgboost.py": "0C67B67475925ED4F540D8687F0BB13EA1678181380D08905E65C8C50C516135",
    "audit_xgboost.py": "5D5393792D09B671B3298D003AB3E7817061ECAA7F0020EA2E630E337EB7AFCE",
}

for filename, expected_hash in _EXPECTED_HASHES.items():
    candidates = [
        os.path.abspath(os.path.join("models", "baselines", "xgboost_synthetic", filename)),
        os.path.abspath(os.path.join("..", "models", "baselines", "xgboost_synthetic", filename)),
    ]
    path = next((c for c in candidates if os.path.exists(c)), None)
    try:
        assert path is not None, f"Baseline file not found: {filename}"
        with open(path, "rb") as bfh:
            actual_hash = hashlib.sha256(bfh.read()).hexdigest().upper()
        assert actual_hash == expected_hash.upper(), f"SHA256 mismatch: expected {expected_hash}, got {actual_hash}"
        _report(f"Baseline integrity: {filename}", True, f"SHA256 verified")
    except Exception as e:
        _report(f"Baseline integrity: {filename}", False, str(e))


# ============================================================
# Section 10: Existing RoadPredictionInput Backward Compatibility
# ============================================================
print("\n── Section 10: Backward Compatibility — RoadPredictionInput ──")

try:
    orig = RoadPredictionInput(rainfall=50.0, traffic=7.0, waterLevel=25.0)
    assert orig.rainfall == 50.0
    assert orig.traffic == 7.0
    assert orig.waterLevel == 25.0
    _report("Existing RoadPredictionInput (rainfall, traffic, waterLevel) unchanged", True)
except Exception as e:
    _report("Existing RoadPredictionInput unchanged", False, str(e))

try:
    RoadPredictionInput(rainfall=-1.0, traffic=7.0, waterLevel=25.0)
    _report("RoadPredictionInput still rejects negative rainfall", False, "Expected error")
except ValidationError:
    _report("RoadPredictionInput still rejects negative rainfall", True)

try:
    RoadPredictionInput(rainfall=50.0, traffic=0.5, waterLevel=25.0)
    _report("RoadPredictionInput still rejects traffic < 1", False, "Expected error")
except ValidationError:
    _report("RoadPredictionInput still rejects traffic < 1", True)


# ============================================================
# Final Summary
# ============================================================
total = _RESULTS["passed"] + _RESULTS["failed"]
print(f"\n══════════════════════════════════════════════════════════")
print(f"  ADAS Phase 1 Tests: {_RESULTS['passed']}/{total} passed, {_RESULTS['failed']} failed")
print(f"══════════════════════════════════════════════════════════")

if _RESULTS["failed"] > 0:
    sys.exit(1)
