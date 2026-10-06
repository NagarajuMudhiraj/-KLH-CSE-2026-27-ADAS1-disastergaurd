# Road Risk Target Decision Framework (v6)

**Document Version:** 6.0  
**Phase:** Phase 9 Geospatial Road-Flood Pilot  
**Date:** 2026-09-30  
**Scope:** Rigorous evaluation of target definitions for real-data road risk modeling in ADAS.

---

## 1. Executive Summary

In Phase 8, synthetic target generation and heuristic fallback formulas (e.g. `risk_score = rainfall * ... + traffic * ... + water_level * ...`) were permanently deprecated. Phase 9 requires establishing the target variable based **solely on what the real data sources actually justify**, without forcing unsupported 3-class distinctions.

Following an exhaustive audit of:
1. **INDOFLOODS** (IIT Delhi / HydroSense Lab, Central Water Commission streamflow data)
2. **TGRAC GIS Services** (Telangana Remote Sensing Applications Centre)
3. **Open-Meteo Historical Reanalysis Archive**

We systematically evaluated four candidate target semantics. The conclusion is unambiguous:
**The only target genuinely supported by the empirical evidence is Option A: Binary Flood Exposure (`target_flooded`: 0 or 1).**

---

## 2. Comparative Evaluation Matrix

| Target Option | Empirical Source Evidence | Label Independence | Real-Time ADAS Meaning | Defensibility & Limitations | Decision |
|---|---|---|---|---|---|
| **A. Flood Exposure Binary** (`FLOODED` / `NOT_FLOODED`) | CWC hydrological gauge level exceeding official Warning / Danger thresholds during active flood dates + spatial proximity/intersection with road geometry. | **High (Independent)**: Derived from river gauge telemetry and geospatial topology; completely independent of meteorological features and model inputs. | Clear operational hazard gate: informs ADAS whether the road segment is exposed to an active fluvial inundation corridor. | **High Academic & Practical Rigor**: Avoids unverified assumptions about vehicle traversability or barricades. Fully reproducible from open government sources. | **RECOMMENDED & ADOPTED for Phase 9 Pilot & Scaling** |
| **B. Continuous Flood Exposure Ratio** (0.0 to 1.0) | Continuous polyline intersection length divided by total road segment length, or buffer decay. | **High (Independent)**: Purely geometrical calculation. | Degree of roadway segment physical submergence. | **Moderate**: Requires fine-resolution 2D hydrodynamic flood rasters (e.g. HEC-RAS hydraulic models), which are unavailable for historical events across Telangana. As a target, continuous values are difficult to threshold safely for ADAS brake/abort decisions. | **REJECTED**: Insufficient raster resolution in verified sources. |
| **C. SAFE / RISKY / BLOCKED Proxy** (3-Class) | CWC Warning Level (classified as "Flood") vs Danger Level (classified as "Severe Flood"). Normal baseline = SAFE. | **Moderate**: Stage thresholds are independent, but the class mapping is heuristic. | Assumes Warning = RISKY (passable with caution) and Danger = BLOCKED (impassable). | **Weak / Defective**: Fails real-world validation. A high-embankment highway may remain completely open during a "Severe Flood", while an unpaved road may be blocked during minor waterlogging. Assigning "BLOCKED" without physical closure reports is scientifically indefensible. | **REJECTED**: Forcing 3 classes without ground-truth closures violates ADAS data policy. |
| **D. Actual Road Closure Status** (`CLOSED`, `LANE_RESTRICTION`, `OPEN`) | Official police blotters, Department of Transportation closure notices, or emergency incident feeds. | **High (Independent)**: True operational status of the road network. | Gold standard for ADAS routing: absolute confirmation that the roadway is impassable. | **Unavailable**: Neither INDOFLOODS nor TGRAC provides timestamped historical road-closure incident logs. External candidates (DriveBC, Australia NFDH, Ottawa) were audited in Phase 7 and rejected due to lack of historical depth or out-of-domain geography. | **UNAVAILABLE**: Zero historical rows available in verified Telangana feeds. |

---

## 3. Deep Dive into Target Semantics

### Why Binary Flood Exposure is Defensible
1. **Source Integrity:** Central Water Commission (CWC) warning and danger levels are established through decades of engineering hydrology for every river cross-section in India. When the water level exceeds the warning level at Bhadrachalam (45.72 m) or Singur Dam (523.60 m), river overflow is an observed physical reality, not a simulation.
2. **Spatial Correlation:** By joining TGRAC road geometry with the flood reach coordinates, we distinguish roads that directly traverse the flood plain from roads situated high on ridges or tens of kilometers inland.
3. **No Leakage:** Meteorological features (rainfall, temperature, wind) and physical features (elevation, road type) serve as predictive inputs. The target is established by hydrological stage and spatial proximity, guaranteeing zero label-feature leakage.
4. **ADAS Functionality:** For an autonomous vehicle or advanced driver assistance system, knowing with high confidence whether a road segment enters an active fluvial flood zone is the fundamental requirement for rerouting or issuing critical driver takeover requests.

### Why 3-Class (SAFE/RISKY/BLOCKED) is Permanently Rejected for This Data
In synthetic datasets, creating three classes (`Safe=0, Risky=1, Blocked=2`) is trivial because synthetic formulas can arbitrarily partition risk scores. In real physical systems, however, claiming a road is `BLOCKED` requires evidence of complete obstruction (e.g., water depth > 300 mm, physical road closure, or traffic stoppage). 

Because our real sources do not contain vehicle-specific submersion depths or barrier logs, promoting a proxy 3-class target would replicate the fundamental flaws of earlier iterations.

---

## 4. Final Policy Decision

1. **Adopt Binary Target:** All real-world geospatial training and evaluation datasets in the ADAS pipeline will formulate the primary classification target as:
   $$\text{target\_flooded} \in \{0, 1\}$$
   Where:
   * `1` = `FLOODED` (Road segment is within the active fluvial flood inundation corridor during a confirmed CWC flood event).
   * `0` = `NOT_FLOODED` (Road segment is outside the flood corridor during an event, or observed during confirmed dry baseline periods).
2. **Label Governance:** No heuristic rules based on rainfall, wind, or synthetic risk scores may generate or alter this label.
3. **Future Extensibility:** If authoritative historical road-closure logs (e.g., Highway Police incident databases) are acquired in future phases, a secondary operational closure target (`target_closed`) may be introduced as a multi-task head alongside `target_flooded`.
