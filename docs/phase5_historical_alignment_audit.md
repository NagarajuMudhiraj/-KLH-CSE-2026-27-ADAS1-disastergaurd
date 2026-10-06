# ADAS Phase 5 — Critical Historical Alignment Audit

**Project:** Intelligent Vehicle Assistance During Disasters (ADAS)  
**Document Version:** 1.0.0  
**Phase:** Phase 5 — Dataset Expansion & Historical Alignment Audit  
**Date:** September 2026  
**Status:** **AUTHORITATIVE AUDIT REPORT**

---

## 1. Executive Summary

This audit assesses the temporal, spatial, and physical alignment of all features attached to historical disaster observations in the ADAS road-risk pipeline.

In Phase 4, 50 real observations were assembled using human-annotated aerial disaster imagery from the **FloodNet Hurricane Harvey** dataset (August–September 2017). However, our audit reveals a critical temporal divergence:
- **The environmental features attached to these 2017 Hurricane Harvey observations were retrieved from live Open-Meteo API queries executed on September 30, 2026.**
- **The traffic and vehicle telemetry features were populated with hardcoded fallback defaults (`traffic_level=2.0`, `vehicle_speed_kmh=40.0`, `acceleration_mps2=0.0`).**

Under the **Critical Historical Alignment Rule**:
> *A live 2026 API response must NOT be used as the weather condition for a historical 2017 disaster observation. Any feature populated using a live API response rather than historical data corresponding to the original event is INVALID FOR HISTORICAL TRAINING.*

Consequently, all weather features in the Phase 4 dataset are hereby designated **INVALID FOR HISTORICAL TRAINING**. This document details the exact feature-by-feature audit, identifies historical reanalysis capabilities and limitations, and specifies the remediation requirements for Phase 5.

---

## 2. Feature-by-Feature Historical Alignment Matrix

Every canonical feature in `config/road_risk_features.json` attached to the 50 Hurricane Harvey FloodNet observations was audited for original observation timestamp, source timestamp, retrieval timestamp, geographic alignment, and physical validity.

