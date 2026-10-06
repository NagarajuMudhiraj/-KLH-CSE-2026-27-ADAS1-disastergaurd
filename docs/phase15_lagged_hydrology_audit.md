# Phase 15 Lagged Hydrology & Upstream Dynamics Audit

**Document Version:** 1.0  
**Phase:** Phase 15 Representation & Dataset Expansion  
**Date:** 2026-09-30  
**Status:** **`FUTURE_PROVIDER`** (Sub-daily lagged telemetry not present in daily historical catalogs)

---

## 1. Conceptual Framework & Value Proposition

In riverine flood forecasting, downstream flood waves lag upstream conditions by several hours to days depending on channel hydraulic geometry and distance:
$$\text{Downstream Flood State}(t) = f\big(\text{Upstream Stage}(t - \Delta t), \ \text{Upstream Discharge } Q(t - \Delta t), \ \frac{\Delta h}{\Delta t}\big)$$

Where:
* $\Delta t$: Hydraulic wave travel time (typically 6 to 24 hours between upstream reservoirs/gauges and downstream road crossings).
* $\frac{\Delta h}{\Delta t}$: Rate of water level change (stage surge velocity).

If available, an upstream measurement taken 6 to 12 hours prior to the prediction time is a **legitimate predictive feature** that precedes downstream road exposure without target leakage.

---

## 2. Forensic Audit of Available Datasets

We audited all historical repositories in the project workspace to determine whether genuine sub-daily upstream time-series data exists:

| Source Repository | File Audited | Temporal Granularity | Variables Present | Sub-Daily Availability | Audit Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **CWC IndoFloods** | `floodevents_indofloods.csv` | Event-aggregated | `Start Date`, `End Date`, `Peak Flood Level`, `Peak Discharge Q`, `Time to Peak (days)` | **None (Event aggregates only)** | **Leakage Risk (Event Peak)** |
| **CWC IndoFloods** | `precipitation_variables_indofloods.csv`| Daily-aggregated | `T1d`, `T2d`, `T3d`, ..., `T10d` (Daily basin-averaged precipitation) | **None (Daily sums only)** | Valid daily antecedent precipitation |
| **CWC IndoFloods** | `catchment_characteristics_indofloods.csv`| Static geomorphic | Catchment area, slope, stream length, elevation | **Static (Time-invariant)** | Valid static catchment descriptors |
| **Open-Meteo Archive** | Historical Archive REST API | Hourly & Daily | Precipitation, temperature, wind, soil moisture | **Available for meteorology** | Does not contain river stage |
| **Central Water Commission** | India-WRIS / CWC Portal | Hourly telemetry | Real-time gauge level, reservoir outflow ($Q_{\text{out}}$) | **Available in live portal** | Requires live API key & credentials |

---

## 3. Scientific Integrity & Anti-Fabrication Ruling

1. **No Hourly Gauge Telemetry in Historical Catalog:**
   * The IndoFloods catalog provides summary statistics of historical floods (peak water level, peak discharge, event duration), but does **NOT** contain continuous hourly time-series readings for $t-6\text{h}$ or $t-12\text{h}$.
2. **Strict Prohibition Against Post-Event Summaries:**
   * The event's `Peak Flood Level` and `Peak Discharge Q` occurred *during* or *at the crest* of the flood event. Feeding peak event discharge into a model to predict whether the road is flood-exposed for that same event is a **severe direct target leakage**.
3. **No Synthetic Interpolation:**
   * Fabricating hypothetical hourly hydrographs by spline interpolation between daily entries would violate the core project principle of using 100% genuine source-backed data.

---

## 4. Architectural Contract & Future Provider Roadmap

The following hydrological features are formally defined in the V4 feature contract, but categorized strictly as **`FUTURE_PROVIDER`**:

| Feature Name | Intended Unit | Required Sampling | Integration Prerequisite | Real-Time Feasibility | Status |
| :--- | :---: | :---: | :--- | :---: | :---: |
| `upstream_stage_lag_6h_m` | meters | Hourly ($t-6\text{h}$) | Central Water Commission (CWC) Telemetry API | High (CWC automated sensor) | **FUTURE_PROVIDER** |
| `upstream_discharge_lag_6h_cumec`| $\text{m}^3/\text{s}$ | Hourly ($t-6\text{h}$) | State Irrigation Dept / Dam Gate Telemetry | Moderate (Reservoir outflow log) | **FUTURE_PROVIDER** |
| `stage_change_rate_6h_m_per_hr` | $\text{m}/\text{hr}$ | Hourly ($t \dots t-6\text{h}$) | Continuous automated river gauge API | High (Calculated from stage delta) | **FUTURE_PROVIDER** |

*These features will remain inactive until real-time CWC/India-WRIS telemetry is integrated.*
