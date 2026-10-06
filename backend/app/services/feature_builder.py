"""
Canonical Road-Risk Feature Builder
Single source of truth bridge converting validated RoadRiskFeatures schemas
into ordered, canonical feature vectors strictly governed by config/road_risk_features.json.
"""

import os
import json
from typing import Dict, Any, List, Union, Optional
import numpy as np

# Locate configuration file relative to this module or project root
_POSSIBLE_CONFIG_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "road_risk_features.json")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "road_risk_features.json")),
    os.path.abspath(os.path.join("config", "road_risk_features.json")),
    os.path.abspath(os.path.join("..", "config", "road_risk_features.json")),
]

_CONTRACT_DATA: Optional[Dict[str, Any]] = None
_CONFIG_FILE_PATH: Optional[str] = None

for path in _POSSIBLE_CONFIG_PATHS:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _CONTRACT_DATA = json.load(f)
            _CONFIG_FILE_PATH = path
            break

if _CONTRACT_DATA is None:
    raise RuntimeError(
        f"Road-Risk Feature Contract config file not found. Checked: {_POSSIBLE_CONFIG_PATHS}"
    )

CANONICAL_FEATURE_ORDER: List[str] = list(_CONTRACT_DATA["canonical_feature_order"])
FEATURE_METADATA_MAP: Dict[str, Dict[str, Any]] = {
    f["name"]: f for f in _CONTRACT_DATA["features"]
}

# Documented deterministic fallback imputations for optional features
# when telemetry or camera feeds are not yet providing them
DEFAULT_FEATURE_IMPUTATIONS: Dict[str, Any] = {
    "rainfall_10min_mm": lambda d: round(d.get("rainfall_mm_h", 0.0) / 6.0, 2),
    "rainfall_1h_mm": lambda d: round(float(d.get("rainfall_mm_h", 0.0)), 2),
    "visibility_m": 10000.0,
    "temperature_c": 25.0,
    "wind_speed_kmh": 10.0,
    "vehicle_density": lambda d: round(float(d.get("traffic_level", 1.0)) * 10.0, 1),
    "congestion_change": 0.0,
    "vehicle_speed_kmh": 40.0,
    "acceleration_mps2": 0.0,
    "braking_intensity": 0.0,
    "road_slope_pct": 0.0,
    "elevation_m": 500.0,
    "road_type": 0,
    "vehicle_count": 0,
    "person_count": 0,
    "fire_detected": 0,
    "smoke_detected": 0,
    "flood_detected": 0,
    "obstacle_count": 0,
    "hazard_count": 0,
    "hazard_distance_m": 500.0,
    "flood_report": 0,
    "road_closure_report": 0,
}


def get_canonical_feature_order() -> List[str]:
    """Returns the ordered list of canonical feature names as defined in road_risk_features.json."""
    return list(CANONICAL_FEATURE_ORDER)


def get_feature_contract_version() -> str:
    """Returns the version of the active feature contract."""
    return _CONTRACT_DATA.get("version", "1.0.0")


def get_feature_metadata() -> Dict[str, Dict[str, Any]]:
    """Returns dictionary mapping feature name to its full metadata."""
    return dict(FEATURE_METADATA_MAP)


def assess_data_quality(raw_dict: Dict[str, Any]) -> str:
    """
    Computes data quality tier based on percentage of non-null features supplied.
    HIGH: >= 75% provided
    MODERATE: >= 40% provided
    DEGRADED: < 40% provided
    """
    total = len(CANONICAL_FEATURE_ORDER)
    supplied = sum(1 for k in CANONICAL_FEATURE_ORDER if raw_dict.get(k) is not None)
    ratio = supplied / total
    if ratio >= 0.75:
        return "HIGH"
    elif ratio >= 0.40:
        return "MODERATE"
    return "DEGRADED"


def build_canonical_feature_dict(
    features: Union[Dict[str, Any], Any]
) -> Dict[str, float]:
    """
    Transforms a RoadRiskFeatures instance or raw dictionary into a complete canonical
    feature dictionary with all 25 features present, applying documented default imputations
    for optional fields that are None.
    """
    # Extract dict representation
    if hasattr(features, "model_dump"):  # Pydantic v2
        raw = features.model_dump()
    elif hasattr(features, "dict"):       # Pydantic v1 fallback
        raw = features.dict()
    elif isinstance(features, dict):
        raw = dict(features)
    else:
        raise TypeError(f"Expected RoadRiskFeatures or dict, got {type(features)}")

    canonical_dict: Dict[str, float] = {}

    # First pass: copy available features
    for name in CANONICAL_FEATURE_ORDER:
        val = raw.get(name)
        if val is not None:
            canonical_dict[name] = float(val)

    # Second pass: apply deterministic imputations for missing optional features
    for name in CANONICAL_FEATURE_ORDER:
        if name not in canonical_dict:
            imputer = DEFAULT_FEATURE_IMPUTATIONS.get(name, 0.0)
            if callable(imputer):
                canonical_dict[name] = float(imputer(canonical_dict))
            else:
                canonical_dict[name] = float(imputer)

    return canonical_dict


def build_canonical_feature_vector(
    features: Union[Dict[str, Any], Any],
    as_2d: bool = True
) -> np.ndarray:
    """
    Assembles the canonical feature vector in the EXACT order defined by road_risk_features.json.
    Returns:
        np.ndarray of shape (1, 25) if as_2d=True else (25,) of dtype float64.
    """
    canonical_dict = build_canonical_feature_dict(features)
    vector = np.array([canonical_dict[name] for name in CANONICAL_FEATURE_ORDER], dtype=np.float64)

    if np.isnan(vector).any() or np.isinf(vector).any():
        raise ValueError("Canonical feature vector contains NaN or infinite values after construction.")

    return vector.reshape(1, -1) if as_2d else vector
