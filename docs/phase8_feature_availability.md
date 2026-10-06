# Phase 8 Feature Availability — Actual Implementation

| Classification | Features | Current source/status | Historical / inference availability | Fallback policy |
|---|---|---|---|---|
| CORE | None | No feature has qualified source-native training rows | Not established | Exclude from training |
| OPTIONAL | `visibility_m`, `rainfall_10min_mm` | Weather provider can return live values when available | Historical needs explicit station/gauge join | `None` / UNAVAILABLE |
| FUTURE | `rainfall_mm_h`, `rainfall_1h_mm`, `temperature_c`, `wind_speed_kmh`, `traffic_level`, `elevation_m` | Weather live API exists; traffic/road connectors do not | Weather needs real row time/location; traffic/DEM need provider + geometry | No constants |
| EXCLUDED | `road_slope_pct`, `road_type`, telemetry, visual detections, reports, target | Road/telemetry providers are unavailable without a verified connector; visual/report features can leak | Not valid for first tabular model | Do not include in model vector |

Provider modes are explicit: LIVE, SIMULATOR, FIXTURE, and UNAVAILABLE. Only a
verified LIVE source observation may be classified REAL. Simulator output is
REALISTIC_SIMULATION; fixture/benchmark data is never REAL.
