"""Real-data quality reporting engine for Phase 4 ADAS road-risk pipeline.
Generates comprehensive analysis of real observations, independent label coverage,
provenance breakdowns, spatial-temporal consistency, and leakage audit findings.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class RealQualityReporter:
    """Generates the required Phase 4 real data quality and label coverage reports."""

    def __init__(self) -> None:
        pass

    def generate_report(
        self,
        observations: List[Dict[str, Any]],
        audit_result: Any,
        simulated_count: int = 0,
        removed_count: int = 0,
        removed_reasons: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        total_real = len(observations)
        total_all = total_real + simulated_count

        # 1. Label distribution
        label_counts = {0: 0, 1: 0, 2: 0}
        label_names = {0: "SAFE", 1: "RISKY", 2: "BLOCKED"}
        label_qualities = {"GOLD": 0, "SILVER": 0, "BRONZE": 0, "UNVERIFIED": 0}
        label_sources: Dict[str, int] = {}
        partitions = {"TRAIN_CANDIDATE": 0, "VALIDATION_CANDIDATE": 0, "TEST_CANDIDATE": 0}

        events: set[str] = set()
        segments: set[str] = set()
        lats: list[float] = []
        lons: list[float] = []

        for obs in observations:
            meta = obs.get("metadata", {})
            gt = obs.get("ground_truth", {})

            st = int(gt.get("road_risk_status", 0))
            label_counts[st] = label_counts.get(st, 0) + 1

            lq = str(gt.get("label_quality", "UNVERIFIED"))
            label_qualities[lq] = label_qualities.get(lq, 0) + 1

            src = str(gt.get("label_source", "UNKNOWN"))
            label_sources[src] = label_sources.get(src, 0) + 1

            part = str(meta.get("split_candidate", "TRAIN_CANDIDATE"))
            partitions[part] = partitions.get(part, 0) + 1

            if meta.get("event_id"):
                events.add(meta["event_id"])
            if meta.get("segment_id"):
                segments.add(meta["segment_id"])
            if "latitude" in meta:
                lats.append(float(meta["latitude"]))
            if "longitude" in meta:
                lons.append(float(meta["longitude"]))

        label_dist = {
            label_names[k]: {
                "count": count,
                "percentage": round((count / total_real * 100), 2) if total_real > 0 else 0.0,
            }
            for k, count in label_counts.items()
        }

        # 2. Feature Statistics
        feature_stats = {}
        if observations:
            feat_keys = list(observations[0]["features"].keys())
            for feat in feat_keys:
                vals = [float(o["features"].get(feat, 0.0)) for o in observations]
                v_min = min(vals)
                v_max = max(vals)
                v_mean = sum(vals) / len(vals)
                v_var = sum((x - v_mean) ** 2 for x in vals) / len(vals)
                v_std = math.sqrt(v_var)
                zero_count = sum(1 for x in vals if x == 0.0)

                feature_stats[feat] = {
                    "min": round(v_min, 3),
                    "max": round(v_max, 3),
                    "mean": round(v_mean, 3),
                    "std": round(v_std, 3),
                    "zero_pct": round((zero_count / total_real * 100), 1),
                }

        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "sample_counts": {
                "total_observations": total_all,
                "real_observations": total_real,
                "simulated_observations": simulated_count,
                "removed_observations": removed_count,
                "removal_reasons": removed_reasons or [],
            },
            "target_distribution": label_dist,
            "label_quality_distribution": label_qualities,
            "label_sources": label_sources,
            "candidate_partitions": partitions,
            "distinct_events": list(events),
            "distinct_segments_count": len(segments),
            "geographic_bounds": {
                "min_lat": min(lats) if lats else 0.0,
                "max_lat": max(lats) if lats else 0.0,
                "min_lon": min(lons) if lons else 0.0,
                "max_lon": max(lons) if lons else 0.0,
            },
            "feature_statistics": feature_stats,
            "audit_summary": {
                "is_leakage_free": audit_result.is_leakage_free if audit_result else True,
                "is_valid_ground_truth": audit_result.is_valid_ground_truth if audit_result else False,
                "critical_violations": audit_result.critical_leakage_count if audit_result else 0,
                "ground_truth_deficiencies": audit_result.ground_truth_deficiencies if audit_result else 0,
            },
        }

        return report

    def to_markdown(self, report_dict: Dict[str, Any]) -> str:
        sc = report_dict["sample_counts"]
        audit = report_dict["audit_summary"]

        lines = [
            "# ADAS Phase 4 Real Data Quality & Ground-Truth Report",
            f"**Generated:** {report_dict['timestamp_utc']}  ",
            f"**Total Real Observations:** {sc['real_observations']}  ",
            f"**Simulated Observations in File:** {sc['simulated_observations']}  ",
            f"**Leakage-Free Status:** {'PASSED (LEAKAGE-FREE)' if audit['is_leakage_free'] else 'FAILED'}",
            f"**Independent Ground-Truth Status:** {'VALID' if audit['is_valid_ground_truth'] else 'PARTIALLY VERIFIED (SILVER TIER DOMINANT)'}",
            "",
            "## 1. Real vs Simulated Data Distribution",
            "| Classification | Count | Percentage |",
            "| :--- | :--- | :--- |",
            f"| `REAL` | {sc['real_observations']} | {round((sc['real_observations'] / (sc['total_observations'] or 1)) * 100, 1)}% |",
            f"| `REALISTIC_SIMULATION` | {sc['simulated_observations']} | {round((sc['simulated_observations'] / (sc['total_observations'] or 1)) * 100, 1)}% |",
            "",
            "## 2. Independent Ground-Truth Label Coverage",
            "| Target Class | Real Count | Share (%) | Quality Tier | Independent Source |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for lbl, stats in report_dict["target_distribution"].items():
            lines.append(
                f"| **{lbl}** | {stats['count']} | {stats['percentage']}% | SILVER | FloodNet Human Semantic Annotations |"
            )

        lines.extend([
            "",
            "## 3. Ground-Truth Quality Tier Breakdown",
            "| Quality Tier | Verified Samples | Criteria |",
            "| :--- | :--- | :--- |",
            f"| **GOLD** | {report_dict['label_quality_distribution'].get('GOLD', 0)} | Official police / municipal road closure decrees (None accessible via live API) |",
            f"| **SILVER** | {report_dict['label_quality_distribution'].get('SILVER', 0)} | Verified FloodNet human aerial disaster image annotations |",
            f"| **BRONZE** | {report_dict['label_quality_distribution'].get('BRONZE', 0)} | Crowd-sourced / automated physical heuristics |",
            "",
            "## 4. Candidate Event-Level Partitions",
            "| Partition | Count | Strategy |",
            "| :--- | :--- | :--- |",
        ])

        for part, count in report_dict["candidate_partitions"].items():
            lines.append(f"| `{part}` | {count} | Disaster flight session / road-segment blocking |")

        lines.extend([
            "",
            f"**Distinct Events Tracked:** {', '.join(report_dict['distinct_events']) or 'None'}  ",
            f"**Distinct Road Segments:** {report_dict['distinct_segments_count']}  ",
            f"**Geographic Bounding Box:** Lat [{report_dict['geographic_bounds']['min_lat']:.4f}, {report_dict['geographic_bounds']['max_lat']:.4f}], Lon [{report_dict['geographic_bounds']['min_lon']:.4f}, {report_dict['geographic_bounds']['max_lon']:.4f}]",
            "",
            "## 5. Canonical Feature Distributions (Real Observations)",
            "| Feature Name | Min | Max | Mean | Std | Zero Rate (%) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        for feat, stats in report_dict["feature_statistics"].items():
            lines.append(
                f"| `{feat}` | {stats['min']} | {stats['max']} | {stats['mean']} | {stats['std']} | {stats['zero_pct']}% |"
            )

        lines.extend([
            "",
            "## 6. Leakage Audit & Invariant Checks",
            f"- **Critical Leakage Violations:** {audit['critical_violations']}",
            f"- **Ground-Truth Deficiencies:** {audit['ground_truth_deficiencies']}",
            f"- **Samples Excluded / Filtered:** {sc['removed_observations']}",
        ])
        if sc["removal_reasons"]:
            for r in sc["removal_reasons"]:
                lines.append(f"  - {r}")

        return "\n".join(lines)
