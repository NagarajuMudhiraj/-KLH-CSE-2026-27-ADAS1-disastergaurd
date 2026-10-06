# Road Risk Dataset Schema
**ADAS — Intelligent Vehicle Assistance During Disasters**
**Document version:** 2.0 | **Phase:** 2 | **Status:** AUTHORITATIVE

---

## Purpose

This document defines the complete table structure for the future XGBoost road-risk training dataset. It specifies every column, its data type, unit, source, prediction-time availability, leakage risk, and relationship to the target variable.

This schema is fully compatible with `config/road_risk_features.json` v1.0.0. No Phase 1 feature contract changes are required.

---

## Observation Identity Columns (NOT features — excluded from X)

These columns identify each row. They are used for splitting, deduplication, and traceability. They must NEVER be passed as model input features.

| Column | Datatype | Description | Notes |
|---|---|---|---|
| `observation_id` | string (UUID) | Unique row identifier | Generated at collection time |
| `timestamp` | datetime (UTC ISO-8601) | Exact time of observation | Required for temporal split |
| `latitude` | float (degrees) | GPS latitude of road segment | Required for geographic grouping |
| `longitude` | float (degrees) | GPS longitude of road segment | Required for geographic grouping |
| `segment_id` | string | Road segment identifier (OSM way ID or custom) | Required for segment-level splitting |
| `event_id` | string (nullable) | Disaster event identifier if observation falls within a known event | Used to prevent same-event train/test mixing |
| `session_id` | string (nullable) | Vehicle / sensor session identifier | Used if vehicle telemetry data is included |
| `label_source` | string | How the label was obtained (see label_definition.md) | Audit trail |
| `data_quality` | string (HIGH/MODERATE/DEGRADED) | Based on fraction of non-null feature columns | Computed by feature_builder.py |

---

## Target Column (y — NOT an input feature)

| Column | Datatype | Values | Description | Leakage risk |
|---|---|---|---|---|
| `road_risk_status` | int | 0=Safe, 1=Risky, 2=Blocked | Ground-truth road condition label | MUST NOT appear in X |

---

## Feature Columns (X — model inputs)

All features below correspond to canonical features in `config/road_risk_features.json` v1.0.0.

### GROUP: ENVIRONMENT

| Feature | Datatype | Unit | Source | Required/Optional | Prediction-time Available | Leakage Risk | Notes |
|---|---|---|---|---|---|---|---|
| `rainfall_mm_h` | float | mm/h | OpenWeatherMap / Open-Meteo API | **REQUIRED** | YES | LOW | Currently live via /api/weather |
| `rainfall_10min_mm` | float | mm | Rolling 10-min weather API aggregate | Optional | YES (derived from API) | LOW | Must use past-10-min window only |
| `rainfall_1h_mm` | float | mm | OpenWeatherMap API `rain.1h` | Optional | YES | LOW | Currently returned by /api/weather |
| `visibility_m` | float | meters | OpenWeatherMap / Open-Meteo API | Optional | YES | LOW | Currently live via /api/weather |
| `temperature_c` | float | Celsius | OpenWeatherMap / Open-Meteo API | Optional | YES | LOW | Currently live via /api/weather |
| `wind_speed_kmh` | float | km/h | OpenWeatherMap / Open-Meteo API | Optional | YES | LOW | Currently live (converted from m/s) |

### GROUP: TRAFFIC

| Feature | Datatype | Unit | Source | Required/Optional | Prediction-time Available | Leakage Risk | Notes |
|---|---|---|---|---|---|---|---|
| `traffic_level` | float | index 1-10 | Traffic API / driver input / HERE Maps | **REQUIRED** | YES | MEDIUM | Current value, not future |
| `vehicle_density` | float | vehicles/km/lane | Traffic API / CCTV / highway telemetry | Optional | YES | MEDIUM | FUTURE PROVIDER |
| `congestion_change` | float | delta/h | Temporal delta of traffic_level, 15-min window | Optional | YES (requires past window) | LOW | Must not use future values |

