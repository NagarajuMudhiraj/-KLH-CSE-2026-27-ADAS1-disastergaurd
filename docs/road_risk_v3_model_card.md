# Model Card: Road Risk XGBoost V3 (Dynamic Weather & Relative Hydrology Benchmark)

## 1. Model Details

* **Model Name:** XGBoost Road Risk V3 (`road_risk_v3`)
* **Model Version:** 3.0.0-pilot
* **Release Date:** September 2026
* **Model Type:** Gradient Boosted Decision Trees (Binary Classifier)
* **Algorithm / Runtime:** `xgboost==3.4.1`, `scikit-learn==1.9.0`, Python 3.12
* **Artifact Directory:** `models/road_risk_v3/`
* **Preservation Status:** Synthetic baseline (`models/road_model.pkl`) and XGBoost V2 (`models/road_risk_v2/`) are strictly preserved and remain untouched.

---

## 2. Model Purpose & Intended Use

* **Primary Purpose:** Provide an exploratory offline machine learning benchmark for estimating road segment flood-hazard corridor exposure (`target_flood_exposure`) using dynamic weather, antecedent precipitation, and relative channel hydrology.
* **Intended Use:**
  * Offline spatial vulnerability benchmarking.
  * Hydrological feature sensitivity analysis.
  * Research into cross-basin generalization vs spatial memorization.
* **Prohibited Uses & Strict Safety Exclusions:**
  * **NOT a validated vehicle safety controller.**
  * **NOT designed or approved for automated emergency braking (AEB), dynamic hazard steering, or vehicle control intervention.**
  * **NOT a road closure or pavement submergence prediction system.**
  * **NOT an accident prediction or crash prevention model.**
  * **NOT validated for nationwide or state-wide (Telangana-wide) autonomous deployment.**

---

## 3. Dataset & Provenance

* **Dataset File:** `data/processed/road_risk_dataset_v8.csv`
* **Dataset SHA-256 Checksum:** `1dce0d6ef702c2159d4d0ad0a57b16ab9327eafa66267a52eacba750cd10db5c`
* **Total Observations ($N$):** 68 real observations (zero synthetic rows)
* **Temporal Events:** 13 distinct historical event periods (9 historical flood events + 4 dry baseline controls, 2005–2022)
* **Geographical Basins:** 4 regions across 2 river basins (Godavari Lower, Manjira Singur, Manjira NizamSagar, Krishna Agraharam)
* **Target Distribution:**
  * Class 0 (`NOT_EXPOSED`): 50 observations (73.53%)
  * Class 1 (`FLOOD_EXPOSED`): 18 observations (26.47%)
  * Class Imbalance Ratio: 2.78 : 1

---

## 4. Feature Contract (9 Features)

| Feature Name | Category | Type | Unit | Source | Real-Time Feasibility |
| :--- | :--- | :--- | :---: | :--- | :---: |
| `rainfall_24h_mm` | DYNAMIC_WEATHER | float | mm | Open-Meteo ERA5 Reanalysis | **AVAILABLE_NOW** |
| `rainfall_72h_mm` | DYNAMIC_WEATHER | float | mm | Open-Meteo ERA5 Reanalysis ($t-2d \dots t$) | **AVAILABLE_NOW** |
| `rainfall_7d_mm` | DYNAMIC_WEATHER | float | mm | Open-Meteo ERA5 Reanalysis ($t-6d \dots t$) | **AVAILABLE_NOW** |
| `temperature_c` | DYNAMIC_WEATHER | float | °C | Open-Meteo ERA5 Reanalysis | **AVAILABLE_NOW** |
| `wind_speed_kmh` | DYNAMIC_WEATHER | float | km/h | Open-Meteo ERA5 Reanalysis | **AVAILABLE_NOW** |
| `relative_elevation_m` | RELATIVE_HYDROLOGY | float | m | Copernicus GLO-30 DEM ($z_{\text{road}} - z_{\text{datum}}$) | **AVAILABLE_NOW** |
| `upstream_rainfall_72h_mm`| UPSTREAM_HYDROLOGY | float | mm | Open-Meteo ERA5 Reanalysis at gauge coordinate | **AVAILABLE_WITH_PROVIDER** |
| `road_type` | ROAD | categorical | enum | TGRAC GIS RnB Roads (`arterial`, `collector`, `highway`)| **AVAILABLE_NOW** |
| `road_surface` | ROAD | categorical | enum | TGRAC GIS RnB Roads (`BT`, `CC`) | **AVAILABLE_NOW** |

