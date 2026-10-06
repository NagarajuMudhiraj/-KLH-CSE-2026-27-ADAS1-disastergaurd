# Phase 12 Target Generation Audit: Ground-Truth Mechanics & Proxy Risks

**Document Version:** 1.0  
**Phase:** Phase 12 Generalization & Proxy Audit  
**Audit Date:** 2026-09-30  
**Artifacts Audited:**
* `pipeline/build_dataset_v7.py` (lines 220–240)
* `pipeline/build_geospatial_pilot.py` (lines 180–200)
* `pipeline/audit_dataset_v7.py`
* `docs/phase10_target_semantics_audit.md`
* `data/processed/road_risk_dataset_v7.csv`

---

## 1. Executive Summary

In Phase 11, the XGBoost V2 model achieved 87.5% test accuracy on an event-held-out split. However, an ablation test demonstrated that **Road-Only features (excluding all weather features) achieved 100% accuracy**.

This audit inspects the mathematical and spatial mechanics of how `target_flood_exposure` is computed in `road_risk_dataset_v7.csv` to establish why static road features showed such artificially inflated predictive power.

**Core Diagnostic Finding:**  
`target_flood_exposure` is computed deterministically from two components:
$$\text{target\_flood\_exposure} = \mathbf{1}_{[\text{is\_flood\_event} == \text{True}]} \times \mathbf{1}_{[\text{distance\_to\_gauge} \le 2500\text{m}]}$$

Because the gauging station coordinates for each region are fixed, `distance_to_gauge` is a **static spatial constant** for each road segment. Across all 16 road segments in the dataset:
* Exactly **5 road segments** have $\text{distance\_to\_gauge} \le 2,500\text{ m}$.
* The remaining **11 road segments** have $\text{distance\_to\_gauge} > 2,500\text{ m}$.

When evaluating on test splits where the same 16 roads recur, tree models simply use static road attributes (`elevation_m`, `road_length_m`, `road_type`) as unique fingerprints to memorize which 5 roads are within 2.5 km of the river gauge.

---

## 2. Line-by-Line Mechanics of Target Generation

In `pipeline/build_dataset_v7.py` (lines 220–239), the target label is assigned as follows:

```python
dist_m = min_distance_to_line(ev['gauge_lat'], ev['gauge_lon'], r['coords'])
road_length_m = round(r['length_km'] * 1000.0, 1)

is_near = (dist_m <= 2500.0)
if ev['is_flood'] and is_near:
    target = 1
    evidence_type = "PROXIMITY_PROXY"
    reason = (f"Road segment {r['road_id']} is within {dist_m:.0f}m of active CWC flood reach "
              f"during confirmed {ev['flood_stage']} (stage {ev['water_level_m']}m >= Warning {ev['warning_level_m']}m).")
elif ev['is_flood'] and not is_near:
    target = 0
    evidence_type = "SPATIAL_NEGATIVE_CONTROL"
    reason = (f"Road segment {r['road_id']} is {dist_m:.0f}m from active CWC flood reach "
              f"(outside riparian inundation corridor) during {ev['flood_stage']}.")
else:
    target = 0
    evidence_type = "TEMPORAL_NEGATIVE_CONTROL"
    reason = (f"Observed during confirmed non-flood baseline period ({ev['event_date']}); "
              f"normal river stage {ev['water_level_m']}m below Warning Level {ev['warning_level_m']}m.")
```

### Component Breakdown

| Parameter / Factor | Operational Definition | Exact Rule in Code |
| :--- | :--- | :--- |
| **Gauge Stage Condition** | CWC observed hydrological water level at the regional gauge. | `ev['water_level_m'] >= ev['warning_level_m']` |
| **Warning Threshold** | CWC designated threshold for bankfull stage. | Bhadrachalam: 45.72 m<br>Singur Dam: 523.60 m<br>NizamSagar: 428.24 m<br>Agraharam: 281.00 m |
| **Danger Threshold** | CWC severe flood stage threshold. | Logged in metadata (`flood_stage = 'Severe Flood'`), but `Warning Level` initiates candidate exposure. |
| **Event Condition (`is_flood`)** | Binary boolean flag denoting whether observation date falls inside a verified flood event. | `True` for historical flood peaks (2005–2022); `False` for dry-season baseline controls (`2019-03-15`). |
| **Distance Calculation (`dist_m`)** | Minimum geodesic distance from road polyline coordinates to CWC gauge coordinates. | Haversine distance from all vertices in `r['coords']` to `(ev['gauge_lat'], ev['gauge_lon'])`. |
| **Spatial Buffer** | 2,500-meter fixed riparian flood corridor buffer. | `is_near = (dist_m <= 2500.0)` |
| **Spatial Negative Control** | Road observed during active flood event, but located $>2,500\text{ m}$ away. | $Target = 0$, `evidence_type = SPATIAL_NEGATIVE_CONTROL`. |
| **Temporal Negative Control** | Road observed during confirmed dry baseline dates. | $Target = 0$, `evidence_type = TEMPORAL_NEGATIVE_CONTROL`. |

