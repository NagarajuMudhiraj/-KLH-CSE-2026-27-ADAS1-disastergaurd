# Phase 15 Height Above Nearest Drainage (HAND) Design & Target Proxy Audit

**Document Version:** 1.0  
**Phase:** Phase 15 Representation & Dataset Expansion  
**Date:** 2026-09-30  
**Intermediate Pilot File:** [`data/intermediate/hand_pilot_v4.csv`](file:///d:/datasets_IDM(ADAS)/data/intermediate/hand_pilot_v4.csv)

---

## 1. Scientific Principles of HAND

Height Above Nearest Drainage (HAND) is a normalized, hydrologically conditioned terrain model. Instead of measuring surface elevation above sea level ($z_{\text{MSL}}$) or elevation above an arbitrary regional gauge point ($z - z_{\text{gauge}}$), HAND calculates the **vertical elevation difference between a terrain surface cell and the specific hydrologically connected drainage stream cell to which it discharges**:

$$\text{HAND}(x) = z(x) - z(x_{\text{drainage}})$$

### Why HAND Eliminates Cross-Basin Bias:
1. **Physical Scale Equivalence:** In fluvial hydrology, backwater overflow and floodplain inundation depend on whether the river stage exceeds the channel bank height. A road located 5 meters above its local drainage stream ($\text{HAND} = 5\text{ m}$) faces identical gravitational inundation potential whether the river lies at sea level (Godavari: $33\text{ m}$ MSL) or in an upland Deccan plateau (Singur: $520\text{ m}$ MSL).
2. **Accounts for Downstream Stream Gradient:** Simple scalar channel subtraction ($z_{\text{road}} - z_{\text{gauge}}$) assumes the riverbed is completely flat. Real rivers slope downwards; over a 15 km reach, riverbeds drop by 10 to 30 meters. HAND traces the local flow path directly to the adjacent river cell, compensating for natural stream gradients.

---

## 2. Derivation Methodology & Data Sources

* **DEM Source:** European Space Agency Copernicus GLO-30 Digital Elevation Model (30m spatial resolution).
* **Drainage Network Authority:** Central Water Commission (CWC) monitored river channels and HydroSHEDS flowlines.
* **Coordinate Reference System:** WGS84 Geographic Coordinates (EPSG:4326).
* **Derivation Method:**
  * For each road segment polyline centroid $(x_{\text{road}}, y_{\text{road}})$, the nearest hydraulic drainage centerline coordinate $(x_{\text{channel}}, y_{\text{channel}})$ along the active river reach was identified.
  * Digital radar surface elevations were extracted from the Copernicus GLO-30 DEM for both the road centroid and the drainage channel cell.
  * $\text{HAND} = z(x_{\text{road}}, y_{\text{road}}) - z(x_{\text{channel}}, y_{\text{channel}})$.

---

## 3. Road Segment HAND Pilot Census

Extracted from [`data/intermediate/hand_pilot_v4.csv`](file:///d:/datasets_IDM(ADAS)/data/intermediate/hand_pilot_v4.csv):

| Region | Road Segment ID | Road Elevation | Nearest Stream Elevation | HAND ($m$) | Historical Flood Target Rate |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Godavari_Lower** | `TGRAC_ARTERIAL_23` | 56.0 m | 48.0 m | **+8.0 m** | **0.80 (Exposed)** |
| **Godavari_Lower** | `TGRAC_HIGHWAY_44` | 58.0 m | 49.0 m | **+9.0 m** | **0.80 (Exposed)** |
| **Godavari_Lower** | `TGRAC_HIGHWAY_43` | 61.0 m | 47.0 m | **+14.0 m** | **0.80 (Exposed)** |
| **Godavari_Lower** | `TGRAC_HIGHWAY_45` | 84.0 m | 49.0 m | **+35.0 m** | 0.00 (Unexposed) |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1730`| 508.0 m | 510.0 m | **-2.0 m** | **0.75 (Exposed)** |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1731`| 511.0 m | 513.0 m | **-2.0 m** | **0.75 (Exposed)** |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1732`| 518.0 m | 509.0 m | **+9.0 m** | 0.00 (Unexposed) |
| **Manjira_Singur** | `TGRAC_HIGHWAY_322` | 607.0 m | 509.0 m | **+98.0 m** | 0.00 (Unexposed) |
| **Manjira_NizamSagar**| `TGRAC_COLLECTOR_452`| 400.0 m | 403.0 m | **-3.0 m** | 0.00 (Unexposed) |
| **Manjira_NizamSagar**| `TGRAC_HIGHWAY_25` | 410.0 m | 403.0 m | **+7.0 m** | 0.00 (Unexposed) |
| **Manjira_NizamSagar**| `TGRAC_HIGHWAY_355`| 443.0 m | 410.0 m | **+33.0 m** | 0.00 (Unexposed) |
| **Manjira_NizamSagar**| `TGRAC_HIGHWAY_79` | 442.0 m | 388.0 m | **+54.0 m** | 0.00 (Unexposed) |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_72` | 288.0 m | 272.0 m | **+16.0 m** | 0.00 (Unexposed) |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_423` | 287.0 m | 309.0 m | **-22.0 m** | 0.00 (Unexposed) |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_419` | 347.0 m | 309.0 m | **+38.0 m** | 0.00 (Unexposed) |
| **Krishna_Agraharam** | `TGRAC_ARTERIAL_9` | 331.0 m | 272.0 m | **+59.0 m** | 0.00 (Unexposed) |

---

## 4. Target Proxy Audit & Physical Analysis

### Distribution of Historical Target Rate by HAND Range:
* **$\text{HAND} < 10\text{ m}$ (Active Floodplain):** 52 observations, 28 exposed (**53.8% target rate**).
* **$\text{HAND} \in [10, 20\text{ m}]$ (Terrace / Secondary):** 14 observations, 8 exposed (**57.1% target rate**).
* **$\text{HAND} \in [20, 35\text{ m}]$ (Valley Margin):** 9 observations, 0 exposed (**0.0% target rate**).
* **$\text{HAND} \in [35, 50\text{ m}]$ (Upland Transition):** 4 observations, 0 exposed (**0.0% target rate**).
* **$\text{HAND} > 50\text{ m}$ (Plateau / Ridge):** 12 observations, 0 exposed (**0.0% target rate**).

### Crucial Diagnostic Findings:
1. **Low HAND is a Physical Prerequisite, Not a Label Proxy:**
   * Every single flood-exposed road segment in the entire dataset has $\text{HAND} \le 14.0\text{ m}$.
   * Roads with $\text{HAND} > 20\text{ m}$ have **zero historical flood events**.
   * However, $\text{HAND} \le 10\text{ m}$ **does NOT guarantee flood exposure**: in NizamSagar, `TGRAC_COLLECTOR_452` has $\text{HAND} = -3.0\text{ m}$ and `TGRAC_HIGHWAY_25` has $\text{HAND} = +7.0\text{ m}$, yet neither flooded because the river did not reach their reach during the monitored period.
2. **Does HAND Reconstruct the 2,500m Target Buffer?**
   * **No.** In NizamSagar and Agraharam, roads with low HAND lie 4 to 14 km away from the regional CWC river gauge. They were classified as unexposed because they were outside the active gauge flood corridor.
   * HAND provides genuine geomorphic valley clearance without leaking the horizontal circular buffer.
3. **Inference Feasibility:**
   * HAND is time-invariant. A pre-indexed 2D raster of HAND enables sub-millisecond in-vehicle lookup during navigation.
