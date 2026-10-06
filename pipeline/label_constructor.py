"""Ground-truth label constructor for ADAS road-risk pipeline.
Implements the tripartite operational definition (SAFE=0, RISKY=1, BLOCKED=2)
defined in docs/road_risk_label_definition.md.
Explicitly tracks label provenance and leakage candidate features.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LabelAssignment:
    road_risk_status: int  # 0=SAFE, 1=RISKY, 2=BLOCKED
    label_name: str        # "SAFE", "RISKY", "BLOCKED"
    label_source: str      # e.g., "MUNICIPAL_DISASTER_LOG", "PHYSICAL_GROUND_TRUTH"
    label_timestamp: str   # ISO-8601 UTC
    label_location: str    # "lat,lon" or segment ID
    label_reason: str      # Textual justification
    leaked_features: List[str]  # Features used to determine label (must be masked or checked by auditor)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "road_risk_status": self.road_risk_status,
            "label_name": self.label_name,
            "label_source": self.label_source,
            "label_timestamp": self.label_timestamp,
            "label_location": self.label_location,
            "label_reason": self.label_reason,
            "leaked_features": self.leaked_features,
        }


class LabelConstructor:
    """Assigns ground truth road-risk labels based on independent physical & municipal criteria."""

    def __init__(self, default_authority: str = "INDEPENDENT_GROUND_TRUTH_ENGINE") -> None:
        self.default_authority = default_authority

    def assign_label(
        self,
        observation: Dict[str, Any],
        external_ground_truth: Optional[Dict[str, Any]] = None,
    ) -> LabelAssignment:
        metadata = observation.get("metadata", {})
        features = observation.get("features", {})
        lat = metadata.get("latitude", 0.0)
        lon = metadata.get("longitude", 0.0)
        location_str = f"{lat:.4f},{lon:.4f}"
        now_utc = metadata.get("timestamp") or datetime.now(timezone.utc).isoformat()

        # Priority 1: External authoritative ground truth if provided
        if external_ground_truth:
            status = external_ground_truth.get("status")
            reason = external_ground_truth.get("reason", "Verified external report")
            source = external_ground_truth.get("source", "EXTERNAL_AUTHORITY")
            leaked = external_ground_truth.get("used_fields", [])
            status_int = {"SAFE": 0, "RISKY": 1, "BLOCKED": 2}.get(status, 0)
            return LabelAssignment(
                road_risk_status=status_int,
                label_name=status,
                label_source=source,
                label_timestamp=now_utc,
                label_location=location_str,
                label_reason=reason,
                leaked_features=leaked,
            )

        # Priority 2: Physical / Environmental Ground Truth Logic
        # Check BLOCKED conditions
        is_blocked, blocked_reason, blocked_leaked = self._evaluate_blocked(features)
        if is_blocked:
            return LabelAssignment(
                road_risk_status=2,
                label_name="BLOCKED",
                label_source=self.default_authority,
                label_timestamp=now_utc,
                label_location=location_str,
                label_reason=blocked_reason,
                leaked_features=blocked_leaked,
            )

        # Check RISKY conditions
        is_risky, risky_reason, risky_leaked = self._evaluate_risky(features)
        if is_risky:
            return LabelAssignment(
                road_risk_status=1,
                label_name="RISKY",
                label_source=self.default_authority,
                label_timestamp=now_utc,
                label_location=location_str,
                label_reason=risky_reason,
                leaked_features=risky_leaked,
            )

        # Default to SAFE
        return LabelAssignment(
            road_risk_status=0,
            label_name="SAFE",
            label_source=self.default_authority,
            label_timestamp=now_utc,
            label_location=location_str,
            label_reason="Normal operating conditions, no physical impediment or hazard detected",
            leaked_features=[],
        )

    def _evaluate_blocked(self, features: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        leaked = []

        # Criterion B1: Active official road closure
        if features.get("road_closure_report", 0) == 1:
            leaked.append("road_closure_report")
            return True, "Official municipal road closure report active", leaked

        # Criterion B2: Complete physical obstruction or major hazard
        obstructions = []
        if features.get("fire_detected", 0) == 1:
            obstructions.append("fire_detected")
        if features.get("obstacle_count", 0) >= 2:
            obstructions.append("obstacle_count")

        if obstructions:
            return True, f"Severe physical obstruction detected: {', '.join(obstructions)}", obstructions

        # Criterion B3: Extreme inundation (flash flood with water hazard)
        if features.get("flood_detected", 0) == 1 and features.get("rainfall_mm_h", 0) > 40.0:
            return True, "Submerged roadway with flash flood conditions (>40mm/h)", ["flood_detected", "rainfall_mm_h"]

        return False, "", []

    def _evaluate_risky(self, features: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        leaked = []

        # Criterion R1: Active flood report in area
        if features.get("flood_report", 0) == 1:
            leaked.append("flood_report")
            return True, "Active flood advisory reported in vicinity", leaked

        # Criterion R2: High rainfall, reduced visibility, or gale winds
        rain = features.get("rainfall_mm_h", 0.0)
        vis = features.get("visibility_m", 10000.0)
        wind = features.get("wind_speed_kmh", 0.0)

        if rain > 20.0 or vis < 500.0 or wind > 60.0:
            reasons = []
            if rain > 20.0:
                reasons.append(f"heavy rain ({rain} mm/h)")
                leaked.append("rainfall_mm_h")
            if vis < 500.0:
                reasons.append(f"low visibility ({vis} m)")
                leaked.append("visibility_m")
            if wind > 60.0:
                reasons.append(f"high winds ({wind} km/h)")
                leaked.append("wind_speed_kmh")
            return True, f"Adverse weather conditions: {', '.join(reasons)}", leaked

        # Criterion R3: Visual hazard detected or emergency braking
        if features.get("flood_detected", 0) == 1:
            return True, "Surface water / flood detected on roadway", ["flood_detected"]
        if features.get("obstacle_count", 0) == 1:
            return True, "Road obstacle detected in travel lane", ["obstacle_count"]
        if features.get("braking_intensity", 0.0) > 0.6:
            return True, "Severe vehicle braking event observed", ["braking_intensity"]

        # Criterion R4: Gridlock combined with adverse conditions
        if features.get("traffic_level", 1.0) >= 7.0 and rain > 10.0:
            return True, "Severe traffic congestion in rainy conditions", ["traffic_level", "rainfall_mm_h"]

        return False, "", []