---

## 3. Road-by-Road Proximity & Label Breakdown

Below is the complete census of all 16 road segments in `road_risk_dataset_v7.csv` and their static relation to the 2,500 m threshold:

| Region | Road Segment ID | Elevation | Length | Road Type | Distance to Gauge | Total Obs | Exposed Obs ($Y=1$) | Target Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Godavari_Lower** | `TGRAC_ARTERIAL_23` | 56.0 m | 1,303.8 m | arterial | **1,778.2 m** | 5 | 4 | **0.80** |
| **Godavari_Lower** | `TGRAC_HIGHWAY_43` | 61.0 m | 5,314.5 m | highway | **1,071.8 m** | 5 | 4 | **0.80** |
| **Godavari_Lower** | `TGRAC_HIGHWAY_44` | 58.0 m | 18,163.0 m | highway | **1,205.6 m** | 5 | 4 | **0.80** |
| **Godavari_Lower** | `TGRAC_HIGHWAY_45` | 84.0 m | 8,520.0 m | highway | 11,541.2 m | 5 | 0 | 0.00 |
| **Krishna_Agraharam** | `TGRAC_ARTERIAL_9` | 331.0 m | 5,456.8 m | arterial | 7,178.4 m | 4 | 0 | 0.00 |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_419` | 347.0 m | 12,396.9 m | highway | 12,225.2 m | 4 | 0 | 0.00 |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_423` | 287.0 m | 6,128.9 m | highway | 14,738.4 m | 4 | 0 | 0.00 |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_72` | 288.0 m | 19,094.2 m | highway | 14,282.3 m | 4 | 0 | 0.00 |
| **Manjira_NizamSagar** | `TGRAC_COLLECTOR_452` | 400.0 m | 3,470.8 m | collector | 4,638.9 m | 4 | 0 | 0.00 |
| **Manjira_NizamSagar** | `TGRAC_HIGHWAY_25` | 410.0 m | 6,968.7 m | highway | 5,752.7 m | 4 | 0 | 0.00 |
| **Manjira_NizamSagar** | `TGRAC_HIGHWAY_355` | 443.0 m | 7,562.0 m | highway | 6,823.3 m | 4 | 0 | 0.00 |
| **Manjira_NizamSagar** | `TGRAC_HIGHWAY_79` | 442.0 m | 11,297.7 m | highway | 8,900.9 m | 4 | 0 | 0.00 |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1730` | 508.0 m | 80.4 m | collector | **619.9 m** | 4 | 3 | **0.75** |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1731` | 511.0 m | 1,321.6 m | collector | **678.2 m** | 4 | 3 | **0.75** |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1732` | 518.0 m | 600.9 m | collector | 6,035.6 m | 4 | 0 | 0.00 |
| **Manjira_Singur** | `TGRAC_HIGHWAY_322` | 607.0 m | 8,709.0 m | highway | 14,293.0 m | 4 | 0 | 0.00 |

### Observations from Census:
1. Exactly 5 road segments have positive labels (`pos_rate = 0.75` or `0.80`). For each of these 5 roads, the label is `1` for all flood events and `0` for the dry baseline event.
2. The remaining 11 road segments are strictly `0` across every event (both flood events and baseline events).
3. Therefore, within any test split consisting exclusively of flood events, **the label is identical to `is_near`**. Any tree classifier that can split on `elevation_m` or `road_length_m` will achieve 100% accuracy without referencing weather inputs.

---

## 4. Key Limitations of the Target Labeling Architecture

1. **Static Buffer Proxy:** The 2,500 m buffer is static. In reality, a road 1,000 m away might be protected by flood dykes, while a culvert 3,000 m away might be submerged by backwater pooling.
2. **Binary River Threshold:** The CWC Warning Level triggers the event flag for the entire region. It does not model hydrodynamic flood wave propagation across individual hours.
3. **No Direct Pavement Sensors:** As established in Phase 10, the target is `target_flood_exposure` (corridor-level exposure), NOT direct road inundation depth.
