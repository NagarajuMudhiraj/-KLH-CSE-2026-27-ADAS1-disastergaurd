# ADAS Road-Risk Model V2 — Feature Selection & Classification Specification

**Project:** Intelligent Vehicle Assistance During Disasters (ADAS)  
**Document Version:** 2.0.0  
**Phase:** Phase 5 — Feature Availability & Training Readiness  
**Target Architecture:** Tabular Road-Risk Gradient Boosted Trees (XGBoost V2) + Independent YOLOv11 Visual Branch  
**Status:** **AUTHORITATIVE SPECIFICATION**

---

## 1. Principles of Feature Selection for Road-Risk V2

The Phase 1 synthetic prototype utilized 25 candidate features. However, real-world deployment and rigorous ML governance prohibit naively training on all 25 features. Features must satisfy strict criteria to be admitted into the V2 training vector:

1. **Dual-Availability Invariant:** A **CORE** feature must be reliably available during both **TRAINING** (historical real-world data) and **REAL-TIME INFERENCE** (vehicle production runtime).
2. **Leakage Immunity:** Features that are direct proxies, circular transformations, or tautological re-encodings of the target variable (`road_risk_status`) must be **EXCLUDED**.
3. **Sensor Realism:** Telemetry that requires non-existent physical sensors (e.g. onboard CAN-bus brake transducers without physical hardware) must be classified as **FUTURE HARDWARE** rather than masquerading as real training data.
4. **Architectural Separation:** The visual object-detection system (YOLOv11) operates as an independent perception branch. Visual detections from the same imagery used for ground-truth annotation must NOT be used as unconstrained inputs to tabular risk models.

---

## 2. Comprehensive 25-Feature Classification Matrix

Every feature from `config/road_risk_features.json` is classified into one of four tiers:
- **`CORE`**: Primary input feature; robustly available in both historical training archives and production inference APIs; minimal leakage risk.
- **`OPTIONAL`**: Secondary feature; admitted into training if available, but model must tolerate missingness/imputation during inference.
- **`FUTURE` / `FUTURE_HARDWARE`**: Architecturally defined, but unavailable without external hardware (OBD-II CAN bus) or commercial subscriptions (Mapbox/TomTom flow).
- **`EXCLUDED`**: Prohibited from XGBoost input vector due to critical target leakage, distribution shift, or severe domain mismatch.

