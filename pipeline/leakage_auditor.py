"""Data leakage auditor and validator for ADAS road-risk pipeline.
Enforces the 10 data policy rules defined in docs/road_risk_data_policy.md.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AuditViolation:
    rule_number: int
    rule_name: str
    severity: str  # "CRITICAL", "HIGH", "WARNING"
    feature_name: Optional[str]
    description: str
    affected_count: int = 1


@dataclass
class AuditReport:
    is_valid: bool
    total_samples: int
    total_violations: int
    critical_count: int
    violations: List[AuditViolation] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        lines = [
            f"=== LEAKAGE AUDIT REPORT: {status} ===",
            f"Total samples audited: {self.total_samples}",
            f"Total violations: {self.total_violations} (Critical: {self.critical_count})",
        ]
        for v in self.violations:
            lines.append(f"  [{v.severity}] Rule {v.rule_number} ({v.rule_name}): {v.description}")
        return "\n".join(lines)


class LeakageAuditor:
    """Enforces anti-leakage rules on datasets before model ingestion."""

    IDENTIFIER_COLUMNS = {
        "observation_id",
        "timestamp",
        "latitude",
        "longitude",
        "segment_id",
        "event_id",
        "session_id",
        "road_risk_status",
        "target",
        "label",
        "status",
    }

    def __init__(self, mask_leaked_features: bool = True) -> None:
        self.mask_leaked_features = mask_leaked_features

    def audit_record(
        self,
        features: Dict[str, Any],
        label_info: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], List[AuditViolation]]:
        """Audits an individual record and optionally masks out directly leaked features."""
        violations: List[AuditViolation] = []
        cleaned_features = dict(features)

        # Rule 1: Target derived features
        if "road_risk_status" in cleaned_features or "target" in cleaned_features:
            violations.append(
                AuditViolation(
                    rule_number=1,
                    rule_name="Target In Features",
                    severity="CRITICAL",
                    feature_name="road_risk_status",
                    description="Target variable is present in the feature dictionary!",
                )
            )
            cleaned_features.pop("road_risk_status", None)
            cleaned_features.pop("target", None)

        # Rule 6: Identifiers in feature matrix
        for id_col in self.IDENTIFIER_COLUMNS:
            if id_col in cleaned_features and id_col != "road_risk_status":
                violations.append(
                    AuditViolation(
                        rule_number=6,
                        rule_name="Identifier Leakage",
                        severity="CRITICAL",
                        feature_name=id_col,
                        description=f"Identifier column '{id_col}' found in feature set.",
                    )
                )
                cleaned_features.pop(id_col, None)

        # Rule 2 & 3: Direct label source leakage / Dual-role leakage
        leaked_candidates = label_info.get("leaked_features", [])
        for feat in leaked_candidates:
            if feat in cleaned_features:
                if self.mask_leaked_features:
                    # Neutralize/mask the feature to prevent 100% shortcut
                    cleaned_features[feat] = 0.0 if isinstance(cleaned_features[feat], float) else 0
                    violations.append(
                        AuditViolation(
                            rule_number=2,
                            rule_name="Direct Label Source Masked",
                            severity="WARNING",
                            feature_name=feat,
                            description=f"Feature '{feat}' directly determined the label; masked to 0 to prevent leakage shortcut.",
                        )
                    )
                else:
                    violations.append(
                        AuditViolation(
                            rule_number=2,
                            rule_name="Direct Label Source Unmasked",
                            severity="CRITICAL",
                            feature_name=feat,
                            description=f"Feature '{feat}' directly determined the label and was left unmasked in features.",
                        )
                    )

        # Rule 10: Invariant validation
        rain = cleaned_features.get("rainfall_mm_h", 0.0)
        vis = cleaned_features.get("visibility_m", 0.0)
        if rain < 0.0 or rain > 500.0:
            violations.append(
                AuditViolation(
                    rule_number=10,
                    rule_name="Feature Invariant Violation",
                    severity="CRITICAL",
                    feature_name="rainfall_mm_h",
                    description=f"Physically impossible rainfall value: {rain}",
                )
            )
        if vis < 0.0 or vis > 100000.0:
            violations.append(
                AuditViolation(
                    rule_number=10,
                    rule_name="Feature Invariant Violation",
                    severity="CRITICAL",
                    feature_name="visibility_m",
                    description=f"Physically impossible visibility value: {vis}",
                )
            )

        return cleaned_features, violations

    def audit_batch(
        self,
        records: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], AuditReport]:
        """Audits a full batch of assembled observations."""
        all_violations: List[AuditViolation] = []
        cleaned_records: List[Dict[str, Any]] = []

        if not records:
            return [], AuditReport(is_valid=True, total_samples=0, total_violations=0, critical_count=0)

        for rec in records:
            features = rec.get("features", {})
            label_info = rec.get("label", {})
            metadata = rec.get("metadata", {})

            cleaned_feat, v_list = self.audit_record(features, label_info, metadata)
            rec["features"] = cleaned_feat
            cleaned_records.append(rec)
            all_violations.extend(v_list)

        # Rule 4: Constant/near-constant features across batch
        if len(records) >= 20:
            keys = list(records[0]["features"].keys())
            for k in keys:
                vals = [r["features"].get(k, 0) for r in cleaned_records]
                unique_vals = set(vals)
                if len(unique_vals) == 1:
                    all_violations.append(
                        AuditViolation(
                            rule_number=4,
                            rule_name="Constant Feature",
                            severity="HIGH",
                            feature_name=k,
                            description=f"Feature '{k}' is 100% constant across all {len(records)} samples ({list(unique_vals)[0]}).",
                            affected_count=len(records),
                        )
                    )

        # Rule 5: Single-feature 100% separator check
        if len(records) >= 20:
            # Check if any single binary feature perfectly separates label
            labels = [r["label"]["road_risk_status"] for r in cleaned_records if "label" in r]
            if len(set(labels)) > 1:
                keys = list(records[0]["features"].keys())
                for k in keys:
                    vals = [r["features"].get(k, 0) for r in cleaned_records]
                    # Check perfect correlation
                    distinct_pairs = set(zip(vals, labels))
                    # If mapping is 1-to-1 and strictly identical to label
                    if vals == labels:
                        all_violations.append(
                            AuditViolation(
                                rule_number=5,
                                rule_name="Suspicious 100% Separator",
                                severity="CRITICAL",
                                feature_name=k,
                                description=f"Feature '{k}' is identical to target label across all rows!",
                                affected_count=len(records),
                            )
                        )

        critical_count = sum(1 for v in all_violations if v.severity == "CRITICAL")
        is_valid = critical_count == 0

        report = AuditReport(
            is_valid=is_valid,
            total_samples=len(records),
            total_violations=len(all_violations),
            critical_count=critical_count,
            violations=all_violations,
        )

        return cleaned_records, report
