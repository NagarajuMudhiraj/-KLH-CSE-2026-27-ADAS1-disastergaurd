# ADAS Phase 6 — V4 Data Quality Report

**Dataset:** `road_risk_dataset_v4`  
**Verdict:** **NOT_READY_FOR_MODEL_TRAINING**

## Counts

| Measure | Count |
|---|---:|
| Source rows inspected (V3) | 50 |
| V4 eligible real rows | 0 |
| Simulated rows | 0 |
| Quarantined real source rows | 50 |
| Independent verified events in V4 | 0 |
| Training / validation / test rows | 0 / 0 / 0 |

## Labels, regions, and missingness

| Measure | SAFE | RISKY | BLOCKED |
|---|---:|---:|---:|
| Eligible V4 labels | 0 | 0 | 0 |

There are no V4 regions or road segments because no source row is eligible.
Eligible label-quality distribution is GOLD 0, SILVER 0, BRONZE 0 and UNVERIFIED
0. Feature missingness and value distributions are therefore not applicable;
they have not been silently filled. The quarantined source ledger contains one
claimed event (Hurricane Harvey / Texas) and SILVER FloodNet annotations, but it
is not an event-level evaluation dataset.

## Why V4 is empty

The source images/labels are genuine FloodNet material, but their tabular
metadata is not source-native. The Phase-5 builder manufactures a Houston
coordinate progression and timestamp rotation, attaches ERA5 values to the
Houston centre, and inserts constant traffic, slope, and road-type values.
Keeping these as model rows would misrepresent provenance. V3 remains as an
auditable source ledger; no source data or labels were deleted/relabelled.

## Feature and integrity audit

| Item | Result |
|---|---|
| Weather temporal alignment | Unsupported per image: assigned hour is not image capture time |
| Weather spatial alignment | Unsupported per image: coordinate is generated |
| Traffic | Hardcoded `2.0`; excluded (FUTURE) |
| Road slope | Hardcoded `0.5`; excluded |
| Road type | Hardcoded `1`; excluded |
| Elevation | Houston-centre value, not a verified segment coordinate; excluded |
| Target leakage | V4 has no feature rows; label-derived visual features remain excluded |
| Duplicates | 0 eligible rows / 0 duplicates |
| Hardcoded/fallback detection | 50/50 source rows contain the traffic, slope and road-type fallbacks listed below |
| Final holdout | Not created: an independent event is required first |

## Quarantine evidence

Every one of the 50 V3 rows has these failures:

- observation timestamp is a builder-assigned ERA5 slot, not a FloodNet capture timestamp
- latitude/longitude and segment_id are builder-generated Houston jitter, not image geolocation
- weather is joined at Houston centre, not a verified observation coordinate
- traffic_level is the hardcoded 2.0 fallback
- road_slope_pct is the hardcoded 0.5 fallback
- road_type is the hardcoded highway fallback
