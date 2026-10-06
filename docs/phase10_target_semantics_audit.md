# Phase 10 Target Semantics Audit: Ground-Truth Mechanics & Limitations

**Document Version:** 1.0  
**Phase:** Phase 10 Scaling & Dataset Hardening  
**Audit Date:** 2026-09-30  
**Artifacts Inspected:**
* `data/processed/road_risk_geospatial_pilot.csv`
* `pipeline/build_geospatial_pilot.py`
* `pipeline/audit_geospatial_pilot.py`
* `docs/road_risk_target_decision_v6.md`

---

## 1. Executive Summary & Core Finding

Phase 9 established the first real-data geospatial pilot ($N=32$) by joining Central Water Commission (CWC) historical flood event telemetry from INDOFLOODS (IIT Delhi) with authoritative road geometries from the Telangana Remote Sensing Applications Centre (TGRAC).

**Audit Finding:**  
The positive label in Phase 9 was named `target_flooded`. However, the underlying physical evidence **does not prove direct road-surface submersion** (e.g. water depth on pavement or vehicle stalling). Rather, the evidence establishes that **the road segment lies within an active hydrological flood-hazard corridor during an officially declared river flood stage**.

Therefore, calling the target `FLOODED` is an overstatement of the empirical evidence. For Phase 10 and all future ML pipelines, the target must be formally designated as:
$$\text{target\_flood\_exposure} \in \{0, 1\}$$
where:
* `1` = `FLOOD_EXPOSED`
* `0` = `NOT_EXPOSED`

---

## 2. Line-by-Line Mechanics of Target Generation in Phase 9

In [`pipeline/build_geospatial_pilot.py`](file:///d:/datasets_IDM(ADAS)/pipeline/build_geospatial_pilot.py#L180-L198), the target was generated through the following deterministic logic:

```python
dist_m = min_distance_to_line(ev['gauge_lat'], ev['gauge_lon'], r['coords'])
is_near_flood = (dist_m <= 2500.0)

if ev['is_flood_period'] and is_near_flood:
    target_flooded = 1
    label_reason = f"Road segment {r['road_id']} is within {dist_m:.0f}m of active CWC flood reach during confirmed {ev['flood_stage']} (stage >= Warning Level)."
elif ev['is_flood_period'] and not is_near_flood:
    target_flooded = 0
    label_reason = f"Road segment {r['road_id']} is {dist_m:.0f}m from active CWC flood reach (outside riparian inundation corridor) during {ev['flood_stage']}."
else:
    target_flooded = 0
    label_reason = f"Observed during confirmed non-flood baseline period ({ev['event_date']}); normal river stage well below Warning Level."
```

### Component Analysis

| Factor | Implementation in Phase 9 | Exact Operational Dependency |
|---|---|---|
| **Actual Flood Polygon** | **Indirect / Catchment-scale only**. Catchment boundaries exist in INDOFLOODS (`catchments_shapefiles_indofloods.zip`), but local dynamic inundation rasters (e.g., 2D flood depth rasters) do not exist for 2006–2019 events. | Does not depend on high-resolution 2D dynamic flood polygons. |
| **River / Gauge Proximity** | **Directly Dependent**. Minimum geodesic distance calculated from road polyline coordinates to the CWC river gauging station (`dist_m`). | `dist_m <= 2500.0` meters. |
| **CWC Warning Level** | **Directly Dependent**. When river water level exceeds the station-specific Warning Level (e.g., 45.72 m at Bhadrachalam, 523.60 m at Singur Dam). | Condition for `is_flood_period = True`. |
| **CWC Danger Level** | **Recorded as severity tier**, but not a binary gate. "Severe Flood" indicates water level exceeded Danger Level. | Used in `label_reason` and metadata, but Warning Level initiates positive candidate status. |
| **Flood Event Existence** | **Directly Dependent**. Event must exist in INDOFLOODS catalog with verified start/end dates. | Observation dates are matched strictly to verified event dates. |
| **Fixed Spatial Buffer** | **Yes: 2,500-meter riparian corridor**. | Any road segment whose polyline passes within 2.5 km of the overflowing gauging reach during the event window is classified as exposed. |
| **Negative Control Mechanics** | **Two Independent Controls**: <br>1. *Spatial Negative Control*: Road segments $>2,500\text{ m}$ away during an active flood ($Target=0$). <br>2. *Temporal Negative Control*: Identical road segments observed during confirmed dry-season non-flood dates ($Target=0$). | Prevents trivial overfitting or correlation with fixed road properties. |

---

## 3. Evidence Classification: Proximity Proxy vs Direct Flood Evidence

1. **Why It is a `PROXIMITY_PROXY` / `HYDROLOGICAL_PROXY`:**
   * Central Water Commission (CWC) telemetry confirms that the river cross-section overflowed its banks (stage above warning/danger level).
   * Geospatial computation confirms that the road segment is within the immediate riparian corridor ($<2.5\text{ km}$).
   * However, without LiDAR-derived digital surface models of the road embankment height or in-situ road CCTV cameras, we cannot guarantee every square meter of asphalt was submerged. High road embankments or bridge superstructures may remain dry while the surrounding floodplain is inundated.
2. **Scientific Integrity Standard:**
   * Describing the label as `FLOODED` creates a false impression of direct pavement-level water depth sensing.
   * Describing the label as `FLOOD_EXPOSED` is 100% accurate: the road traverses an active fluvial flood hazard corridor.
3. **ADAS Operational Reality:**
   * In automotive ADAS routing, exposing a vehicle to an active riverine flood hazard corridor is a critical risk state triggering preventive rerouting, regardless of whether the water is 5 cm or 50 cm deep.
