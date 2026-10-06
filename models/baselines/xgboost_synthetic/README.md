# XGBoost Synthetic Baseline Model (`synthetic-baseline-v1`)

## ⚠️ Important Preservation & Archival Notice

This directory archives the original **XGBoost Road Safety Classifier** developed during early project prototyping.

* **Model Version:** `synthetic-baseline-v1`
* **Model File:** `road_model.pkl` (SHA256: `FA2658F878B5D2B802CAFF01E84C9FE5BB093C07096E5544805CF347AD39B3A8`)
* **Training Script:** `train_xgboost.py` (SHA256: `0C67B67475925ED4F540D8687F0BB13EA1678181380D08905E65C8C50C516135`)
* **Audit Script:** `audit_xgboost.py` (SHA256: `5D5393792D09B671B3298D003AB3E7817061ECAA7F0020EA2E630E337EB7AFCE`)

---

## 📌 Critical Audit Disclosures

1. **Synthetic Benchmark Only**:
   This model was trained exclusively on a 2,500-sample synthetic dataset generated from uniform distributions.
2. **Deterministic Label Derivation**:
   The ground truth labels (`0: Safe`, `1: Risky`, `2: Blocked`) were produced by a closed-form programmatic `if/elif/else` rule directly evaluating the exact 3 features fed to the model:
   ```python
   risk_score = (rainfall * 0.3) + (traffic * 4.0) + (water_level * 1.2)
   if wl > 50 or r_score > 120 or rf > 100:
       label = 2  # Blocked
   elif wl > 20 or r_score > 65 or rf > 40:
       label = 1  # Risky
   else:
       label = 0  # Safe
   ```
3. **99.4% Accuracy is NOT Real-World ADAS Validation**:
   The reported 99.4% test accuracy (and 99.40% ± 0.30% 5-fold CV) represents the capability of a decision tree / gradient boosting model to approximate orthogonal piecewise threshold logic in a 3D coordinate space with zero stochastic noise. It must **not** be presented as real-world disaster road prediction performance.
4. **Permanent Baseline Role**:
   This baseline is permanently preserved here for scientific comparison, regression auditing, and backward compatibility. It must not be overwritten.
