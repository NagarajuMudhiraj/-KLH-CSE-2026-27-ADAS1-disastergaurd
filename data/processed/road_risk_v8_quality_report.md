# Data Quality & Feature Redesign Report: Road Risk Dataset V8

**Document Version:** 1.0  
**Phase:** Phase 13 Feature Representation Redesign  
**Audit Date:** 2026-09-30  
**Dataset Files:**
* `data/processed/road_risk_dataset_v8.csv`
* `data/processed/road_risk_dataset_v8.parquet`

---

## 1. Executive Summary

Dataset V8 represents a major architectural redesign of the tabular road flood-exposure dataset. Following the Phase 12 finding of `ROAD_PROXY_DOMINATED`, Dataset V8:
1. **Completely removes `road_length_m`** to prevent decision trees from using administrative segment length as a unique road-identity proxy.
2. **Replaces absolute `elevation_m` with `relative_elevation_m`** (relative channel elevation above regional riverbed datum), eliminating sea-level baseline bias between basins.
3. **Adds multi-day antecedent precipitation (`rainfall_72h_mm`, `rainfall_7d_mm`)** from Open-Meteo ERA5 Reanalysis, resolving the physical time lag between upstream rainfall crests and local river overflow.
4. **Adds upstream catchment antecedent precipitation (`upstream_rainfall_72h_mm`)** to capture inflow from upstream drainage corridors.
5. **Maintains 100% real provenance** with zero synthetic rows or label modifications.

---

## 2. Dataset Overview & Inventory

* **Total Observations ($N$):** 68 real observations
* **Total Columns:** 33 columns
* **Historical Flood Events:** 9 verified flood peaks (2005–2022)
* **Temporal Baseline Events:** 4 dry baseline controls (2019-03-15)
* **Total Event Windows:** 13 distinct event periods
* **Geographic Regions:** 4 regions across 2 major river basins:
  * Godavari Basin: `Godavari_Lower` (Bhadrachalam)
  * Krishna Basin: `Manjira_Singur` (Medak/Sangareddy), `Manjira_NizamSagar` (Kamareddy), `Krishna_Agraharam` (Gadwal)
* **Unique Road Segments:** 16 segments from TGRAC GIS RnB Roads
* **Target Label:** `target_flood_exposure`
  * Class 0 (`NOT_EXPOSED`): 50 observations (73.53%)
  * Class 1 (`FLOOD_EXPOSED`): 18 observations (26.47%)
  * Class Imbalance Ratio: 2.78 : 1

---

## 3. Feature Completeness & Summary Statistics

| Feature Name | Type | Completeness | Mean | Std | Min | Median | Max |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `rainfall_24h_mm` | float (mm) | 100% (68/68) | 2.97 | 8.26 | 0.00 | 0.80 | 38.60 |
| `rainfall_72h_mm` | float (mm) | 100% (68/68) | 16.67 | 27.26 | 0.00 | 5.05 | 110.80 |
| `rainfall_7d_mm` | float (mm) | 100% (68/68) | 40.18 | 47.02 | 0.00 | 22.20 | 161.00 |
| `upstream_rainfall_72h_mm`| float (mm) | 100% (68/68) | 17.13 | 27.07 | 0.00 | 5.40 | 99.70 |
| `relative_elevation_m` | float (m) | 100% (68/68) | +25.81 | 28.73 | -13.00 | +25.00 | +86.00 |
| `temperature_c` | float (°C) | 100% (68/68) | 28.55 | 2.20 | 25.20 | 28.15 | 34.40 |
| `wind_speed_kmh` | float (km/h) | 100% (68/68) | 21.12 | 6.68 | 10.70 | 19.50 | 37.60 |
| `road_type` | string (enum) | 100% (68/68) | arterial (9), collector (16), highway (43) | - | - | - | - |
| `road_surface` | string (enum) | 100% (68/68) | BT (64), CC (4) | - | - | - | - |

*Zero missing, null, or NaN values across all features.*

---

## 4. Feature Correlations with Flood Exposure

Linear correlation with `target_flood_exposure`:

| Feature | Correlation ($r$) | Physical Interpretation |
| :--- | :---: | :--- |
| **`rainfall_72h_mm`** | **+0.504** | Strongest meteorological predictor; captures 3-day catchment accumulation preceding flood crests. |
| **`upstream_rainfall_72h_mm`**| **+0.478** | Confirms that upstream precipitation directly drives downstream river exposure. |
| **`rainfall_7d_mm`** | **+0.454** | Captures soil moisture saturation and continuous multi-day monsoon systems. |
| **`relative_elevation_m`** | **-0.268** | Correct negative physical correlation: lower relative elevation increases exposure probability. |
| **`rainfall_24h_mm`** | **+0.267** | Significantly weaker than 72h accumulation due to hydrological propagation lags. |
| **`temperature_c`** | **-0.178** | Moderate negative correlation (dense cloud cover / precipitation drops daily temperature). |
| **`wind_speed_kmh`** | **-0.049** | Negligible correlation with riverine flood exposure. |

