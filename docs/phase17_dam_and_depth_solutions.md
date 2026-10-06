# Technical Specification: Solving Dam-Release Floods & Pavement Water Depth (Phase 17)

**Document Version:** 1.0.0  
**Phase:** Phase 17 — Dual-Hazard Integration & Pavement Depth Formulation  
**Date:** 2026-09-30  
**Status:** IMPLEMENTED_AND_VALIDATED  

---

## 1. Executive Summary

In Phase 16, two critical operational limitations were diagnosed:
1. **The "Sunny-Day Dam Release" Limitation:** In dam-regulated river basins (e.g. Singur Dam on the Manjira), severe flooding can occur when upstream dam spillway gates are opened under dry, zero-rainfall conditions. Weather-only machine learning models predict $0$ on dry days, leading to $0\%$ cross-basin recall when transferred from natural rain-fed basins to dam-controlled basins.
2. **Binary Corridor Exposure vs. Physical Asphalt Submergence:** The previous target (`target_flood_exposure`) only indicated whether a road was within $2,500\text{ m}$ of an overflowing river reach. It did not calculate the physical water depth on the pavement or advise whether a vehicle can safely drive through.

This specification documents the successful implementation of the two solutions in [`data/processed/road_risk_dataset_v10.csv`](file:///d:/datasets_IDM(ADAS)/data/processed/road_risk_dataset_v10.csv) and [`pipeline/evaluate_dual_hazard_v5.py`](file:///d:/datasets_IDM(ADAS)/pipeline/evaluate_dual_hazard_v5.py).

---

## 2. Solution 1: Dual-Hazard Architecture for Dam Releases

### 2.1 The Hydrological Mismatch
* In natural river systems (e.g., Godavari at Bhadrachalam), flood exposure is governed strictly by **Catchment Hydrometeorology** (heavy precipitation $\rightarrow$ runoff $\rightarrow$ river crest).
* In regulated reservoir basins (e.g., Singur Dam, Nizam Sagar), downstream water level is governed by **Human Gate Operation**. On June 2, 2019 (Event `INDOFLOODS-gauge-916-1`), Singur Dam discharged water because its pool was at $544.59\text{ m}$ (danger level is $523.60\text{ m}$), inundating roads despite $0.0\text{ mm}$ of rain.

### 2.2 Dual-Hazard Decision Gate
To reconcile these physically distinct regimes, the ADAS hazard logic integrates a **Dual-Hazard Logical Gate**:

$$\hat{Y}_{\text{ADAS}} = \hat{Y}_{\text{weather\_ML}} \;\lor\; \left(\text{Dam\_Release\_Alert} \land \text{HAND} \le 5.0\text{ m}\right)$$

Where:
* $\hat{Y}_{\text{weather\_ML}}$: Risk prediction from the XGBoost ML model based on antecedent rainfall, climatological anomalies, and soil moisture.
* $\text{Dam\_Release\_Alert}$: Telemetry signal or official irrigation department bulletin indicating active reservoir spillway discharge ($H_{\text{reservoir}} \ge H_{\text{danger}}$).
* $\text{HAND} \le 5.0\text{ m}$: Geomorphic filter ensuring only roads situated inside the low-lying downstream discharge channel are flagged, leaving upland roads safe.

### 2.3 Empirical Cross-Basin Impact (Fold B)
When evaluated on Singur Dam flood events transferred from Godavari:
* **Previous V3 / V4 Recall:** **0.0%** (Missed all dam flood events).
* **Dual-Hazard Architecture Recall:** **100.0%** (Detected all 6 flooded roads).
* **Accuracy:** **100.0%** ($\text{TP}=6, \text{TN}=10, \text{FP}=0, \text{FN}=0$).

---

## 3. Solution 3: Physical Pavement Water Depth & ADAS Safety Tiers

### 3.1 Hydraulic Formulation
Instead of an abstract binary corridor flag, we derive the exact continuous pavement water depth ($D_{\text{pavement}}$ in centimeters) using open-channel hydraulics:

$$D_{\text{pavement}} = \max\left(0.0, \, H_{\text{river\_surge}} - \max(0.0, \text{HAND})\right) \times 100$$

Where:
* $H_{\text{river\_surge}} = Z_{\text{crest}} - Z_{\text{drainage\_bed}}$: Height of river water surface above the channel thalweg (in meters).
* $\text{HAND} = Z_{\text{road}} - Z_{\text{drainage\_bed}}$: Road surface elevation clearance above the channel thalweg (in meters).

If $H_{\text{river\_surge}} > \text{HAND}$, riverine water physically overtops the banks and covers the road surface to a depth of $H_{\text{river\_surge}} - \text{HAND}$ meters.

### 3.2 Actionable ADAS Automotive Safety Tiers

| Tier Name | Pavement Water Depth ($D$) | Physical Meaning | ADAS / Vehicle Action |
| :--- | :---: | :--- | :--- |
| **`DRY_PASSABLE`** | $0.0\text{ cm}$ | Road surface is physically above flood crest level. | Normal vehicle operation. No warnings. |
| **`SHALLOW_CAUTION`** | $1.0\text{–}15.0\text{ cm}$ | Shallow standing water / splash hazard. | Display driver caution alert; reduce advisory speed to $<40\text{ km/h}$. |
| **`HIGH_RISK_STALL`** | $15.1\text{–}30.0\text{ cm}$ | Water level approaches standard vehicle air intake / exhaust height. | Severe audio-visual warning; advise against entry; deactivate cruise control. |
| **`IMPASSABLE_SUBMERGED`** | $> 30.0\text{ cm}$ | Vehicle buoyancy threshold exceeded; high risk of engine flooding or vehicle being swept away. | **Re-route navigation immediately**; initiate automatic safe braking if vehicle approaches hazard point. |

---

## 4. Empirical Breakdown across Dataset V10 ($N=68$)

* **`DRY_PASSABLE` ($0\text{ cm}$):** **52 observations** (76.5%)
* **`IMPASSABLE_SUBMERGED` ($>30\text{ cm}$):** **16 observations** (23.5%)
  - Bhadrachalam low-lying roads during peak monsoons experienced water depths from $1.7\text{ m}$ to $35.8\text{ m}$ above asphalt.
  - Singur downstream floodplain roads during dam gate opening experienced water depths from $3.0\text{ m}$ to $5.0\text{ m}$.
  - Upland roads (e.g. `TGRAC_HIGHWAY_45` with $\text{HAND} = 35\text{ m}$) remained $0\text{ cm}$ dry even while nearby lowland roads were deeply submerged.

---

## 5. Verification & Test Suite

Validated in:
* [`pipeline/evaluate_dual_hazard_v5.py`](file:///d:/datasets_IDM(ADAS)/pipeline/evaluate_dual_hazard_v5.py)
* [`tests/test_phase17_representation_v5.py`](file:///d:/datasets_IDM(ADAS)/tests/test_phase17_representation_v5.py)
* Output Artifact: [`models/road_risk_v4/phase17_dual_hazard_results.json`](file:///d:/datasets_IDM(ADAS)/models/road_risk_v4/phase17_dual_hazard_results.json)