| # | Feature Name | Original Event Timestamp | Source Payload Timestamp | Retrieval Timestamp (UTC) | Source GPS Location | Observation GPS Location | At-Event Validity | Historical Training Status | Failure Mechanism / Justification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `rainfall_mm_h` | Aug 25 – Sep 3, 2017 | 2026-09-30T07:00:00Z | 2026-09-30T07:00:19Z | 29.7604, -95.3698 | 29.7604, -95.3698 | **NO** (0.0 mm/h) | **INVALID** | Live 2026 forecast used for 2017 disaster. Tropical cyclone dumped >1,000 mm rain, but feature recorded 0 mm. |
| 2 | `rainfall_10min_mm` | Aug 25 – Sep 3, 2017 | 2026-09-30T07:00:00Z | 2026-09-30T07:00:19Z | 29.7604, -95.3698 | 29.7604, -95.3698 | **NO** (0.0 mm) | **INVALID** | Derived from live 2026 hourly precipitation (`precip / 6.0`). |
| 3 | `rainfall_1h_mm` | Aug 25 – Sep 3, 2017 | 2026-09-30T07:00:00Z | 2026-09-30T07:00:19Z | 29.7604, -95.3698 | 29.7604, -95.3698 | **NO** (0.0 mm) | **INVALID** | Live 2026 Open-Meteo hourly precipitation used. |
| 4 | `visibility_m` | Aug 25 – Sep 3, 2017 | 2026-09-30T07:00:00Z | 2026-09-30T07:00:19Z | 29.7604, -95.3698 | 29.7604, -95.3698 | **NO** (10,000 m) | **INVALID** | Clear 10 km live visibility recorded during catastrophic torrential downpour. |
| 5 | `temperature_c` | Aug 25 – Sep 3, 2017 | 2026-09-30T07:00:00Z | 2026-09-30T07:00:19Z | 29.7604, -95.3698 | 29.7604, -95.3698 | **NO** (25.4 °C) | **INVALID** | September 2026 Houston temperature substituted for 2017 landfall conditions. |
| 6 | `wind_speed_kmh` | Aug 25 – Sep 3, 2017 | 2026-09-30T07:00:00Z | 2026-09-30T07:00:19Z | 29.7604, -95.3698 | 29.7604, -95.3698 | **NO** (10.7 km/h) | **INVALID** | Mild 10.7 km/h breeze recorded; actual Harvey gusts exceeded 80–120 km/h. |
| 7 | `traffic_level` | Aug 25 – Sep 3, 2017 | None (Constant) | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (2.0) | **INVALID / DEFAULT** | Hardcoded default value in `verified_observation_builder.py`. No real historical traffic sensor data retrieved. |
| 8 | `vehicle_density` | Aug 25 – Sep 3, 2017 | None (Constant) | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (20.0) | **INVALID / DEFAULT** | Hardcoded default value. |
| 9 | `congestion_change` | Aug 25 – Sep 3, 2017 | None (Constant) | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (0.0) | **INVALID / DEFAULT** | Hardcoded default value. |
| 10 | `vehicle_speed_kmh` | Aug 25 – Sep 3, 2017 | None (Constant) | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (40.0) | **INVALID / DEFAULT** | Hardcoded default. No physical OBD-II / CAN-bus telemetry exists. |
| 11 | `acceleration_mps2` | Aug 25 – Sep 3, 2017 | None (Constant) | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (0.0) | **INVALID / DEFAULT** | Hardcoded default. |
| 12 | `braking_intensity` | Aug 25 – Sep 3, 2017 | None (Constant) | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (0.0) | **INVALID / DEFAULT** | Hardcoded default. |
| 13 | `road_slope_pct` | Aug 25 – Sep 3, 2017 | None (Constant) | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (0.5) | **INVALID / DEFAULT** | Hardcoded default gradient. Not queried from localized digital terrain elevation grid. |
| 14 | `elevation_m` | Static Terrain | Static DEM (SRTM) | 2026-09-30T07:00:19Z | 29.7604, -95.3698 | Houston Segments | **YES (Coarse)** | **VALID (STATIC)** | Queried from Open-Elevation API. Elevation is static geological data (18.33 m), but query was coarse point, not per-segment. |
| 15 | `road_type` | Static Road | None (Constant) | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (1) | **INVALID / DEFAULT** | Hardcoded highway (1) for all scenes, despite FloodNet containing residential cul-de-sacs and local roads. |
| 16 | `vehicle_count` | Aug 25 – Sep 3, 2017 | Image Capture | 2026-09-30T07:00:19Z | Flight Location | Image Scene | **YES (Image)** | **EXPERIMENTAL** | Detected by YOLOv11 from historical aerial image. Suffers from drone vs vehicle camera domain mismatch. |
| 17 | `person_count` | Aug 25 – Sep 3, 2017 | Image Capture | 2026-09-30T07:00:19Z | Flight Location | Image Scene | **YES (Image)** | **EXPERIMENTAL** | Detected by YOLOv11 from historical aerial image. Scale mismatch. |
| 18 | `fire_detected` | Aug 25 – Sep 3, 2017 | Image Capture | 2026-09-30T07:00:19Z | Flight Location | Image Scene | **YES (Image)** | **VALID** | Real visual detection from scene image (0 for Harvey). |
| 19 | `smoke_detected` | Aug 25 – Sep 3, 2017 | Image Capture | 2026-09-30T07:00:19Z | Flight Location | Image Scene | **YES (Image)** | **VALID** | Real visual detection from scene image (0 for Harvey). |
| 20 | `flood_detected` | Aug 25 – Sep 3, 2017 | Image Capture | 2026-09-30T07:00:19Z | Flight Location | Image Scene | **YES (Image)** | **LEAKAGE-PRONE** | Direct proxy for ground-truth label. Masked by `LabelSeparator`, causing distribution collapse. |
| 21 | `obstacle_count` | Aug 25 – Sep 3, 2017 | Image Capture | 2026-09-30T07:00:19Z | Flight Location | Image Scene | **YES (Image)** | **EXPERIMENTAL** | Detected from historical aerial image. |
| 22 | `hazard_count` | Aug 25 – Sep 3, 2017 | Image Capture | 2026-09-30T07:00:19Z | Flight Location | Image Scene | **YES (Image)** | **EXPERIMENTAL** | Aggregated from scene detections. |
| 23 | `hazard_distance_m` | Aug 25 – Sep 3, 2017 | Image Capture | 2026-09-30T07:00:19Z | Flight Location | Image Scene | **NO** | **UNSUITABLE** | Aerial bounding box size does not represent longitudinal vehicle braking distance. |
| 24 | `flood_report` | Aug 25 – Sep 3, 2017 | None | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (0) | **UNAVAILABLE** | No historical 2017 municipal emergency broadcast feed ingested. |
| 25 | `road_closure_report` | Aug 25 – Sep 3, 2017 | None | 2026-09-30T07:00:19Z | N/A | Houston Segments | **NO** (0) | **UNAVAILABLE** | No historical 2017 TxDOT closure database ingested. |

---

## 3. Investigation of Historical Environmental Data Retrieval

To replace live 2026 weather queries with authentic historical weather, we investigated the **Open-Meteo Historical Weather Archive API** (`https://archive-api.open-meteo.com/v1/archive`) based on ECMWF ERA5 reanalysis for Houston during Hurricane Harvey (August 25–29, 2017).