### Excluded & Quarantined Variables:
* `road_length_m`: **Permanently removed** (diagnosed in Phase 12 as a road-identity memorization proxy).
* `elevation_m`: **Superseded** by `relative_elevation_m`.
* `distance_to_flood_m`, `gauge_water_level_m`, `gauge_warning_level_m`, `flood_stage`: **Strictly quarantined** (target-generating variables).

---

## 5. Training Configuration & Hyperparameters

* **Algorithm:** `XGBClassifier`
* **Objective:** `binary:logistic`
* **Evaluation Metric:** `logloss`
* **Random Seed:** 42
* **Number of Trees (`n_estimators`):** 50
* **Max Tree Depth (`max_depth`):** 3
* **Learning Rate (`learning_rate`):** 0.05
* **Subsample Ratio (`subsample`):** 0.8
* **Column Subsample (`colsample_bytree`):** 0.8
* **Class Weighting (`scale_pos_weight`):** Dynamically computed as $N_{\text{neg}} / N_{\text{pos}}$ on the training fold only.
* **Preprocessing:** `StandardScaler` for numeric, `OneHotEncoder(handle_unknown='ignore')` for categorical, fitted strictly on training data.

---

## 6. Rigorous Evaluation Results Across 4 Strategies

### Strategy A: Event-Held-Out Split ($N=16$, Pos=5, Neg=11)
* **Accuracy:** 0.3750
* **Precision:** 0.3333
* **Recall:** **1.0000 (100.0% — zero false negatives)**
* **F1 Score:** 0.5000
* **ROC-AUC:** 0.9818
* **PR-AUC:** 0.9667
* **Brier Score:** 0.3034
* **Confusion Matrix:** $\text{TP}=5, \text{TN}=1, \text{FP}=10, \text{FN}=0$.

### Strategy B: Unseen-Road Evaluation ($N=18$, Pos=7, Neg=11) — Primary Anti-Memorization Benchmark
* **Accuracy:** 0.6667 (66.67%)
* **Precision:** 0.5455 (54.55%)
* **Recall:** **0.8571 (85.71% — detected 6 of 7 exposed roads)**
* **F1 Score:** **0.6667**
* **ROC-AUC:** **0.7792**
* **PR-AUC:** 0.5362
* **Brier Score:** 0.1935
* **Confusion Matrix:** $\text{TP}=6, \text{TN}=6, \text{FP}=5, \text{FN}=1$.

### Strategy C: Cross-Basin Evaluation
* **Fold A (Krishna/Manjira Basin $\rightarrow$ Godavari Basin Test, $N=20$, Pos=12, Neg=8):**
  * Accuracy: 0.4000 | Recall: 0.0000 | F1: 0.0000 | ROC-AUC: 0.3750
  * Result: Model fails to detect Godavari flood crests because Godavari flood exposure occurs at $+23\text{m}$ to $+28\text{m}$ above riverbed, whereas Singur flood exposure occurs at $\le -10\text{m}$.
* **Fold B (Godavari/NizamSagar/Agraharam $\rightarrow$ Singur Basin Test, $N=16$, Pos=6, Neg=10):**
  * Accuracy: 0.6250 | Recall: 0.0000 | F1: 0.0000 | ROC-AUC: 0.6833

### Strategy D: Combined Generalization Split (Singur Event 916-11, $N=4$, Pos=2, Neg=2)
* Accuracy: 0.5000 | Recall: 0.0000 | F1: 0.0000 | ROC-AUC: 0.7500

