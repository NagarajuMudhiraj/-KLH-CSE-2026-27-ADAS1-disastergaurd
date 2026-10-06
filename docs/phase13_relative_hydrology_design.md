# Phase 13 Relative Hydrology & Topographic Representation Design

**Document Version:** 1.0  
**Phase:** Phase 13 Feature Representation Redesign  
**Date:** 2026-09-30  
**Context:** Phase 12 proved that absolute elevation (`elevation_m`) failed cross-basin transfer because flood-exposed roads in Godavari Lower lie at 56–61 m, whereas flood-exposed roads in Manjira Singur lie at 508–511 m. A tree model trained on absolute elevation learned an elevation split at $<65\text{ m}$ and predicted 0.0% flood exposure for all Singur plateau roads (Recall = 0.0%).

---

## 1. Evaluation of Alternative Elevation Representations

We evaluated four alternative topographic representations to replace absolute elevation:

| Evaluation Criterion | Option A: Height Above Nearest Drainage (HAND) | Option B: Static Relative Channel Elevation ($\Delta z_{\text{channel}}$) | Option C: Local Drainage Window Elevation ($\Delta z_{\text{basin}}$) | Option D: Intra-Basin Elevation Percentile Rank |
| :--- | :--- | :--- | :--- | :--- |
| **Mathematical Definition** | Elevation difference between surface point and the hydrologically connected flowline cell in a drainage network. | $\Delta z = z_{\text{road}} - z_{\text{channel\_datum}}$ where $z_{\text{channel\_datum}}$ is the DEM elevation of the regional river cross-section / gauge site. | $\Delta z = z_{\text{road}} - \min_{x \in B(5\text{km})} z(x)$ | Percentile rank $P(z_{\text{road}})$ within the distribution of all road elevations in the regional basin. |
| **Physical Meaning** | Direct vertical distance above the hydraulic drainage base. | Height of the road embankment/segment above the regional riverbed/gauge datum. | Height above the lowest point in a local 5 km moving topographic window. | Relative rank of the road within regional topography. |
| **Available Data Sources** | Global MERIT-Hydro (90m) or Copernicus GLO-30 flow accumulation rasters. | Copernicus GLO-30 DEM at road centroid and CWC gauge coordinates (Open-Meteo Elevation API). | Copernicus GLO-30 DEM local radial sampling. | Calculated from road DEM distribution in dataset. |
| **Reproducibility** | Moderate (requires multi-gigabyte D8 flow-routing rasters). | **High (100% reproducible via standard DEM coordinates).** | Moderate (depends on window size parameter). | Low (sensitive to which roads are sampled in the dataset). |
| **Historical Consistency** | Static terrain property (time-invariant). | **Static terrain property (time-invariant).** | Static terrain property. | Dataset-dependent. |
| **Real-Time Feasibility** | Requires pre-indexed HAND grid lookup by GPS. | **Trivially computable by subtracting nearest river reach DEM datum.** | Requires local DEM grid query. | Requires maintaining regional road percentile tables. |
| **Leakage Risk** | **Zero leakage.** | **Zero leakage (as long as static channel datum is used, NOT dynamic water level).** | Zero leakage. | Possible sampling leakage. |
| **Selection Verdict** | **Long-term Target** | **Selected for V3 Implementation** | Alternative candidate | Rejected (non-physical) |

---

## 2. Selection Rationale for Option B: Relative Channel Elevation

Option B ($\Delta z_{\text{channel}} = z_{\text{road}} - z_{\text{gauge\_datum}}$) is selected for the V3 model architecture for the following reasons:

1. **Physical Soundness:** Riverine flooding is governed by the stage rise above the channel bank:
   $$\text{Inundation Condition} \approx h(t) \ge \Delta z_{\text{channel}}$$
   A road at $\Delta z = 15\text{ m}$ above the riverbed faces comparable exposure risks across all river basins, regardless of whether the river is at sea level (Bhadrachalam: $z_{\text{datum}} = 33.0\text{ m}$) or in an upland plateau (Singur: $z_{\text{datum}} = 521.0\text{ m}$).
2. **Eliminates Absolute Elevation Confounding:**
   * In Godavari Lower: Road elevations range from 56.0 m to 84.0 m. Relative to the channel datum ($33.0\text{ m}$), $\Delta z$ ranges from **$+23.0\text{ m}$ to $+51.0\text{ m}$**. The exposed roads are at $+23\text{ m}$, $+25\text{ m}$, and $+28\text{ m}$.
   * In Manjira Singur: Road elevations range from 508.0 m to 607.0 m. Relative to the channel datum ($500.0\text{ m}$), $\Delta z$ ranges from **$+8.0\text{ m}$ to $+107.0\text{ m}$**. The exposed roads are at $+8\text{ m}$ and $+11\text{ m}$.
   * Both basins share a common physical threshold: roads with $\Delta z < 30\text{ m}$ lie in the active fluvial flood hazard zone, whereas roads with $\Delta z > 50\text{ m}$ are upland plateaus.
3. **Inference Feasibility:** In an onboard ADAS or routing backend, the vehicle's relative elevation above the nearest major riverbed can be queried via a static pre-computed riverbed profile, without requiring dynamic raster flow simulation.

---

## 3. Leakage & Spatial Confounding Audit

### Critical Rule on River Reference Datum
> **CRITICAL REQUIREMENT:**  
> The reference datum $z_{\text{gauge\_datum}}$ must be a **static topographic/hydrological elevation** (the ground surface elevation of the river channel/gauge point from Copernicus GLO-30 DEM).  
> It must **NEVER** be set to the event's dynamic water level ($h(t)$) or the flood stage threshold ($h_{\text{warning}}$).

### Spatial Confounding Check
The target label $\text{target\_flood\_exposure}$ was defined using $\text{distance} \le 2,500\text{ m}$ from the gauge. Does $\Delta z_{\text{channel}}$ encode this exact spatial rule?
* **Audit:** No. A road can be very close to the river ($<1,000\text{ m}$) but situated on a high cliff or plateau ($\Delta z > 60\text{ m}$), remaining unexposed. Conversely, a road 2,000 m away in a wide, flat alluvial floodplain can have $\Delta z = 10\text{ m}$.
* In our dataset:
  * `TGRAC_HIGHWAY_45` in Godavari is 11.5 km away with $\Delta z = +51.0\text{ m}$.
  * `TGRAC_HIGHWAY_322` in Singur is 14.3 km away with $\Delta z = +107.0\text{ m}$.
  * Unexposed roads have high $\Delta z$, matching physical intuition.
* Therefore, $\Delta z_{\text{channel}}$ captures vertical topographic clearance rather than horizontal distance to the gauge.