| # | Feature Name | Group | Classification | Inference Availability | Training Availability | Leakage Risk | Primary Data Source | Architectural Justification & Reason for Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `rainfall_mm_h` | Environment | **CORE** | YES (Live API / Radar) | YES (ERA5 / Gauge) | LOW | Open-Meteo / Weather Radar | Key thermodynamic driver of road hydroplaning and localized flash flooding. Accessible via real-time API and historical hourly reanalysis. |
| 2 | `rainfall_10min_mm` | Environment | **OPTIONAL** | YES (Rolling buffer) | LIMITED (Gauge only) | LOW | Vehicle / Station buffer | Critical for detecting sudden convective downbursts. However, absent from standard global hourly reanalysis (ERA5); requires optional handling in historical training. |
| 3 | `rainfall_1h_mm` | Environment | **CORE** | YES (Live API) | YES (ERA5 hourly) | LOW | Open-Meteo / OWM API | Captures cumulative ground saturation and soil absorption exhaustion. Available universally across live and historical sources. |
| 4 | `visibility_m` | Environment | **OPTIONAL** | YES (Live API / Camera) | LIMITED (METAR only) | LOW | Weather API / Station | Vital for fog, torrential rain, and smoke. While available in live forecasts, it is absent in standard historical ERA5 archives. Marked optional to avoid synthetic imputation. |
| 5 | `temperature_c` | Environment | **CORE** | YES (Vehicle / API) | YES (ERA5 hourly) | LOW | Ambient Sensor / API | Informs black ice formation, wildfire convective intensity, and atmospheric lapse rate. Highly reliable across both historical archives and in-vehicle thermometers. |
| 6 | `wind_speed_kmh` | Environment | **CORE** | YES (Live API) | YES (ERA5 hourly) | LOW | Weather Station / API | High crosswinds destabilize high-profile vehicles, down trees, and fan wildfires. Available in live APIs and historical reanalysis archives. |
| 7 | `traffic_level` | Traffic | **CORE** | YES (Navigation / API) | YES (DOT / PeMS) | MEDIUM | Google Routes / OSM Flow | Traffic slowdown is a primary operational indicator of downstream road obstruction. Real-time inference can query routing providers or driver input. |
| 8 | `vehicle_density` | Traffic | **FUTURE** | LIMITED (CCTV / Radar) | LIMITED (Loop Detectors)| MEDIUM | Smart Highway CCTV | Requires smart infrastructure (loop detectors or aerial density cameras) not universally present on standard arterial roadways. |
| 9 | `congestion_change` | Traffic | **OPTIONAL** | YES (Temporal Delta) | YES (Historical Trend) | LOW | Derived Traffic Stream | Rate of congestion growth indicates rapid onset of blockages (e.g., sudden damming or accident). Model handles via temporal rolling window when traffic telemetry exists. |
| 10 | `vehicle_speed_kmh` | Telemetry | **FUTURE_HARDWARE** | YES (GPS / CAN-bus) | NO (No hardware) | LOW | In-vehicle OBD-II / GPS | While trivial to obtain from a connected vehicle in production, current historical training datasets (FloodNet) contain no matched OBD-II telemetry. Retained as future vehicle hardware feature. |
| 11 | `acceleration_mps2`| Telemetry | **FUTURE_HARDWARE** | YES (Vehicle IMU) | NO (No hardware) | LOW | In-vehicle IMU | Captures harsh deceleration patterns. No historical vehicle sensor logging exists in current disaster records. |
| 12 | `braking_intensity`| Telemetry | **FUTURE_HARDWARE** | YES (CAN-bus) | NO (No hardware) | LOW | Brake pressure transducer | Indicates emergency stop attempts. Cannot be fabricated as real historical training data without real vehicle logs. |
| 13 | `road_slope_pct` | Road / Geo | **CORE** | YES (Static GIS/DEM) | YES (Static GIS/DEM) | NONE | Digital Elevation Model | Steep downhill slopes exacerbate water accumulation in road sags and increase stopping distances. Static terrain data guarantees 100% training and inference availability. |
| 14 | `elevation_m` | Road / Geo | **CORE** | YES (GPS / DEM) | YES (Open-Elevation) | NONE | SRTM DEM / GPS Altimeter| Low-elevation coastal plains and river basins are geomorphologically prone to inundation. Static, zero temporal leakage risk. |
| 15 | `road_type` | Road / Geo | **CORE** | YES (OSM Highway) | YES (OSM Highway) | NONE | OpenStreetMap / GIS | Categorical infrastructure tag (0: Urban, 1: Highway, 2: Rural, 3: Bridge, 4: Tunnel). Bridges and low-lying underpasses have radically different vulnerability profiles. |
| 16 | `vehicle_count` | Visual | **OPTIONAL** | YES (YOLOv11 branch) | EXPERIMENTAL (Aerial) | LOW | YOLOv11 Vehicle Detector | Forward vehicle count indicates traffic queueing. Aerial vehicle counts suffer from perspective scale differences, but class presence is physically grounded. |
| 17 | `person_count` | Visual | **OPTIONAL** | YES (YOLOv11 branch) | EXPERIMENTAL (Aerial) | LOW | YOLOv11 Person Detector | Pedestrians on carriageways indicate evacuation, stalled vehicles, or severe hazard. Optional visual feature. |
| 18 | `fire_detected` | Visual | **OPTIONAL** | YES (YOLOv11 branch) | EXPERIMENTAL (Aerial) | MEDIUM | YOLOv11 Fire Detector | Critical visual safety alarm. Handled by YOLOv11 vision pipeline and passed to multimodal risk fusion. |
| 19 | `smoke_detected` | Visual | **OPTIONAL** | YES (YOLOv11 branch) | EXPERIMENTAL (Aerial) | MEDIUM | YOLOv11 Smoke Detector | Indicates wildfire or structural hazard near roadway. |
| 20 | `flood_detected` | Visual | **EXCLUDED (from Tabular)**| YES (YOLOv11 branch) | CIRCLULAR (Label proxy)| **CRITICAL**| YOLOv11 Flood Detector | When training on FloodNet imagery, the ground truth `BLOCKED` label is determined directly by water segmentation area. Feeding `flood_detected` from the same image creates circular leakage. Belongs exclusively in the separate visual perception branch. |
| 21 | `obstacle_count` | Visual | **OPTIONAL** | YES (YOLOv11 branch) | EXPERIMENTAL (Aerial) | LOW | YOLOv11 Road Damage | Debris, fallen trees, potholes detected on roadway. |
| 22 | `hazard_count` | Visual | **OPTIONAL** | YES (YOLOv11 branch) | EXPERIMENTAL (Aerial) | MEDIUM | YOLOv11 Aggregate | Sum of detected hazards in current scene. |
| 23 | `hazard_distance_m`| Visual | **EXCLUDED (from Aerial)** | YES (Dashcam Depth) | UNSUITABLE (Nadir UAV) | LOW | Monocular Depth Network | Dashcam depth networks estimate longitudinal meters ahead of the bumper. Aerial drone bounding box pixel dimensions do not map to vehicle stopping distance. |
| 24 | `flood_report` | Disaster | **OPTIONAL / CONDITIONAL** | YES (MongoDB / Waze) | EXCLUDED IF LABEL SOURCE| **HIGH** | Citizen Incident Database | If a citizen report is used to label the road as flooded/blocked, using `flood_report` as a feature is circular leakage. Only admissible if label comes from independent physical sensor or official police decree. |
| 25 | `road_closure_report`| Disaster | **EXCLUDED (as Predictor)**| YES (DOT Closure Feed) | IDENTICAL TO TARGET | **CRITICAL**| Official Municipal Feed | An official government road closure declaration **IS** the authoritative definition of `BLOCKED`. Using it as an input feature to predict whether the road is blocked is a tautological leak. |

