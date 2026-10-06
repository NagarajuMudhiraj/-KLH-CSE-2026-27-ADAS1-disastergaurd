# Geospatial Road-Flood Pilot Dataset Quality Report (Phase 9)

**File Path:** `data/processed/road_risk_geospatial_pilot.csv`  
**Dataset Version:** `v1.0-geospatial-pilot`  
**Audit Timestamp:** 2026-09-30T19:25:00+05:30  
**Data Classification:** `REAL` (100%)  
**Phase 9 Status:** `PILOT_VALID_TARGET_READY_FOR_SCALING`  
**Model Training Readiness:** `NOT_READY_FOR_MODEL_TRAINING` (pilot sample size N=32 is for methodology validation; scaling required before training).

---

## 1. Candidate and Eligible Event Summary

| Metric | Count | Details / Provenance |
|---|---|---|
| **Total INDOFLOODS National Gauging Stations** | 214 | HydroSense Lab, IIT Delhi (Zenodo Record 14584654 / 14584655) |
| **Total INDOFLOODS Historical Flood Events** | 4,548 | Nationally curated CWC discharge & water-level records (1978–2020) |
| **Telangana Native Gauging Stations** | 8 | Nizam Sagar (939), Singur Dam (916), K. Agraharam (917), Bhadrachalam (925), Jewangi (926), Eturunagaram (943), Dummugudem (922), Srisailam Dam (913) |
| **Telangana Candidate Flood Events** | 68 | CWC verified river flood stages exceeding Warning / Danger thresholds |
| **Pilot Eligible Historical Events Selected** | 6 | `INDOFLOODS-gauge-925-1` (2006), `INDOFLOODS-gauge-925-2` (2014), `INDOFLOODS-gauge-925-6` (2019), `INDOFLOODS-gauge-916-1` (2019), `INDOFLOODS-gauge-916-8` (2019), `INDOFLOODS-gauge-916-11` (2019) |
| **Pilot Baseline Negative Controls** | 2 | Confirmed dry-season non-flood baseline dates (`2019-03-15` for Bhadrachalam and Singur) |
| **Total Distinct Event Periods** | 8 | 6 flood events + 2 baseline control periods across 2 distinct river basins |

---

## 2. Road Network and Spatial Join Metrics

| Metric | Count | Source & Details |
|---|---|---|
| **Authoritative Road Source** | TGRAC GIS | `RnB_Folder/RnB_Roads/MapServer` (Government of Telangana) |
| **Native Spatial Reference** | EPSG:32644 | WGS 84 / UTM Zone 44N (reprojected to EPSG:4326 via `outSR=4326`) |
| **Candidate Road Features Inspected** | 72 | 13 road features in Bhadrachalam bbox; 59 road features in Singur bbox |
| **Selected Representative Pilot Roads** | 8 | NH-30 (3 segments), SH-12, NH-65, MDR-60 (3 segments) across 4 road hierarchies |
| **Valid Road-Event Intersections** | 32 | Exact polyline-to-gauge haversine distance + centroid elevation |
| **Spatial Join Success Rate** | 100.0% | 32 / 32 successful distance and coordinate evaluations |
| **DEM Elevation Join Success Rate** | 100.0% | 32 / 32 successful Copernicus DEM 90m / SRTM elevation queries (33m – 607m) |

---

## 3. Historical Weather Join Metrics

| Metric | Count / Value | Details |
|---|---|---|
| **Historical Weather Provider** | Open-Meteo Archive | Reanalysis archive keyed to exact road centroid coordinates & event date |
| **Historical Weather Join Success Rate** | 100.0% | 32 / 32 successful retrievals |
| **Time Alignment** | Exact event date | ISO 8601 YYYY-MM-DD (preserves native source temporal precision; no invented hours) |
| **Features Retrieved** | 3 | Daily precipitation (`rainfall_24h_mm`), Mean temperature (`temperature_c`), Max wind speed (`wind_speed_kmh`) |

---

## 4. Observation and Target Distribution

| Attribute | Value |
|---|---|
| **Total Valid Pilot Observations** | 32 |
| **Target Variable** | `target_flooded` (Binary Flood Exposure) |
| **Class 0 (`NOT_FLOODED`)** | 17 (53.1%) |
| **Class 1 (`FLOODED`)** | 15 (46.9%) |
| **Label Quality** | 100% HIGH (source-backed by CWC water-level exceedance + physical proximity) |
| **Data Classification** | 100% REAL (zero simulated or synthetic rows) |