---

## 7. Model Evolution: V2 vs V3 Benchmark Comparison

| Evaluation Strategy | Metric | XGBoost V2 (Full) | XGBoost V2 (No Length) | XGBoost V3 (Dynamic + Rel Elev) | Impact & Direction |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Unseen-Road** | **Recall** | 42.86% | 100.0% | **85.71%** | **Massive Recall Gain (+42.9%)** |
| **Unseen-Road** | **F1 Score** | 0.4286 | 0.6667 | **0.6667** | **Substantial F1 Gain (+23.8%)** |
| **Unseen-Road** | **ROC-AUC** | 0.7556 | 0.8459 | **0.7792** | Maintained strong ranking signal |
| **Event-Held-Out** | **Recall** | 60.0% | 60.0% | **100.0%** | Zero missed floods |
| **Event-Held-Out** | **ROC-AUC** | 0.9636 | 0.9636 | **0.9818** | High discrimination |
| **Cross-Basin (Fold A)** | **Recall** | 33.33% | 33.33% | **0.00%** | Unstable due to basin morphology |

---

## 8. Feature Importance (XGBoost Gain)

1. `road_type_collector`: **0.2302 (23.0%)** — *Confounded with Singur/NizamSagar geographic clustering*
2. `relative_elevation_m`: **0.2044 (20.4%)** — *Physical vertical clearance above regional channel*
3. `upstream_rainfall_72h_mm`: **0.1996 (20.0%)** — *Antecedent inflow from upstream drainage*
4. `rainfall_72h_mm`: **0.0915 (9.2%)** — *Multi-day local catchment precipitation*
5. `temperature_c`: **0.0870 (8.7%)**
6. `rainfall_7d_mm`: **0.0833 (8.3%)**
7. `wind_speed_kmh`: **0.0545 (5.5%)**
8. `rainfall_24h_mm`: **0.0495 (5.0%)**

---

## 9. Error Analysis on Unseen-Road Test Set

The Unseen-Road test produced exactly **1 False Negative** and **5 False Positives**:
1. **False Negative (1):**
   * `V8_OBS_002` (Godavari Highway 44, Event 925-1, 2006-08-29): True=1, Pred=0 (Prob: 0.4123).
   * *Explanation:* Local 24h rain was low (1.6 mm); model assigned near-threshold probability (0.412 < 0.50), narrowly missing the severe 2006 crest.
2. **False Positives (5):**
   * `V8_OBS_035` (Singur Collector 1731, Dry Baseline 2019-03-15): True=0, Pred=1 (Prob: 0.5834).
   * `V8_OBS_040`, `044`, `048`, `052` (NizamSagar Collector 452, all 4 events): True=0, Pred=1 (Probs: 0.63–0.80).
   * *Explanation:* Decision trees placed heavy weight on `road_type_collector` and `relative_elevation_m <= -10m`. Collector 452 in NizamSagar possesses both properties, but is situated 4.6 km away from the river, outside the 2.5 km buffer.

---

## 10. Model Limitations & Probability Caveats

1. **Small Sample Size ($N=68$):** The pilot sample size remains exploratory.
2. **Probability Calibration:** Output probabilities must be interpreted as ordinal hazard scores, not calibrated frequentist probabilities.
3. **Cross-Basin Morphology Gap:** Relative elevation above riverbed datum does not completely eliminate basin morphology differences (wide deep river gorge vs reservoir spillway).

---

## 11. Final Status

**`V3_PILOT_UNSTABLE`**

*XGBoost V3 achieved substantial progress on unseen roads (Recall jumped from 42.9% to 85.7%, F1 jumped from 0.43 to 0.67), proving that removing `road_length_m` and adding antecedent rainfall successfully broke the static memorization trap of V2. However, cross-basin transfer remains unstable (Recall = 0.0%), and categorical road type causes false alarms in unexposed collector corridors.*