---

## 5. Data Provenance & Lineage Verification

| Field | Source Authority | Capture Method / Derivation | Temporal Scope |
| :--- | :--- | :--- | :--- |
| **Weather & Rainfall** | Open-Meteo Historical Archive | ERA5 Reanalysis at road centroid ($t-6d \dots t$) | Daily historical, 2005–2022 |
| **Upstream Rainfall** | Open-Meteo Historical Archive | ERA5 Reanalysis at CWC gauge coordinate ($t-2d \dots t$) | Daily historical, 2005–2022 |
| **Road Geometries** | TGRAC GIS RnB Roads | Overpass / ArcGIS REST Polylines (OSM verified) | Static road network layer |
| **DEM Elevation** | Copernicus GLO-30 DEM | Satellite Synthetic Aperture Radar (SAR) Elevation | 30m spatial resolution |
| **Relative Elevation** | Copernicus GLO-30 DEM | $z_{\text{road}} - z_{\text{gauge\_datum}}$ | Static channel relative height |
| **Flood Events** | CWC IndoFloods (IIT Delhi) | Gauged hydrological station water levels | Historical event catalog |
| **Target Label** | CWC Warning Level Stage | Fluvial flood hazard buffer ($<2,500\text{ m}$) | Deterministic label |

---

## 6. Leakage & Confounding Audit

1. **Direct Label Leakage:**
   * `distance_to_flood_m`, `gauge_water_level_m`, `gauge_warning_level_m`, and `flood_stage` are quarantined in `data/processed/road_risk_dataset_v8.csv` and strictly excluded from the V3 model feature contract in `models/road_risk_v3/feature_schema.json`.
2. **Temporal Leakage:**
   * All precipitation features (`rainfall_24h_mm`, `rainfall_72h_mm`, `rainfall_7d_mm`, `upstream_rainfall_72h_mm`) are computed strictly up to the observation timestamp ($t \le t_{\text{obs}}$). Zero future precipitation is included.
3. **Road Length Exclusion:**
   * `road_length_m` was completely removed from the dataset, eliminating the single largest source of artificial memorization found in Phase 12.
4. **Regional Confounding:**
   * `road_surface = CC` exists only in Singur on 1 road segment (`TGRAC_COLLECTOR_1732`).
   * `road_type = collector` exists only in Singur and NizamSagar.
   * These categorical features are retained in Dataset V8 for source integrity, but flagged in the schema as geographically constrained.

---

## 7. Recommended Evaluation Partitions for V3

### Split 1: Unseen-Road Evaluation ($\text{Train roads} \cap \text{Test roads} = \emptyset$)
* **Test Roads ($N=4$ roads, 18 observations: 7 exposed, 11 unexposed):**
  * `TGRAC_HIGHWAY_44` (Godavari_Lower)
  * `TGRAC_HIGHWAY_45` (Godavari_Lower)
  * `TGRAC_COLLECTOR_1731` (Manjira_Singur)
  * `TGRAC_COLLECTOR_452` (Manjira_NizamSagar)
* **Validation Roads ($N=3$ roads, 13 observations: 4 exposed, 9 unexposed):**
  * `TGRAC_ARTERIAL_23` (Godavari_Lower)
  * `TGRAC_COLLECTOR_1732` (Manjira_Singur)
  * `TGRAC_HIGHWAY_423` (Krishna_Agraharam)
* **Train Roads ($N=9$ roads, 37 observations: 7 exposed, 30 unexposed):**
  * All remaining 9 road segments across the 4 regions.

### Split 2: Cross-Basin Validation
* **Fold A (Krishna to Godavari):**
  * Train on Krishna Basin (Singur, NizamSagar, Agraharam: 48 rows).
  * Test on Godavari Basin (Bhadrachalam: 20 rows: 12 exposed, 8 unexposed).
* **Fold B (Godavari to Singur):**
  * Train on Godavari Basin + NizamSagar/Agraharam (52 rows).
  * Test on Singur Basin (16 rows: 6 exposed, 10 unexposed).

---

## 8. Training Readiness Verdict

**`READY_FOR_V3_MODEL_TRAINING`**

*Dataset V8 resolves the core diagnostic defects identified in Phase 12. It eliminates road-length memorization, normalizes elevation into a transferable relative hydrologic datum, and provides multi-day antecedent precipitation that aligns with river flood crest physics.*
