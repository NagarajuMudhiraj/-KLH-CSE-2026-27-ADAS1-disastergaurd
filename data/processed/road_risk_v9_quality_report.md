# Data Quality & Representation Upgrade Report: Road Risk Dataset V9

**Document Version:** 1.0  
**Phase:** Phase 15 Representation & Dataset Expansion  
**Audit Date:** 2026-09-30  
**Dataset Files:**
* CSV: [`data/processed/road_risk_dataset_v9.csv`](file:///d:/datasets_IDM(ADAS)/data/processed/road_risk_dataset_v9.csv)
* Parquet: [`data/processed/road_risk_dataset_v9.parquet`](file:///d:/datasets_IDM(ADAS)/data/processed/road_risk_dataset_v9.parquet)

---

## 1. Executive Summary & Purpose

Dataset V9 formalizes the physical representation overhaul designed in Phase 15 to address the cross-basin instability diagnosed in Phase 14. Key enhancements:
1. **Permanent Exclusion of Administrative & Geographic Proxies:**
   * Completely excluded from candidate model inputs: `road_length_m` (memorization proxy), `road_type` (regional confounding), `road_surface` (unbalanced proxy), and `elevation_m` (sea-level basin bias).
2. **Integration of Height Above Nearest Drainage (`hand_m`):**
   * Implements true local stream-relative drainage clearance (meters) derived from Copernicus GLO-30 DEM and active river centerlines, achieving a negative correlation of **-0.329** with flood exposure.
3. **Integration of Upstream Catchment-Averaged Precipitation (`catchment_mean_rainfall_72h_mm`):**
   * Incorporates spatial basin-averaged 3-day precipitation ($T_{\text{3d}}$) from CWC IndoFloods catchment polygons ($r = +0.434$).
4. **Zero Synthetic Data:**
   * Contains strictly 68 genuine, source-backed observations. No synthetic rows or interpolated hydrographs were fabricated.

---

## 2. Dataset Overview & Inventory

* **Total Observations ($N$):** 68 real observations
* **Total Columns:** 36 columns
* **Historical Flood Event Periods:** 9 verified flood peaks (2005–2022)
* **Temporal Baseline Periods:** 4 dry baseline controls (2019-03-15)
* **Total Event Windows:** 13 distinct event periods
* **Major River Basins:** 2 major river basins (Godavari River Basin, Krishna River Basin)
* **Sub-Basin Regions:** 4 regions (Godavari Lower, Manjira Singur, Manjira NizamSagar, Krishna Agraharam)
* **Unique Road Segments:** 16 segments from TGRAC GIS RnB Roads
* **Target Label:** `target_flood_exposure`
  * Class 0 (`NOT_EXPOSED`): 50 observations (73.53%)
  * Class 1 (`FLOOD_EXPOSED`): 18 observations (26.47%)
  * Class Imbalance Ratio: 2.78 : 1

---

## 3. Candidate Feature Set Summary & Correlations

| Feature Name | Category | Completeness | Mean | Std | Min | Median | Max | Correlation with Target ($r$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `rainfall_72h_mm` | DYNAMIC_WEATHER | 100% | 16.67 mm | 27.26 | 0.00 | 5.05 | 110.80 | **+0.504** |
| `upstream_rainfall_72h_mm` | UPSTREAM_HYDROLOGY | 100% | 17.13 mm | 27.07 | 0.00 | 5.40 | 99.70 | **+0.478** |
| `rainfall_7d_mm` | DYNAMIC_WEATHER | 100% | 40.18 mm | 47.02 | 0.00 | 22.20 | 161.00 | **+0.454** |
| `catchment_mean_rainfall_72h_mm`| UPSTREAM_HYDROLOGY | 100% | 37.56 mm | 42.71 | 0.00 | 36.11 | 145.69 | **+0.434** |
| `rainfall_24h_mm` | DYNAMIC_WEATHER | 100% | 2.97 mm | 8.26 | 0.00 | 0.80 | 38.60 | **+0.267** |
| `wind_speed_kmh` | DYNAMIC_WEATHER | 100% | 21.12 km/h | 6.68 | 10.70 | 19.50 | 37.60 | **-0.049** |
| `temperature_c` | DYNAMIC_WEATHER | 100% | 28.55 °C | 2.20 | 25.20 | 28.15 | 34.40 | **-0.178** |
| `hand_m` | RELATIVE_HYDROLOGY | 100% | 21.62 m | 28.32 | -22.00 | 11.50 | 98.00 | **-0.329** |

*All candidate features are 100% complete with zero nulls / NaNs.*

---

## 4. Evaluation Partitions & Overlap Matrix

| Partition Strategy | Train Rows | Val Rows | Test Rows | Event Overlap | Road Overlap | Basin Overlap | Minimum Test Quality |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **A. Event-Held-Out** | 40 (6 events) | 12 (3 events) | 16 (4 events) | **0.0% (Disjoint)** | 100.0% (Repeating) | 100.0% | Valid (Pos: 5, Neg: 11) |
| **B. Unseen-Road** | 37 (9 roads) | 13 (3 roads) | 18 (4 roads) | 100.0% | **0.0% (Disjoint)** | 100.0% | Valid (Pos: 7, Neg: 11) |
| **C. Cross-Basin (Fold A)** | 48 (Krishna) | 0 | 20 (Godavari) | **0.0% (Disjoint)** | **0.0% (Disjoint)** | **0.0% (Disjoint)** | Valid (Pos: 12, Neg: 8) |
| **C. Cross-Basin (Fold B)** | 52 (Godavari+) | 0 | 16 (Singur) | **0.0% (Disjoint)** | **0.0% (Disjoint)** | **0.0% (Disjoint)** | Valid (Pos: 6, Neg: 10) |
| **C. Cross-Basin (Agraharam)**| 52 | 0 | 16 (Agraharam) | 0.0% | 0.0% | 0.0% | **`INSUFFICIENT_CLASS_DIVERSITY`** (Pos: 0, Neg: 16) |
| **C. Cross-Basin (NizamSagar)**| 52 | 0 | 16 (NizamSagar) | 0.0% | 0.0% | 0.0% | **`INSUFFICIENT_CLASS_DIVERSITY`** (Pos: 0, Neg: 16) |
| **D. Combined Generalization**| 48 | 0 | 4 (Singur 916-11)| **0.0% (Disjoint)** | **0.0% (Disjoint)** | **0.0% (Disjoint)** | Valid (Pos: 2, Neg: 2) |

---

## 5. Leakage & Provenance Audit

1. **Quarantined Direct-Label Variables:**
   * `distance_to_flood_m`, `gauge_water_level_m`, `gauge_warning_level_m`, `flood_stage`, `flood_intersection_ratio`, and `spatial_evidence_type` remain quarantined and strictly excluded from model feature inputs.
2. **Temporal Alignment:**
   * All precipitation features (`rainfall_24h_mm`, `rainfall_72h_mm`, `rainfall_7d_mm`, `upstream_rainfall_72h_mm`, `catchment_mean_rainfall_72h_mm`) represent antecedent periods ending on or before the observation timestamp ($t \le t_{\text{obs}}$). Zero future precipitation is present.
3. **Terrain Static Integrity:**
   * `hand_m` is derived exclusively from static digital elevation and drainage stream centerlines, containing zero dynamic flood stage information.

---

## 6. Training Readiness Assessment

**Final Decision: `V4_DATASET_READY`**

*Dataset V9 provides a scientifically validated feature representation upgrade (`hand_m`, `catchment_mean_rainfall_72h_mm`) while eliminating administrative road proxies. It is ready for offline benchmarking once a dedicated model training phase is commissioned.*
