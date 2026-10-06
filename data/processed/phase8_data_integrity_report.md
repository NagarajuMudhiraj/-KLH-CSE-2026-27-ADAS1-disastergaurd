# ADAS Phase 8 — Data Integrity Report

**Training readiness:** **NOT_READY_FOR_MODEL_TRAINING**

| Measure | Result |
|---|---:|
| Legacy V3 rows quarantined | 50 |
| Genuine real training rows | 0 |
| Integrity findings on inspected legacy rows | 256 |
| Critical findings | 250 |

## Quarantine reasons

- Generated Houston coordinate progression and assigned timestamp slots.
- Hardcoded traffic (`2.0`), road slope (`0.5`) and road type (`1`).
- Reused Houston-centre elevation and weather joins without source-native observation location/time.
- Feature-level provenance is absent from the legacy CSV.

## Provider status after cleanup

| Provider | Status | Training treatment |
|---|---|---|
| WeatherProvider | LIVE only when Open-Meteo/OWM responds; otherwise UNAVAILABLE | no fallback constants |
| TrafficProvider | UNAVAILABLE in LIVE mode | FUTURE/excluded |
| RoadProvider | UNAVAILABLE in LIVE mode | FUTURE/excluded |
| TelemetryProvider | UNAVAILABLE without CAN/OBD | FUTURE_SENSOR/excluded |
| DisasterReportProvider | UNAVAILABLE when MongoDB is offline | no default-zero report |
| YOLOFeatureProvider | LIVE only for successful inference; simulated otherwise | visual branch, not tabular V2 training |

## Auditor detections observed

- `GENERATED_COORDINATE_PATTERN`
- `GENERATED_TIMESTAMP_PATTERN`
- `MISSING_FEATURE_PROVENANCE`
- `REUSED_ELEVATION_ACROSS_LOCATIONS`
- `SUSPICIOUS_CONSTANT_FEATURE`