### GROUP: VEHICLE TELEMETRY

| Feature | Datatype | Unit | Source | Required/Optional | Prediction-time Available | Leakage Risk | Notes |
|---|---|---|---|---|---|---|---|
| `vehicle_speed_kmh` | float | km/h | GPS / OBD-II / smartphone | Optional | YES | LOW | Indicates if traffic is flowing |
| `acceleration_mps2` | float | m/s² | IMU / smartphone accelerometer | Optional | YES | LOW | FUTURE PROVIDER |
| `braking_intensity` | float | ratio 0.0-1.0 | CAN-bus / deceleration classifier | Optional | YES | LOW | FUTURE PROVIDER |

### GROUP: ROAD / GEOGRAPHY

| Feature | Datatype | Unit | Source | Required/Optional | Prediction-time Available | Leakage Risk | Notes |
|---|---|---|---|---|---|---|---|
| `road_slope_pct` | float | % grade | Digital Elevation Model / OSM | Optional | YES (static) | NONE | Static map data, no temporal leakage |
| `elevation_m` | float | meters | GPS altitude / Open-Elevation API | Optional | YES | NONE | Static map data, no temporal leakage |
| `road_type` | int | categorical 0-4 | OpenStreetMap highway tag | Optional | YES (static) | NONE | Static, no temporal leakage |

### GROUP: VISUAL HAZARDS (from YOLOv11)

| Feature | Datatype | Unit | Source | Required/Optional | Prediction-time Available | Leakage Risk | Notes |
|---|---|---|---|---|---|---|---|
| `vehicle_count` | int | count | YOLOv11 class 'Vehicle' detection count | Optional | YES (current frame) | LOW | Must come from current frame only |
| `person_count` | int | count | YOLOv11 class 'Person' detection count | Optional | YES (current frame) | LOW | Must come from current frame only |
| `fire_detected` | int | 0 or 1 | YOLOv11 class 'Fire' presence flag | Optional | YES (current frame) | MEDIUM | Correlated with BLOCKED; monitor correlation |
| `smoke_detected` | int | 0 or 1 | YOLOv11 class 'Smoke' presence flag | Optional | YES (current frame) | MEDIUM | Correlated with RISKY |
| `flood_detected` | int | 0 or 1 | YOLOv11 class 'Flood' presence flag | Optional | YES (current frame) | HIGH | Strongly correlated with target; require dual-source validation |
| `obstacle_count` | int | count | YOLOv11 class 'Road Damage' count | Optional | YES (current frame) | LOW | |
| `hazard_count` | int | count | Sum of all YOLO hazard detections | Optional | YES (current frame) | MEDIUM | Aggregated from current frame |
| `hazard_distance_m` | float | meters | Monocular depth estimate / bbox geometry | Optional | YES | LOW | Requires calibration |

**Note on YOLO visual features and leakage:**
`flood_detected` and `fire_detected` will be highly correlated with the BLOCKED label. This is acceptable because YOLO detection is a legitimate real-time predictor. However, if YOLO confidence was used to *assign* the label, this becomes circular. The label must be sourced from an independent authority record. YOLO features may then be used as predictors of that label.

### GROUP: DISASTER / ROAD STATUS

| Feature | Datatype | Unit | Source | Required/Optional | Prediction-time Available | Leakage Risk | Notes |
|---|---|---|---|---|---|---|---|
| `flood_report` | int | 0 or 1 | MongoDB hazard collection (active reports within 2 km, 30 min) | Optional | YES | HIGH | If the report is also the label source, this creates leakage — must use separate reports |
| `road_closure_report` | int | 0 or 1 | Disaster authority / road authority API | Optional | YES | HIGH | If official closure IS the BLOCKED label, this feature must not be used as a predictor |

