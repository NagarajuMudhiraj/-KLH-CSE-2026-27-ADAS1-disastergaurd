# Road Risk Label Definition
**ADAS — Intelligent Vehicle Assistance During Disasters**
**Document version:** 2.0 | **Phase:** 2 | **Status:** AUTHORITATIVE

---

## Purpose

This document defines the three road-risk classes used as targets for the XGBoost road-risk classification model. The definitions are **operational and measurable**. They must NOT be derived directly from any single environmental variable (such as rainfall or traffic alone). The label must represent an **independently verifiable road condition** that a driver, authority, or sensor system could observe without knowing the feature values in advance.

---

## Design Principles

1. **Independence from features.** The target must be obtainable from a source other than the features that predict it. A label derived from the same formula as the features creates circular leakage.
2. **Operational meaning.** Each class must correspond to a decision a driver can physically act on.
3. **Measurable.** Each class must be verifiable against at least one independent evidence source.
4. **No chasing a target accuracy.** Thresholds are set by road safety physics, not by desired model performance.

---

## Class Definitions

### CLASS 0 — SAFE

**Definition:** The road segment is fully passable under normal driving behaviour. No physical obstruction, active hazard, or exceptional environmental condition prevents safe travel at or near the posted speed limit.

**Operational criteria (ALL must be true):**

| Criterion | Measurable condition |
|---|---|
| No physical blockage | No debris, flood water, collapsed structure, or landslide crosses any lane |
| No active authorities closure | No official road closure notice for the segment from government/road authority |
| Visibility adequate | Visibility > 200 m |
| Surface draining | No standing water depth exceeding 5 cm on the carriageway |
| No confirmed hazard reports | Zero active hazard events within 500 m in last 30 min |
| Traffic moving | Average segment speed > 30% of posted speed limit |

**Independent evidence sources:**
- Road authority closure API (NHAI, State PWD)
- Flood monitoring station: water depth < 5 cm at road-level gauge
- Crowdsourced incident reports: zero within 500 m
- YOLO: no flood/fire/smoke/road-damage objects at confidence >= 0.4

---

### CLASS 1 — RISKY

**Definition:** The road segment is physically passable but requires heightened driver attention and reduced speed. At least one degrading condition is present that significantly increases crash or stranding risk.

**Operational criteria (at least ONE must be true):**

| Criterion | Measurable condition |
|---|---|
| Reduced visibility | 50 m < Visibility <= 200 m |
| Surface water present | 5-20 cm standing water on carriageway |
| Active hazard within 500 m | Confirmed incident report present but not blocking full cross-section |
| Heavy traffic under disaster | Traffic level >= 7.5/10 with concurrent rainfall >= 15 mm/h |
| Strong crosswind | Wind speed >= 60 km/h |
| Road damage detected | YOLO detects potholes/cracks not covering full lane |
| Braking anomaly cluster | >= 3 vehicles in 2-min window reporting emergency braking on same segment |

**Independent evidence sources:**
- Flood monitoring station: water depth 5-20 cm
- Meteorological service: visibility <= 200 m or wind >= 60 km/h
- YOLO: medium-severity events present
- Crowdsource: 1-2 incident reports within 500 m

---

### CLASS 2 — BLOCKED

**Definition:** The road segment is impassable. Any vehicle attempting to traverse the segment will be physically stopped, become stranded, or suffer an unrecoverable condition.

**Operational criteria (ANY ONE is sufficient):**

| Criterion | Measurable condition |
|---|---|
| Full cross-section inundation | Standing water depth > 20 cm across entire lane width |
| Official road closure declared | Government/road authority formal closure notice |
| Structural failure | Bridge, overpass, or embankment collapse |
| Landslide/debris blocking all lanes | Physical mass blocking 100% of carriageway |
| Fire on or immediately adjacent to road | Active fire within 20 m of carriageway |
| Visibility near-zero | Visibility < 50 m |
| Complete traffic standstill >= 10 min | Segment speed = 0 km/h for 10+ consecutive minutes |

**Independent evidence sources:**
- Official closure notices: road authority API, emergency services broadcast
- Flood monitoring station: water depth > 20 cm
- YOLO: critical-severity flood/fire/landslide detection
- GPS/probe data: zero movement for >= 10 min
- Satellite imagery (ex-post validation): Sentinel flood maps

---

## What This Definition Explicitly Excludes

| Excluded single-variable rule | Reason |
|---|---|
| if rainfall > 100 mm/h → Blocked | Heavy rain does not automatically block every road |
| if traffic_level > 7 → Risky | High traffic on a normal day is congestion, not disaster risk |
| if water_level > 50 cm → Blocked | water_level gauge has no location context for road blockage |
| risk_score = formula(rainfall, traffic, water_level) | Exact anti-pattern producing the 99.4% synthetic accuracy |

---

## Mapping to Independent Sources

| Class | Minimum independent evidence required |
|---|---|
| SAFE | 0 confirmed hazard reports + no official closure + no critical visual detection |
| RISKY | >= 1 of: active incident report OR water 5-20 cm OR visibility <= 200 m OR medium YOLO |
| BLOCKED | >= 1 of: official closure OR water > 20 cm OR critical YOLO detection OR traffic standstill |

---

## Future Label Acquisition Strategy

1. **Gold standard:** Official road authority closure records with timestamp and segment ID (BLOCKED)
2. **Silver standard:** Flood monitoring station water depth with GPS coordinate (RISKY/BLOCKED)
3. **Bronze standard:** Corroborated crowdsource reports (>= 2 independent reports within 500 m, 30 min) (RISKY)
4. **Inferred:** YOLO visual detection + meteorological co-validation (SAFE/RISKY)

SAFE labels must be derived by **absence of evidence** only when the absence can itself be verified (e.g., no incident reports AND weather API shows no precipitation AND GPS probe shows normal speed).

---

*Document maintained by ADAS Phase 2 dataset design. Do not alter label thresholds without updating the label acquisition pipeline and re-labelling any training data.*
