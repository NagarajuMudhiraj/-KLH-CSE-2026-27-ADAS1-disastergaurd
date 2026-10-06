# Phase 12 Generalization & Proxy Audit: Road Memorization vs Genuine Flood Risk Signal

**Document Version:** 1.0  
**Phase:** Phase 12 Generalization Audit  
**Audit Date:** 2026-09-30  
**Status / Final Verdict:** **`ROAD_PROXY_DOMINATED`**  
**Dataset:** `data/processed/road_risk_dataset_v7.csv` ($N=68$, SHA-256: `066d1e44445eb6b2eeecdd4cef7d611c2fcfe2eb573e8ffc0c9ecab1e1b74658`)

---

## 1. Executive Summary & Core Diagnostic Findings

In Phase 11, the XGBoost V2 model achieved 87.5% test accuracy on an event-held-out split. However, an ablation test revealed that **Road-Only features (without any meteorological data) achieved 100.0% test accuracy**. 

Phase 12 conducted a rigorous forensic audit to determine whether the model was learning genuine flood-exposure physics or exploiting static geographic proxies. The empirical findings are conclusive:

1. **The 100% Road-Only Test Result Was an Illusion of Road Overlap:**
   In the Strategy A event-held-out split, **100% of the test road segments were present in the training set** ($\text{Train roads} \cap \text{Test roads} = 16$). Because exactly 5 road segments in the dataset are situated within 2.5 km of river gauges, tree models used static `elevation_m` and `road_length_m` as unique fingerprints to memorize which 5 roads were flood-exposed.
2. **Road-Only Performance Collapses on Unseen Roads:**
   When evaluated on a strict holdout of completely unseen roads ($\text{Train roads} \cap \text{Test roads} = \emptyset$), Road-Only accuracy plummeted from **100.0% to 65.38%** (ROC-AUC: 0.5827, F1: 0.4000).
3. **Absolute Elevation Prevents Cross-Basin Generalization:**
   Exposed roads in Godavari Lower lie at elevations of **56–61 m**, whereas exposed roads in Manjira Singur lie at **508–511 m**. When trained on Godavari and tested on Singur, the model learned a split at $<65\text{ m}$ and predicted **zero flood exposure for all Singur roads (Recall = 0.0%)**, failing completely.
4. **Road Length is an Artifact:**
   `road_length_m` is an arbitrary GIS digitization artifact. Ablation proved that **removing road length improved unseen-road accuracy from 69.2% to 73.1% and raised ROC-AUC to 0.8459**.
5. **Final Diagnostic Verdict:** **`ROAD_PROXY_DOMINATED`**.

---

## 2. Target Generation Mechanism & Spatial Confounding

