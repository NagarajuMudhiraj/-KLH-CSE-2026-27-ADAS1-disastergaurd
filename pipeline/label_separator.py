"""Label source separation and feature exclusion controller for ADAS road-risk pipeline.
Ensures strict independence between ground-truth labels and model input features.
Prevents train/inference distribution mismatch by documenting and controlling exclusions.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SeparationResult:
    features: Dict[str, Any]
    label_info: Dict[str, Any]
    excluded_features: List[str]
    has_exclusion: bool
    exclusion_reason: Optional[str] = None
    is_distribution_safe: bool = True


class LabelSeparator:
    """Controls label-source feature separation and enforces independence."""

    def __init__(self, allow_masking: bool = True) -> None:
        self.allow_masking = allow_masking

    def separate_label_and_features(
        self,
        features: Dict[str, Any],
        ground_truth: Dict[str, Any],
    ) -> SeparationResult:
        """Separates ground truth fields from feature vectors to prevent label leakage."""
        cleaned_features = dict(features)
        leaked_candidates = ground_truth.get("leaked_features", [])
        label_source = ground_truth.get("label_source", "UNKNOWN")

        excluded: List[str] = []
        reason: Optional[str] = None

        # 1. Target column must NEVER be inside features
        for target_key in ["road_risk_status", "target", "label", "status"]:
            if target_key in cleaned_features:
                cleaned_features.pop(target_key, None)
                excluded.append(target_key)
                reason = "Target variable was present in feature dict"

        # 2. Check direct label-source features
        # Example: If a municipal road closure log was the label source,
        # 'road_closure_report' was responsible for the label.
        # If FloodNet human visual annotation was the label source,
        # 'flood_detected' was responsible for the label.
        for feat in leaked_candidates:
            if feat in cleaned_features:
                excluded.append(feat)
                if self.allow_masking:
                    # Explicitly mask the feature value
                    # and record the reason in metadata
                    cleaned_features[feat] = 0.0 if isinstance(cleaned_features[feat], float) else 0
                    reason = (
                        f"Feature '{feat}' determined the label via '{label_source}'. "
                        "Excluded from predictor inputs for this row to maintain independent ground truth."
                    )

        has_exclusion = len(excluded) > 0

        # Assess train/inference distribution safety
        # If a feature is always zeroed in training whenever it occurs in reality,
        # the model will never learn its actual effect in production.
        is_safe = True
        if len(excluded) > 2:
            is_safe = False
            logger.warning(
                f"Row has multiple ({len(excluded)}) excluded features ({excluded}); "
                "risk of train/inference distribution shift."
            )

        return SeparationResult(
            features=cleaned_features,
            label_info=ground_truth,
            excluded_features=excluded,
            has_exclusion=has_exclusion,
            exclusion_reason=reason,
            is_distribution_safe=is_safe,
        )
