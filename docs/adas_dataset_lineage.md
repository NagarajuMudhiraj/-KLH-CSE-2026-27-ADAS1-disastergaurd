# ADAS Dataset Lineage and Training Status

```text
V1/V2 synthetic baseline (SYNTHETIC_BENCHMARK; preserved)
    ↓
V3 FloodNet tabular attempt (QUARANTINED / NOT_FOR_MODEL_TRAINING)
    ↓
V4 provenance gate (0 eligible rows)
    ↓
V5 candidate-source audit (0 selected rows)
    ↓
Future source-native verified dataset (required before XGBoost training)
```

V3 is retained only as evidence of the original FloodNet-label experiment. Its
coordinates/timestamps and several tabular features were builder-generated or
fallback values, so it is not an XGBoost training source. V4/V5 intentionally
contain no promoted REAL rows. The synthetic baseline remains separate and is
not evidence of real-world model readiness.