As detailed in [`docs/phase12_target_generation_audit.md`](file:///d:/datasets_IDM(ADAS)/docs/phase12_target_generation_audit.md), the target is computed deterministically:
$$\text{target\_flood\_exposure} = \mathbf{1}_{[\text{is\_flood\_event} == \text{True}]} \times \mathbf{1}_{[\text{distance\_to\_gauge} \le 2500\text{m}]}$$

Because regional river gauge coordinates are fixed:
* $\text{distance\_to\_gauge}$ is a **static spatial constant** for each road segment.
* Out of 16 road segments in the entire dataset, **exactly 5 roads** are $\le 2,500\text{ m}$ from a gauge:
  * `TGRAC_ARTERIAL_23` (Bhadrachalam): 1,778 m
  * `TGRAC_HIGHWAY_43` (Bhadrachalam): 1,072 m
  * `TGRAC_HIGHWAY_44` (Bhadrachalam): 1,206 m
  * `TGRAC_COLLECTOR_1730` (Singur): 620 m
  * `TGRAC_COLLECTOR_1731` (Singur): 678 m
* The remaining 11 roads are all $>4,600\text{ m}$ away and **never have a positive label in the entire dataset**.

Whenever an evaluation split tests exclusively on flood dates, any classifier that can distinguish these 5 road IDs from the other 11 will achieve 100% accuracy.

---

## 3. Road Repeat & Overlap Analysis

In Phase 11's Strategy A (Event-Level Holdout):
* **Total Unique Road Segments:** 16
* **Train Road Segments ($N=40$ rows):** 16 unique roads
* **Validation Road Segments ($N=12$ rows):** 12 unique roads
* **Test Road Segments ($N=16$ rows):** 16 unique roads
* **Pairwise Overlaps:**
  * $\text{Train roads} \cap \text{Test roads} = 16\text{ roads}$ (**100.0% road overlap**)
  * $\text{Train roads} \cap \text{Val roads} = 12\text{ roads}$ (**100.0% val road overlap**)
  * $\text{Val roads} \cap \text{Test roads} = 12\text{ roads}$ (**100.0% overlap**)
* **Event Overlap:**
  * $\text{Train events} \cap \text{Test events} = \emptyset$ (**0.0% event overlap**)

> **Critical Distinction:** Strategy A guaranteed **event uniqueness** (no temporal leakage), but had **complete road repetition** (100% spatial overlap). The model was evaluated on the exact same 16 physical roads it was trained on.

---

## 4. Unseen-Road Evaluation Strategy

To isolate genuine learning from spatial memorization, we created a clean **Unseen-Road Split** where:
$$\text{Train roads} \cap \text{Test roads} = \emptyset$$

* **Test Roads ($N=6$ roads, 26 observations):**
  * `TGRAC_HIGHWAY_44` (Bhadrachalam, exposed)
  * `TGRAC_HIGHWAY_45` (Bhadrachalam, unexposed)
  * `TGRAC_COLLECTOR_1731` (Singur, exposed)
  * `TGRAC_COLLECTOR_1732` (Singur, unexposed)
  * `TGRAC_HIGHWAY_25` (NizamSagar, unexposed)
  * `TGRAC_HIGHWAY_419` (Agraharam, unexposed)
  * *Test Class Distribution:* 7 Exposed, 19 Unexposed.
* **Train Roads ($N=10$ roads, 42 observations):**
  * 11 Exposed, 31 Unexposed.

### Model Performance on Strictly Unseen Roads:

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Raw Counts (TP / TN / FP / FN) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dummy (Majority)** | 0.7308 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0 / 19 / 0 / 7 |
| **Logistic Regression** | 0.6923 | 0.0000 | 0.0000 | 0.0000 | 0.4436 | 0 / 18 / 1 / 7 |
| **Decision Tree ($d=3$)** | 0.7308 | 0.5000 | 0.1429 | 0.2222 | 0.6353 | 1 / 18 / 1 / 6 |
| **Random Forest ($n=50$)** | 0.6923 | 0.4444 | 0.5714 | 0.5000 | 0.7782 | 4 / 14 / 5 / 3 |
| **XGBoost V2 (Full)** | **0.6923** | **0.4286** | **0.4286** | **0.4286** | **0.7556** | **3 / 15 / 4 / 4** |

**Finding:** On truly unseen roads, XGBoost V2 accuracy drops from 87.5% to **69.23%**, and F1 drops from 0.75 to **0.4286**. It is no longer superior to a simple Random Forest.

---

## 5. Comprehensive Feature Ablation on Unseen Roads

We tested 9 feature configurations on the Unseen-Road holdout:

| Configuration | Features Included | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Counts (TP / TN / FP / FN) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A. Weather only** | rain, temp, wind | 0.6538 | 0.4000 | 0.5714 | 0.4706 | 0.7707 | 4 / 13 / 6 / 3 |
| **B. Road only** | elev, length, type, surface | 0.6538 | 0.3750 | 0.4286 | 0.4000 | 0.5827 | 3 / 14 / 5 / 4 |
| **C. Weather + Road** | all 7 features | 0.6923 | 0.4286 | 0.4286 | 0.4286 | 0.7556 | 3 / 15 / 4 / 4 |
| **D. Remove elevation** | rain, temp, wind, length, type, surface | 0.7308 | 0.5000 | 0.4286 | 0.4615 | 0.7218 | 3 / 16 / 3 / 4 |
| **E. Remove road length** | **rain, temp, wind, elev, type, surface** | **0.7308** | **0.5000** | **1.0000** | **0.6667** | **0.8459** | **7 / 12 / 7 / 0** |
| **F. Remove road type** | num_cols, surface | 0.7308 | 0.5000 | 0.4286 | 0.4615 | 0.7444 | 3 / 16 / 3 / 4 |
| **G. Remove road surface**| num_cols, type | 0.7308 | 0.5000 | 0.4286 | 0.4615 | 0.7782 | 3 / 16 / 3 / 4 |
| **H. Elevation only** | elevation_m | 0.5769 | 0.3889 | 1.0000 | 0.5600 | 0.7932 | 7 / 8 / 11 / 0 |
| **I. Road length only** | road_length_m | 0.6538 | 0.3750 | 0.4286 | 0.4000 | 0.5376 | 3 / 14 / 5 / 4 |

### Critical Ablation Insights:
1. **Road Only Collapses:** Road-Only ROC-AUC is just **0.5827** (barely above random 0.50). Its Phase 11 score of 100% was pure memorization.
2. **Weather Provides the Real Generalization Signal:** Weather Only achieves ROC-AUC **0.7707** on unseen roads.
3. **Removing Road Length Dramatically Improves Generalization:** 
   When `road_length_m` is removed, Recall jumps from 42.9% to **100.0%** (zero false negatives), F1 rises to **0.6667**, and ROC-AUC reaches **0.8459**. `road_length_m` was acting as an adversarial distractor.

---

## 6. Elevation Proxy & Regional Confounding Test

Elevation distribution across target classes:

| Elevation Band | Total Obs | Exposed Obs ($Y=1$) | Target Rate | Min Elev | Max Elev | Regions Represented |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **$< 100\text{ m}$** | 20 | 12 | **0.600** (60%) | 56.0 m | 84.0 m | Godavari_Lower |
| **$100 - 300\text{ m}$** | 8 | 0 | **0.000** (0%) | 287.0 m | 288.0 m | Krishna_Agraharam |
| **$300 - 500\text{ m}$** | 24 | 0 | **0.000** (0%) | 331.0 m | 443.0 m | NizamSagar & Agraharam |
| **$500 - 700\text{ m}$** | 16 | 6 | **0.375** (37.5%) | 508.0 m | 607.0 m | Manjira_Singur |

### Why Elevation Confounding Breaks Cross-Region Generalization:
* In the Godavari basin, floodplains are at **56–61 m**.
* In the Manjira basin (Singur), floodplains are at **508–511 m**.
* In the Krishna basin (Agraharam), non-flood plateau roads are at **287–347 m**.
* A tree split on `elevation_m <= 65m` successfully isolates Godavari floods, but completely misclassifies Singur floods as unexposed.
* **Empirical Proof:** When holding out `Manjira_Singur` and training on the remaining regions, XGBoost V2 scored:
  $$\text{Accuracy} = 62.50\%, \quad \text{Recall} = 0.00\%, \quad \text{F1} = 0.000$$
  It predicted $\hat{Y} = 0$ for every single road in Singur because their elevation exceeded 500 m.

---

## 7. Road Length Proxy Test

* **Unique lengths:** 16 unique values for 16 roads (100% unique).
* Length ranges vs Target:
  * $<1,000\text{ m}$: 2 roads (8 obs, 3 pos, rate: 37.5%)
  * $1,000 - 5,000\text{ m}$: 3 roads (13 obs, 7 pos, rate: 53.8%)
  * $5,000 - 10,000\text{ m}$: 7 roads (30 obs, 4 pos, rate: 13.3%)
  * $>10,000\text{ m}$: 4 roads (17 obs, 4 pos, rate: 23.5%)
* **Finding:** Road length in TGRAC GIS is an arbitrary artifact of where administrative GIS digitizers split polyline shapefiles. It has no physical relation to flood physics. Because every road segment had a unique float value (e.g. 80.4 m, 1303.8 m, 18163.0 m), decision trees used length as an exact surrogate for `road_segment_id`.

---

## 8. Categorical Proxy & Confounding Test

* `road_type`:
  * `collector`: Only present in Singur and NizamSagar.
  * `arterial`: Only present in Godavari and Agraharam.
  * `highway`: Present in all 4 regions.
* `road_surface`:
  * `CC` (cement concrete): Only 1 road in the dataset (`TGRAC_COLLECTOR_1732` in Singur), which happens to be unexposed ($Y=0$).
  * `BT` (bituminous): 15 of 16 roads.
* **Finding:** Road classifications are geographically clustered, reinforcing regional confounding.

---

## 9. Weather Signal & Hydrological Disconnect

Why did weather features contribute relatively little in Phase 11?

1. **Local Rain vs Catchment Discharge:**
   * Mean 24h rainfall on unexposed days: **1.65 mm**
   * Mean 24h rainfall on exposed days: **6.62 mm**
   * However, in major riverine events (e.g. `INDOFLOODS-gauge-916-1` at Singur, `INDOFLOODS-gauge-925-2` at Bhadrachalam), local 24h rainfall on the peak flood date was **0.0 mm to 0.3 mm**!
   * **Hydrological Reason:** Large river basins (Godavari, Krishna) experience peak river stages 24–72 hours after torrential rain hundreds of kilometers upstream in the Western Ghats / Maharashtra. The local gauge water level spikes due to upstream dam releases (e.g. Singur Dam gate openings), even under clear local skies.
2. **Spatial and Temporal Aggregation Loss:**
   * Same-day 24h precipitation at the road centroid does not reflect multi-day antecedent catchment rainfall ($R_{3d}, R_{7d}$) or upstream inflow.

---

## 10. Unseen-Region Holdout Results

Evaluating strict cross-regional holdouts:

| Held-Out Region | Train Rows | Test Rows | Test Distribution | Holdout Status | Accuracy | Recall | F1 | ROC-AUC |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| **Krishna_Agraharam** | 52 | 16 | 0 Pos, 16 Neg | `INSUFFICIENT_POSITIVE_HOLDOUT` | 1.0000 | N/A | N/A | N/A |
| **Manjira_NizamSagar** | 52 | 16 | 0 Pos, 16 Neg | `INSUFFICIENT_POSITIVE_HOLDOUT` | 0.8125 | N/A | N/A | N/A |
| **Manjira_Singur** | 52 | 16 | 6 Pos, 10 Neg | Validated Holdout | 0.6250 | **0.0000** | **0.0000** | 0.6333 |
| **Godavari_Lower** | 48 | 20 | 12 Pos, 8 Neg | Validated Holdout | 0.5500 | 0.3333 | 0.4706 | 0.4792 |

*Holding out Singur or Godavari proves that the model fails to transfer across basins due to absolute elevation reliance.*

---

## 11. Test-Set Quality & Generalizability Assessment

* **Is the 87.5% result from Phase 11 generalizable?**
  **NO.** It reflects strong memorization of repeating road segments across recurring events.
* **Is road memorization present?**
  **YES.** Road features alone achieved 100% on the repeating-road test set, but dropped to 65.4% (ROC-AUC: 0.58) on unseen roads.
* **Is there genuine weather signal?**
  **YES.** Weather features alone achieved ROC-AUC = 0.7707 on unseen roads, proving non-trivial transferable signal exists.

---

## 12. Strategic Recommendations for Next Model & Dataset Phases

### A. Recommended Feature Changes:
1. **Drop `road_length_m`:** It is non-causal GIS noise that encourages overfitting.
2. **Replace Absolute `elevation_m` with Relative Hydrological Elevation:**
   * Calculate **Height Above Nearest Drainage (HAND)** or $\Delta \text{elevation} = \text{road\_elevation} - \text{gauge\_zero\_elevation}$.
   * Relative elevation transfers seamlessly between a river at 50 m and a river at 500 m.
3. **Incorporate Multi-Day Antecedent Rainfall:**
   * Add 3-day (`rainfall_72h_mm`) and 7-day cumulative precipitation to capture catchment runoff delays.
4. **Incorporate Catchment Upstream Hydrology:**
   * Include upstream reservoir discharge ($Q_{\text{out}}$) or upstream gauge water level rates of change ($\Delta h / \Delta t$).

### B. Recommended Dataset Improvements:
1. **Expand Road Diversity:** Expand beyond 4 segments per region so roads do not recur identically in every fold.
2. **DEM Hydrological Polygons:** Replace the crude 2,500 m circular buffer with hydrodynamic flood inundation rasters (e.g., Copernicus Water / CWC flood depth maps).

---

## 13. Final Diagnostic Verdict

**`ROAD_PROXY_DOMINATED`**

*(The high performance of Road-Only features in Phase 11 was driven by geographic proxy memorization of 5 specific road segments within the fixed gauge buffer. On unseen roads and cross-basin holdouts, static road memorization collapses, while meteorological and relative hydrological features provide the only transferable signal).*
