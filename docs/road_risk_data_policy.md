# Road Risk Data Policy
**ADAS — Intelligent Vehicle Assistance During Disasters**
**Document version:** 2.0 | **Phase:** 2 | **Status:** AUTHORITATIVE

---

## Purpose

This policy defines the rules that MUST be followed when constructing any training, validation, or test dataset for the XGBoost road-risk model. Its primary goal is to prevent **target leakage** — the accidental inclusion of information derived from the label or from the future into the input features.

Violation of these rules produces artificially high training accuracy that does not reflect real-world performance. The 99.4% accuracy of the Phase 1 synthetic model is a direct consequence of such a violation.

---

## RULE 1 — No Target-Derived Features

The label (Safe / Risky / Blocked) or any variable computed from the label MUST NOT appear in the input feature set.

**Forbidden patterns:**

| Forbidden pattern | Why forbidden |
|---|---|
| Including `road_risk_status` in X | Direct target leakage |
| Including `risk_score = f(rainfall, traffic, water_level)` in X where `risk_score` determines the label | Intermediate leakage variable |
| Including any risk category derived from the same thresholds | The model learns the rule, not reality |
| Computing a feature as a function of `y` (e.g., label-encoding the target and including it as a feature) | Information from y injected into X |

**Required check before any dataset is used:**
- Compute Pearson correlation of every feature column with the numeric label.
- Any feature with |correlation| > 0.95 must be manually reviewed and justified or removed.
- Run a single Decision Tree (max_depth=1) on each feature individually. If any single feature achieves > 90% accuracy, that feature is suspect.

---

## RULE 2 — No Future Information at Prediction Time

Every feature used during training MUST be obtainable at inference time from information available at or before the prediction timestamp.

**Forbidden temporal patterns:**

| Forbidden pattern | Reason |
|---|---|
| Using road status at t+10 min as a feature to predict status at t | Post-event information |
| Using rainfall measured at t+30 min | Future weather unavailable at prediction time |
| Using the final water depth after a flood event | Outcome-based feature |
| Using "road was cleared at 14:00" to label an observation at 13:45 | Label derived from future state |
| Using a feature aggregated over the entire event window | Includes future observations |

**Required check:**
- For every feature, document the `prediction_time_available` flag in `config/road_risk_features.json`.
- Any feature marked `prediction_time_available: false` must not be used as a predictor.

---

## RULE 3 — No Post-Event Labelling Using Within-Event Aggregates

When a disaster event (flood, fire, etc.) runs over a time window [t_start, t_end], observations collected during [t_start, t_end] MUST NOT be labelled using information that was only available at t_end.

**Correct approach:**
- At each timestamp t, the label must reflect the road condition at time t as determined by evidence available at or before t.
- If the label is obtained from an official report issued at t_end covering the event from t_start, that label may only be applied to timestamps within the event window if the evidence is presented as a look-ahead-free annotation (i.e., a human annotator reviewing the event after the fact, explicitly constrained to conditions visible at time t).

---

## RULE 4 — Temporal Splitting (Not Random Row Splitting)

When splitting the dataset into train / validation / test partitions, splitting must be done by **time**, not by random row shuffle.

**Required split design:**

| Partition | Description |
|---|---|
| Train | All observations before cut-off date T1 |
| Validation | Observations in [T1, T2] |
| Test (held-out) | Observations after T2 |

**Why random splitting is prohibited:**
- Random splitting allows the model to see data from the same disaster event in both train and test, causing information leakage across the split boundary.
- Near-duplicate consecutive rows from the same road segment can appear in both train and test.
- The model can memorise event-specific patterns that do not generalise.

---

## RULE 5 — Geographic and Session Isolation

The following grouping leakage sources must be controlled:

| Source | Risk | Mitigation |
|---|---|---|
| Same road segment in train and test | Model learns segment-specific patterns | Group by segment_id when splitting |
| Same disaster event in train and test | Model memorises event context | Split by event_id or event start time |
| Same vehicle/session in train and test | Driver behaviour correlation | Split by session_id if vehicle data used |
| Consecutive near-duplicate rows | Model memorises trivially correlated steps | Deduplicate rows where all features identical within 30-second window |

---

## RULE 6 — Feature Engineering Transparency

All derived features must be documented before they are added to the dataset. Specifically:

- **Rolling window features** (e.g., `rainfall_10min_mm`, `congestion_change`): the window must end at or before the prediction timestamp. The window must not extend into the future.
- **Ratios and deltas**: computed from two point-in-time values, both of which must satisfy Rule 2.
- **Spatial features** (e.g., `elevation_m`, `road_slope_pct`): from static map data, not from events. These are safe from temporal leakage.
- **YOLO-derived features** (vehicle_count, fire_detected, etc.): must come from the frame captured at prediction time, not from a later review.

---

## RULE 7 — Synthetic Benchmark Isolation

The existing synthetic XGBoost model and its dataset are classified as:

**SYNTHETIC BENCHMARK — for architecture validation only**

Rules:
- This dataset MUST NOT be merged with real-world observations.
- This dataset MUST NOT be used to report real-world ADAS accuracy.
- This dataset is preserved in `models/baselines/xgboost_synthetic/` for reference.
- Its 99.4% accuracy reflects learning a deterministic formula and has no predictive validity.

---

## RULE 8 — Label Must Be Independently Sourced

The label (Safe / Risky / Blocked) must come from a source that is **not** derived from the same features used for prediction. Acceptable label sources are defined in `docs/road_risk_label_definition.md`.

**Forbidden label sources:**
- Applying threshold rules directly to rainfall, traffic, or water_level values
- Having a developer manually label rows by visually examining feature values
- Any labelling script that reads the feature columns and applies a formula

**Required label sources:**
- Official road closure records
- Flood gauge readings (water depth at road location)
- Emergency service / disaster management reports
- Confirmed multi-source crowdsource incident reports
- YOLO-validated visual evidence (as secondary corroboration, not sole source)

---

## RULE 9 — Water Level Classification

`water_level` as used in the Phase 1 synthetic model is an abstract scalar. For a real dataset:

- Water depth must be measured at or near the road segment, not at an arbitrary gauge.
- It must have a GPS coordinate and timestamp.
- It must not be used as the direct determinant of the label (see Rule 1 and Label Definition).
- Classification: **sensor-dependent / optional**. Not suitable as a required feature until physical sensor or authoritative real-time flood gauge data is integrated.

---

## RULE 10 — Reporting Requirements

Any model trained under this policy must report:
1. Dataset date range (train / val / test)
2. Label source(s) and percentage of labels from each source
3. Feature engineering provenance for all derived features
4. Geographic coverage (bounding box or list of regions)
5. Class distribution in each split
6. Whether temporal or geographic split was used
7. Any deviations from this policy with written justification

---

## Summary Checklist

Before submitting any dataset for training:

- [ ] No feature correlation with label exceeds 0.95 without manual justification
- [ ] No single feature achieves > 90% accuracy in a depth-1 decision tree
- [ ] Every feature is `prediction_time_available: true`
- [ ] Dataset is split by time, not by random row shuffle
- [ ] Train and test contain no overlapping disaster events
- [ ] Labels are sourced independently of the feature values
- [ ] Synthetic benchmark data is not merged with real data
- [ ] Rolling window features do not look into the future
- [ ] water_level is treated as sensor-dependent / optional
- [ ] Reporting requirements (Rule 10) are documented

---

*This policy is effective from Phase 2 of the ADAS project. It supersedes any implicit data conventions established during Phase 1.*
