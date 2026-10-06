"""Data quality reporting engine for ADAS road-risk pipeline.
Analyzes processed observation batches and generates comprehensive markdown & json summaries.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class QualityReporter:
    """Computes quality metrics, class distributions, and feature statistics."""

    def __init__(self) -> None:
        pass

    def generate_report(
        self,
        records: List[Dict[str, Any]],
        audit_report: Optional[Any] = None,
    ) -> Dict[str, Any]:
        total = len(records)
        if total == 0:
            return {"status": "EMPTY", "total_records": 0}

        # 1. Label distribution
        label_counts = {0: 0, 1: 0, 2: 0}
        label_names = {0: "SAFE", 1: "RISKY", 2: "BLOCKED"}
        label_sources: Dict[str, int] = {}
        for r in records:
            lbl_info = r.get("label", {})
            st = lbl_info.get("road_risk_status", 0)
            label_counts[st] = label_counts.get(st, 0) + 1
            src = lbl_info.get("label_source", "UNKNOWN")
            label_sources[src] = label_sources.get(src, 0) + 1

        label_dist = {
            label_names[k]: {
                "count": count,
                "percentage": round((count / total) * 100, 2),
            }
            for k, count in label_counts.items()
        }

        # 2. Quality & Source provenance distribution
        quality_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        for r in records:
            meta = r.get("metadata", {})
            q = meta.get("data_quality", "UNKNOWN")
            quality_counts[q] = quality_counts.get(q, 0) + 1
            s = meta.get("source_classification", "UNKNOWN")
            source_counts[s] = source_counts.get(s, 0) + 1

        # 3. Feature statistics
        feature_names = list(records[0].get("features", {}).keys())
        feature_stats = {}
        for feat in feature_names:
            vals = [float(r["features"].get(feat, 0.0)) for r in records if feat in r.get("features", {})]
            if not vals:
                continue
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
                "zero_pct": round((zero_count / total) * 100, 1),
            }

        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_records": total,
            "label_distribution": label_dist,
            "label_sources": label_sources,
            "data_quality_breakdown": {
                k: {"count": v, "percentage": round((v / total) * 100, 1)}
                for k, v in quality_counts.items()
            },
            "source_provenance_breakdown": {
                k: {"count": v, "percentage": round((v / total) * 100, 1)}
                for k, v in source_counts.items()
            },
            "feature_statistics": feature_stats,
            "audit_summary": {
                "is_valid": audit_report.is_valid if audit_report else True,
                "total_violations": audit_report.total_violations if audit_report else 0,
                "critical_violations": audit_report.critical_count if audit_report else 0,
            },
        }

        return report

    def to_markdown(self, report_dict: Dict[str, Any]) -> str:
        if report_dict.get("status") == "EMPTY":
            return "# Road-Risk Dataset Quality Report\n\nNo records present in dataset."

        total = report_dict["total_records"]
        lines = [
            "# ADAS Road-Risk Dataset Quality Report",
            f"**Generated:** {report_dict['timestamp_utc']}  ",
            f"**Total Records Processed:** {total}  ",
            f"**Leakage Audit Gate:** {'PASSED' if report_dict['audit_summary']['is_valid'] else 'FAILED'}",
            "",
            "## 1. Target Label Distribution",
            "| Class | Count | Share (%) |",
            "| :--- | :--- | :--- |",
        ]

        for lbl, stats in report_dict["label_distribution"].items():
            lines.append(f"| **{lbl}** | {stats['count']} | {stats['percentage']}% |")

        lines.extend([
            "",
            "## 2. Source Provenance Breakdown",
            "| Source Classification | Count | Share (%) |",
            "| :--- | :--- | :--- |",
        ])
        for src, stats in report_dict["source_provenance_breakdown"].items():
            lines.append(f"| `{src}` | {stats['count']} | {stats['percentage']}% |")

        lines.extend([
            "",
            "## 3. Data Quality Tier Breakdown",
            "| Quality Tier | Count | Share (%) |",
            "| :--- | :--- | :--- |",
        ])
        for q, stats in report_dict["data_quality_breakdown"].items():
            lines.append(f"| `{q}` | {stats['count']} | {stats['percentage']}% |")

        lines.extend([
            "",
            "## 4. Canonical Feature Summary (25 Features)",
            "| Feature Name | Min | Max | Mean | Std | Zero Rate (%) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for feat, stats in report_dict["feature_statistics"].items():
            lines.append(
                f"| `{feat}` | {stats['min']} | {stats['max']} | {stats['mean']} | {stats['std']} | {stats['zero_pct']}% |"
            )

        lines.extend([
            "",
            "## 5. Leakage & Invariant Audit Status",
            f"- **Valid for Ingestion:** {report_dict['audit_summary']['is_valid']}",
            f"- **Total Violations Detected:** {report_dict['audit_summary']['total_violations']}",
            f"- **Critical Violations:** {report_dict['audit_summary']['critical_violations']}",
        ])

        return "\n".join(lines)