---

## 3. Approved Core Feature Set for XGBoost V2

For the first real-world XGBoost V2 tabular model, the **Approved Core Feature Set** consists of 7 universally available, leakage-free physical and environmental predictors:

```json
{
  "approved_core_features": [
    "rainfall_mm_h",
    "rainfall_1h_mm",
    "temperature_c",
    "wind_speed_kmh",
    "traffic_level",
    "road_slope_pct",
    "elevation_m",
    "road_type"
  ],
  "approved_optional_features": [
    "rainfall_10min_mm",
    "visibility_m",
    "congestion_change",
    "vehicle_count",
    "person_count",
    "fire_detected",
    "smoke_detected",
    "obstacle_count",
    "hazard_count"
  ],
  "excluded_or_future_features": [
    "vehicle_speed_kmh",
    "acceleration_mps2",
    "braking_intensity",
    "vehicle_density",
    "flood_detected",
    "hazard_distance_m",
    "flood_report",
    "road_closure_report"
  ]
}
```

### Architectural Rationale for Core Isolation:
By restricting the foundational tabular risk model to **environmental meteorology**, **topographical physics**, and **traffic impedance**, the system avoids visual circularity with FloodNet annotations and maintains complete independence between the **XGBoost Risk Assessor** and the **YOLOv11 Object Detector**. The two branches are subsequently integrated at the application decision layer via the **Late-Fusion Risk Service** (`backend/app/services/risk_service.py`), preserving modularity, interpretability, and robust failover.
