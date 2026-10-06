# Phase 6 Multi-Event Source Audit

## Verified in the repository

| Event | Region | Source/label | Usable V4 rows |
|---|---|---|---:|
| Hurricane Harvey (2017) | Texas, USA | FloodNet human aerial annotation (SILVER) | 0 — current files lack source-native capture coordinates/times |

## Public sources assessed, not ingested

| Candidate | Scope | Why not connected/used |
|---|---|---|
| FloodNet | Hurricane Harvey; UAV, post-flood imagery | Present locally, but the repository has no per-image geolocation/capture-time manifest needed for feature joins. |
| xBD/xView2 | Multiple floods, fires, storms and other events; geographic patch metadata | Labels are building-damage classes, not the project's three road-risk classes. Mapping them to SAFE/RISKY/BLOCKED would fabricate labels. |
| USGS 3DEP | United States terrain | Can supply elevation/slope only after genuine road coordinates/geometry are available; it cannot create labels or event observations. |
| Open-Meteo historical archive | Global hourly reanalysis | Can supply weather only for a verified event time and coordinate; it cannot repair manufactured row metadata. |

No connector was implemented and no source was downloaded. A future source must provide independent event identity, licensed access, label semantics compatible with 0/1/2, coordinates, timestamp, and road geometry before admission.

## Partition plan

When at least three independent qualified events exist: assign older event(s) to TRAIN, a separate later event to VALIDATION, and an untouched independent event to TEST_HOLDOUT. No event may span splits. There is no valid split today.