**Critical note on `flood_report` and `road_closure_report`:**
If the label for a BLOCKED row comes from an official road closure notice, then `road_closure_report = 1` would be perfectly correlated with `label = BLOCKED`. This is **circular leakage**. To use these as features, the label must come from a **different and independent source** than the report used for the feature value (e.g., label from physical flood gauge; feature from crowdsource reports, or vice versa).

---

## water_level — Special Column Assessment

The Phase 1 synthetic model used `water_level` as a key predictor. This column is assessed as:

| Criterion | Assessment |
|---|---|
| Classification | **sensor-dependent / optional** |
| Physical meaning | Water depth at a specific gauge location |
| Realistic for prototype | Only if a physical flood gauge or road-mounted water level sensor is integrated |
| Centimetre-precision at road | NOT realistic without a dedicated sensor infrastructure |
| Suitable as required feature | NO — cannot be required without sensor commitment |
| Suitable as optional feature | YES — if sourced from CWC/IMD flood gauge with GPS coordinate within 500 m of segment |
| Recommendation | Keep in feature contract as optional. Do not include as required. Do not allow it to be the primary label determinant. |

---

## Feature Columns Summary Table

| # | Feature | Group | Required? | Currently Available? | Real-time? | Leakage Risk |
|---|---|---|---|---|---|---|
| 1 | rainfall_mm_h | Environment | YES | YES (API) | YES | LOW |
| 2 | rainfall_10min_mm | Environment | No | Partial | YES | LOW |
| 3 | rainfall_1h_mm | Environment | No | YES (API) | YES | LOW |
| 4 | visibility_m | Environment | No | YES (API) | YES | LOW |
| 5 | temperature_c | Environment | No | YES (API) | YES | LOW |
| 6 | wind_speed_kmh | Environment | No | YES (API) | YES | LOW |
| 7 | traffic_level | Traffic | YES | YES (manual/API) | YES | MEDIUM |
| 8 | vehicle_density | Traffic | No | NO (Future) | YES | MEDIUM |
| 9 | congestion_change | Traffic | No | NO (Future) | YES | LOW |
| 10 | vehicle_speed_kmh | Vehicle | No | NO (Future) | YES | LOW |
| 11 | acceleration_mps2 | Vehicle | No | NO (Future) | YES | LOW |
| 12 | braking_intensity | Vehicle | No | NO (Future) | YES | LOW |
| 13 | road_slope_pct | Road | No | NO (Future) | YES | NONE |
| 14 | elevation_m | Road | No | NO (Future) | YES | NONE |
| 15 | road_type | Road | No | NO (Future) | YES | NONE |
| 16 | vehicle_count | Visual | No | YES (YOLO) | YES | LOW |
| 17 | person_count | Visual | No | YES (YOLO) | YES | LOW |
| 18 | fire_detected | Visual | No | YES (YOLO) | YES | MEDIUM |
| 19 | smoke_detected | Visual | No | YES (YOLO) | YES | MEDIUM |
| 20 | flood_detected | Visual | No | YES (YOLO) | YES | HIGH* |
| 21 | obstacle_count | Visual | No | YES (YOLO) | YES | LOW |
| 22 | hazard_count | Visual | No | YES (YOLO) | YES | MEDIUM |
| 23 | hazard_distance_m | Visual | No | Partial (YOLO) | YES | LOW |
| 24 | flood_report | Disaster | No | YES (MongoDB) | YES | HIGH* |
| 25 | road_closure_report | Disaster | No | YES (MongoDB) | YES | HIGH* |

*HIGH leakage risk features require independent label source validation before use (see data_policy.md Rule 8).

---

## Schema Compatibility

This schema is backward-compatible with `config/road_risk_features.json` v1.0.0. No changes to the Phase 1 feature contract are needed. The identity columns (`timestamp`, `latitude`, `longitude`, `segment_id`, etc.) are additions that sit outside the 25-feature canonical vector.

---

*Schema maintained by ADAS Phase 2 dataset design. Requires update if Phase 1 feature contract version changes.*
