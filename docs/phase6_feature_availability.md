# Phase 6 Feature Availability

| Classification | Features | Requirement/status |
|---|---|---|
| CORE | None | No feature currently has both source-native training provenance and a consistent inference-time contract. |
| OPTIONAL | `visibility_m`, `rainfall_10min_mm` | Only after station/gauge data are explicitly time-and-location joined. Never impute constants. |
| FUTURE | `rainfall_mm_h`, `rainfall_1h_mm`, `temperature_c`, `wind_speed_kmh`, `traffic_level`, `elevation_m` | Weather and DEM can become CORE when source-native observation coordinates/times are available. Traffic needs a credible historical archive and defined scale. |
| EXCLUDED | `road_slope_pct`, `road_type`, all vehicle telemetry, visual detections, reports, target | V3 uses hardcoded geography; telemetry has no logs; visual features risk label/source and camera-domain leakage; reports are tautological. |

`traffic_level` is **FUTURE**, not CORE: every current V3 value is the same `2.0` fallback. The V4 schema contains no traffic column.