### Class Breakdown by Event
* `INDOFLOODS-gauge-925-1` (2006 Severe Flood): 3 Flooded, 1 Not Flooded
* `INDOFLOODS-gauge-925-2` (2014 Flood): 3 Flooded, 1 Not Flooded
* `INDOFLOODS-gauge-925-6` (2019 Flood): 3 Flooded, 1 Not Flooded
* `BASELINE_DRY_20190315_BHADRA`: 0 Flooded, 4 Not Flooded
* `INDOFLOODS-gauge-916-1` (2019 Severe Flood): 2 Flooded, 2 Not Flooded
* `INDOFLOODS-gauge-916-8` (2019 Severe Flood): 2 Flooded, 2 Not Flooded
* `INDOFLOODS-gauge-916-11` (2019 Severe Flood): 2 Flooded, 2 Not Flooded
* `BASELINE_DRY_20190315_SINGUR`: 0 Flooded, 4 Not Flooded

---

## 5. Feature Availability and Schema Audit

| Feature Name | Type | Availability | Source |
|---|---|---|---|
| `observation_id` | String | 100% (32/32) | Canonical pilot key (`REAL_OBS_001` - `032`) |
| `event_id` | String | 100% (32/32) | INDOFLOODS / Baseline identifier |
| `event_date` | String | 100% (32/32) | ISO 8601 (YYYY-MM-DD) |
| `road_segment_id` | String | 100% (32/32) | TGRAC authoritative layer + ObjectID |
| `road_name` | String | 100% (32/32) | TGRAC official road name |
| `latitude` | Float | 100% (32/32) | Road polyline centroid WGS84 |
| `longitude` | Float | 100% (32/32) | Road polyline centroid WGS84 |
| `elevation_m` | Float | 100% (32/32) | Open-Meteo DEM (Copernicus 90m) |
| `road_type` | String | 100% (32/32) | Canonical mapping (`highway`, `arterial`, `collector`, `local`) |
| `road_surface` | String | 100% (32/32) | TGRAC road surface (`BT`, `CC`, `WBM`, `Earthen`) |
| `road_length_m` | Float | 100% (32/32) | TGRAC native segment length |
| `distance_to_flood_m` | Float | 100% (32/32) | Geospatial haversine distance to active flood reach |
| `rainfall_24h_mm` | Float | 100% (32/32) | Open-Meteo reanalysis archive |
| `temperature_c` | Float | 100% (32/32) | Open-Meteo reanalysis archive |
| `wind_speed_kmh` | Float | 100% (32/32) | Open-Meteo reanalysis archive |
| `gauge_water_level_m` | Float | 100% (32/32) | CWC / INDOFLOODS peak water level |
| `flood_stage` | String | 100% (32/32) | CWC flood classification (`Normal`, `Flood`, `Severe Flood`) |
| `target_flooded` | Integer | 100% (32/32) | Binary ground-truth target (0 or 1) |

---

## 6. Provenance Completeness

All 32 rows contain full end-to-end source tracking:
* `flood_source`: `INDOFLOODS_IIT_DELHI_ZENODO_14584655`
* `road_source`: `TGRAC_GIS_RnB_Roads_EPSG32644`
* `weather_source`: `OPEN_METEO_HISTORICAL_ARCHIVE`
* `elevation_source`: `OPEN_METEO_ELEVATION_API_COPERNICUS_DEM`
* `label_source`: `CWC_INDOFLOODS_TGRAC_SPATIAL_JOIN`
* `label_reason`: Full human-readable physical rationale documented per row
* `label_quality`: `HIGH`
* `data_classification`: `REAL`

---

## 7. Rejected Observations and Exclusion Reasons

1. **TGRAC GHMC Inundation Areas (`GHMCNalas_Folder/GHMCNalas_vul/MapServer/1`)**:
   - Rejected as historical event ground truth.
   - Reason: Layer contains 23 static point locations (KMZ waterlogging spots) with `Time Info: None` and zero event timestamps. Per Phase 9 instructions, it is classified as `STATIC_SPATIAL_REFERENCE`, not `HISTORICAL_EVENT_LABEL`.
2. **Road Slope (`road_slope_pct`)**:
   - Excluded from the pilot feature set.
   - Reason: TGRAC road polylines are 2D (no native Z vertices). Approximating slopes from coarse 90m DEM introduces severe topological artifacts. Excluded per policy until verified 3D road profiles are integrated.
3. **Traffic Features (`traffic_level`, `vehicle_density`, `congestion_change`)**:
   - Excluded from the pilot feature set.
   - Reason: No verified historical traffic feed exists for 2006–2019 in these rural/suburban Telangana corridors. Zero synthetic injection permitted.
4. **Vehicle Telemetry & Visual Features**:
   - Excluded from tabular pilot.
   - Reason: Hardware-dependent operational variables; FloodNet aerial visual features are domain-incompatible with ground ADAS perception.