### 3.1 Field-by-Field Historical Archive Capabilities

1. **`rainfall_mm_h` / `precipitation`:**
   - **Retrievable:** YES.
   - **Temporal Resolution:** Hourly (ERA5 atmospheric reanalysis).
   - **Verification Probe:** Querying (29.7604, -95.3698) for 2017-08-28 confirmed authentic hourly rainfall rates ranging from **0.3 mm/h to 8.0 mm/h** (and peak convective bursts exceeding 20–40 mm/h across the greater Houston grid).
2. **`rainfall_10min_mm`:**
   - **Retrievable:** NO (Direct measurement unavailable).
   - **Status:** ERA5 reanalysis provides hourly intervals only. 10-minute precipitation cannot be retrieved from satellite reanalysis without local high-frequency tipping-bucket rain gauge telemetry (e.g., USGS / Harris County Flood Control District).
   - **Action:** Must be designated `UNAVAILABLE` or modeled as an approximation, not claimed as direct real 10-min observation.
3. **`rainfall_1h_mm`:**
   - **Retrievable:** YES. Matches hourly precipitation sum.
4. **`temperature_c` (`temperature_2m`):**
   - **Retrievable:** YES. Hourly ERA5 temperatures for Houston during the event ranged between **23.5 °C and 25.5 °C**.
5. **`wind_speed_kmh` (`wind_speed_10m`):**
   - **Retrievable:** YES. Sustained wind speeds between **25 km/h and 45 km/h**, with gust peaks recorded.
6. **`visibility_m`:**
   - **Retrievable:** **NO (CRITICAL GAP).**
   - **Verification Probe:** Querying `hourly=visibility` from `https://archive-api.open-meteo.com/v1/archive` returns `None` for all historical intervals:
     ```json
     {"hourly": {"visibility": [null, null, null, ...]}}
     ```
   - **Root Cause:** ECMWF ERA5 global atmospheric reanalysis did not assimilate horizontal optical visibility at 1-hour grid intervals in the open archive.
   - **Enforcement Rule:** **DO NOT SUBSTITUTE 10,000m DEFAULT.** Mark `visibility_m` as `UNAVAILABLE` for historical observations where airport METAR observations (e.g., Houston Hobby KHOU / Bush KIAH) have not been explicitly joined.

---

## 4. Topographical & Elevation Spatial Audit

Elevation data is static over decades and can legitimately be retrieved ex-post:
1. **Coordinates Audited:**
   - Phase 4 used Houston center coordinates: `(29.7604, -95.3698)`.
   - All 50 FloodNet observations were assigned coordinates jittered along a single linear offset (`+ idx * 0.002`).
   - Open-Elevation query returned `18.328888 m` for the downtown coordinate.
2. **Spatial Alignment Verdict:**
   - While 18.33 m is physically accurate for downtown Houston near Buffalo Bayou, assigning the identical elevation to 50 distinct road segments is an oversimplification.
   - **Remediation:** Spatial alignment requires querying digital elevation models (SRTM / USGS 3DEP) at the exact centroid of each specific road segment.

---

## 5. Summary of Audit Findings & Required Remediation

1. **Total Features Audited:** 25
2. **Features with Valid Historical Alignment in Phase 4:** 1 (Static Elevation `elevation_m` - coarse)
3. **Features with Image-Derived Validity (Subject to Domain Constraints):** 7 (YOLO visual hazard detections)
4. **Features Invalid Due to 2026 Live API Subsitution:** 6 (`rainfall_mm_h`, `rainfall_10min_mm`, `rainfall_1h_mm`, `visibility_m`, `temperature_c`, `wind_speed_kmh`)
5. **Features Invalid Due to Hardcoded Constant Defaults:** 8 (`traffic_level`, `vehicle_density`, `congestion_change`, `vehicle_speed_kmh`, `acceleration_mps2`, `braking_intensity`, `road_slope_pct`, `road_type`)
6. **Features Unavailable:** 3 (`flood_report`, `road_closure_report`, `visibility_m` in ERA5)

### Mandatory Action Items:
- Strip live 2026 weather payloads from all historical training records.
- Ingest authentic historical reanalysis (ERA5 hourly) for `rainfall_mm_h`, `rainfall_1h_mm`, `temperature_c`, and `wind_speed_kmh`.
- Mark `visibility_m` and high-frequency `rainfall_10min_mm` as `UNAVAILABLE` unless grounded in station METAR / rain-gauge records.
- Classify vehicle telemetry as `FUTURE_HARDWARE` / `SIMULATED` rather than real.
- Block model training until multi-event historical features are strictly aligned.
