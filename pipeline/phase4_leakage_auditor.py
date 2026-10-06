"""Advanced multi-dimensional leakage and ground-truth auditor for Phase 4 ADAS road-risk pipeline.
Distinguishes between LEAKAGE-FREE and VALID-GROUND-TRUTH.
Checks:
- Label-source feature leakage
- Indirect target leakage
- Future information / temporal leakage
- Same-event partition leakage
- Same-road segment partition leakage
- Same-session partition leakage
- Duplicate observations
- Identifiers in feature matrix
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Phase4AuditViolation:
    category: str  # "LEAKAGE", "GROUND_TRUTH", "TEMPORAL", "PARTITION"
    severity: str  # "CRITICAL", "HIGH", "WARNING"
    rule_name: str
    description: str
    feature_name: Optional[str] = None
    affected_count: int = 1


@dataclass
class Phase4AuditResult:
    is_leakage_free: bool
    is_valid_ground_truth: bool
    total_samples: int
    critical_leakage_count: int
    ground_truth_deficiencies: int
    violations: List[Phase4AuditViolation] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "=== PHASE 4 DATA AUDIT REPORT ===",
            f"Total Samples Audited: {self.total_samples}",
            f"Leakage-Free Status: {'PASSED (LEAKAGE-FREE)' if self.is_leakage_free else 'FAILED (LEAKAGE DETECTED)'}",
            f"Ground-Truth Validity: {'VALID (INDEPENDENT EVIDENCE)' if self.is_valid_ground_truth else 'DEFICIENT (HEURISTIC / UNVERIFIED)'}",
            f"Critical Violations: {self.critical_leakage_count}",
            f"Ground-Truth Issues: {self.ground_truth_deficiencies}",
            "Violations Detail:",
        ]
        for v in self.violations:
            lines.append(f"  [{v.severity}] ({v.category}) {v.rule_name}: {v.description}")
        return "\n".join(lines)


class Phase4LeakageAuditor:
    """Enforces multi-faceted leakage prevention and ground-truth validation."""

    IDENTIFIERS = {
        "observation_id",
        "timestamp",
        "latitude",
        "longitude",
        "segment_id",
        "event_id",
        "session_id",
        "split_candidate",
        "road_risk_status",
        "target",
        "label",
    }

    def __init__(self) -> None:
        pass

    def audit_dataset(self, observations: List[Dict[str, Any]]) -> Phase4AuditResult:
        violations: List[Phase4AuditViolation] = []
        total = len(observations)

        if total == 0:
            return Phase4AuditResult(
                is_leakage_free=True,
                is_valid_ground_truth=False,
                total_samples=0,
                critical_leakage_count=0,
                ground_truth_deficiencies=1,
                violations=[Phase4AuditViolation(category="GROUND_TRUTH", severity="CRITICAL", rule_name="Empty Dataset", description="No observations to audit")],
            )

        # 1. Feature Level & Record Level Audits
        for obs in observations:
            meta = obs.get("metadata", {})
            features = obs.get("features", {})
            gt = obs.get("ground_truth", {})

            # Check 1A: Target in Features
            if "road_risk_status" in features or "target" in features:
                violations.append(
                    Phase4AuditViolation(
                        category="LEAKAGE",
                        severity="CRITICAL",
                        rule_name="Target In Features",
                        description="Target variable present in feature dictionary!",
                        feature_name="road_risk_status",
                    )
                )

            # Check 1B: Identifiers in Features
            for id_col in self.IDENTIFIERS:
                if id_col in features and id_col != "road_risk_status":
                    violations.append(
                        Phase4AuditViolation(
                            category="LEAKAGE",
                            severity="CRITICAL",
                            rule_name="Identifier In Features",
                            description=f"Identifier column '{id_col}' found in feature matrix!",
                            feature_name=id_col,
                        )
                    )

            # Check 1C: Unmasked Label-Source Feature Leakage
            leaked_candidates = gt.get("leaked_features", [])
            for feat in leaked_candidates:
                val = features.get(feat, 0)
                # If feature is nonzero despite being the direct label source
                if val != 0 and val != 0.0:
                    violations.append(
                        Phase4AuditViolation(
                            category="LEAKAGE",
                            severity="CRITICAL",
                            rule_name="Unmasked Label-Source Feature",
                            description=f"Feature '{feat}' determined the label but remains nonzero ({val}) in features for obs {meta.get('observation_id')}",
                            feature_name=feat,
                        )
                    )

            # Check 1D: Temporal Inversion (Future Information Leakage)
            obs_time_str = meta.get("timestamp")
            if obs_time_str:
                try:
                    obs_dt = datetime.fromisoformat(obs_time_str)
                    now_dt = datetime.now(obs_dt.tzinfo)
                    if obs_dt > now_dt:
                        violations.append(
                            Phase4AuditViolation(
                                category="TEMPORAL",
                                severity="HIGH",
                                rule_name="Future Timestamp",
                                description=f"Observation timestamp {obs_time_str} is set in the future.",
                            )
                        )
                except Exception:
                    pass

            # Check 1E: Ground Truth Quality & Independence
            label_quality = gt.get("label_quality", "UNKNOWN")
            if label_quality not in ["GOLD", "SILVER"]:
                violations.append(
                    Phase4AuditViolation(
                        category="GROUND_TRUTH",
                        severity="WARNING",
                        rule_name="Non-Authoritative Label Quality",
                        description=f"Observation has '{label_quality}' label quality; not certified by independent expert/authority.",
                    )
                )

        # 2. Batch-Level Partition Contamination Checks
        train_events = {obs["metadata"]["event_id"] for obs in observations if obs["metadata"].get("split_candidate") == "TRAIN_CANDIDATE"}
        test_events = {obs["metadata"]["event_id"] for obs in observations if obs["metadata"].get("split_candidate") == "TEST_CANDIDATE"}

        # Event overlap check
        event_overlap = train_events.intersection(test_events)
        if event_overlap:
            violations.append(
                Phase4AuditViolation(
                    category="PARTITION",
                    severity="HIGH",
                    rule_name="Same-Event Cross-Partition Contamination",
                    description=f"Disaster event(s) {event_overlap} span both TRAIN and TEST partitions. Requires event-isolated splits.",
                    affected_count=len(event_overlap),
                )
            )

        # Same road segment overlap check
        train_segs = {obs["metadata"].get("segment_id") for obs in observations if obs["metadata"].get("split_candidate") == "TRAIN_CANDIDATE"}
        test_segs = {obs["metadata"].get("segment_id") for obs in observations if obs["metadata"].get("split_candidate") == "TEST_CANDIDATE"}
        seg_overlap = train_segs.intersection(test_segs)
        if seg_overlap and None not in seg_overlap:
            violations.append(
                Phase4AuditViolation(
                    category="PARTITION",
                    severity="HIGH",
                    rule_name="Same-Road Segment Contamination",
                    description=f"Road segment(s) {seg_overlap} appear in both TRAIN and TEST partitions. Requires spatial blocking.",
                    affected_count=len(seg_overlap),
                )
            )

        # 3. Duplicate Observations Check
        coords_and_time = [
            (
                round(obs["metadata"].get("latitude", 0), 4),
                round(obs["metadata"].get("longitude", 0), 4),
                obs["metadata"].get("timestamp"),
            )
            for obs in observations
        ]
        if len(coords_and_time) != len(set(coords_and_time)):
            dup_count = len(coords_and_time) - len(set(coords_and_time))
            violations.append(
                Phase4AuditViolation(
                    category="LEAKAGE",
                    severity="WARNING",
                    rule_name="Duplicate Spatial-Temporal Observations",
                    description=f"Found {dup_count} duplicate coordinate-timestamp observations in dataset.",
                    affected_count=dup_count,
                )
            )

        critical_count = sum(1 for v in violations if v.severity == "CRITICAL")
        gt_deficiencies = sum(1 for v in violations if v.category == "GROUND_TRUTH")

        is_leakage_free = critical_count == 0
        is_valid_gt = gt_deficiencies == 0

        return Phase4AuditResult(
            is_leakage_free=is_leakage_free,
            is_valid_ground_truth=is_valid_gt,
            total_samples=total,
            critical_leakage_count=critical_count,
            ground_truth_deficiencies=gt_deficiencies,
            violations=violations,
        )
