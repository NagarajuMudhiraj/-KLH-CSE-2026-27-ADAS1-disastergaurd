# ADAS Phase 7 — V5 Dataset Quality Report

**Status:** **NO_SUITABLE_REAL_TABULAR_DATASET_FOUND**  
**Training readiness:** **NOT_READY_FOR_MODEL_TRAINING**

## V5 profile

| Check | Result |
|---|---:|
| Rows | 0 |
| REAL / simulation / synthetic | 0 / 0 / 0 |
| Events / regions / road segments | 0 / 0 / 0 |
| Temporal coverage | None |
| SAFE / RISKY / BLOCKED | 0 / 0 / 0 |
| Original labels / mapped labels | 0 / 0 |
| Duplicate rows / duplicate observations | 0 / 0 |

## Integrity checks

No missing values, temporal leakage, spatial leakage, or target leakage can be
measured because no row was admitted.  This is intentional: current candidates
lack either an inspectable historical extract, compatible independent target
semantics, or a validated feature-at-time-of-label join.  V5 includes the
canonical metadata and original/mapped-label columns for a future source, but
contains no model features or target rows.

## Admission requirements

A future row must supply a source observation timestamp, WGS84 (or documented
transformable) location/geometry, independently recorded road-state label,
source identity, and a documented feature join where each value existed at or
before the label time.  Closure notices may map only `ROAD_CLOSED -> BLOCKED`;
they do not create SAFE or RISKY observations.
