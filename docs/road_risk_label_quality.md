# ADAS Road-Risk Ground-Truth Label Quality Hierarchy

**Project:** Intelligent Vehicle Assistance During Disasters (ADAS)  
**Phase:** Phase 4 — Data Population & Ground-Truth Verification  
**Standard:** Tiered Ground-Truth Assurance (GOLD / SILVER / BRONZE)

---

## 1. Principle of Independent Ground Truth

The core failure of legacy synthetic benchmarks (such as the 99.4% XGBoost baseline) was that labels were computed from the very same features given to the model (e.g., `risk_score = rainfall * 0.4 + traffic * 0.3 + water * 0.3`).

In Phase 4, ground-truth labels for `road_risk_status` (`SAFE=0`, `RISKY=1`, `BLOCKED=2`) must strictly originate from **independent observation sources** that:
1. Do not use an arbitrary mathematical formula of the input features.
2. Are separated from the vehicle's model input features.
3. Carry an explicit verification provenance and quality tier.

---

## 2. Quality Tier Definitions

```
                     ┌───────────────────────────────────────────┐
                     │            GOLD QUALITY TIER              │
                     │  Authoritative Official Municipal Decrees │
                     │  Direct Verified Physical Road Closure    │
                     └─────────────────────┬─────────────────────┘
                                           │
                     ┌─────────────────────▼─────────────────────┐
                     │           SILVER QUALITY TIER             │
                     │  Expert-Annotated Aerial Disaster Imagery │
                     │  Verified Gauge Crossing Major Flood Stage│
                     └─────────────────────┬─────────────────────┘
                                           │
                     ┌─────────────────────▼─────────────────────┐
                     │           BRONZE QUALITY TIER             │
                     │  Crowd-Sourced Reports / Municipal Advisories
                     │  Physical Multi-Sensor Consensuses        │
                     └───────────────────────────────────────────┘
```

### 2.1 GOLD Quality Tier (Authoritative / Direct Physical Verification)
- **Definition:** The ground-truth road status is established by an official government or municipal authority, legal order, or on-site physical inspection.
- **Criteria for GOLD:**
  - Official municipal police / NHAI / disaster management closure notice specifying road segment and closure window.
  - On-site road barricade or physical closure by emergency responders.
  - Multi-witness confirmed impassable roadway verified by municipal operations center.
- **Independence:** 100% independent of vehicle onboard sensors and independent of weather forecasts.
- **Model Training Role:** High-confidence benchmark for validation and testing; training samples with GOLD labels are prioritized.

### 2.2 SILVER Quality Tier (Expert-Annotated Physical Observational Data)
- **Definition:** The road status is derived from high-resolution, independently verified observational data inspected and annotated by human domain experts.
- **Criteria for SILVER:**
  - **FloodNet Expert Semantic Ground-Truth:** Human-annotated pixel-level segmentation masks proving complete road submergence (`BLOCKED`), partial water encroachment with passable lanes (`RISKY`), or clear dry pavement (`SAFE`).
  - **Hydrological River Gauge Over-topping:** USGS or state water gauge directly measuring water surface elevation exceeding known bridge/road deck elevation by $> 30\text{ cm}$.
  - Verified post-disaster reconnaissance survey records (e.g., FEMA / NDRF post-flood damage assessments).
- **Independence:** Independent of real-time onboard vehicle sensors, but spatially tied to the specific aerial or station footprint.
- **Model Training Role:** Primary volume source for complex visual-environmental disaster scenarios.

### 2.3 BRONZE Quality Tier (Crowd-Sourced / Multi-Sensor Heuristic Consensus)
- **Definition:** The road status is derived from citizen hazard reports, unverified municipal social feeds, or cross-validated physical sensor thresholds.
- **Criteria for BRONZE:**
  - Citizen report in local hazard collection (`adas_db.hazards`) without police sign-off.
  - Severe physical degradation consensus (e.g. active flood advisory + rainfall $> 35\text{ mm/h}$ + visibility $< 300\text{ m}$).
  - Social media incident reports without geocoded photo verification.
- **Independence:** Semi-independent; carries higher risk of false alarms or reporting delays.
- **Model Training Role:** Must be explicitly down-weighted or isolated into candidate exploration partitions; **cannot be used as sole evaluation ground truth**.

---

## 3. Class-Specific Mapping Standards

| Risk Class | GOLD Criteria | SILVER Criteria | BRONZE Criteria |
| :--- | :--- | :--- | :--- |
| **SAFE (0)** | Official police/NHAI notice lifting closure; verified normal traffic flow log. | Expert-annotated dry, unobstructed pavement in FloodNet imagery during disaster survey. | Zero reported hazards within 5km, clear skies, and normal ambient parameters. |
| **RISKY (1)** | Official flood advisory or speed-restriction advisory issued for corridor. | FloodNet mask showing partial roadway water coverage, with at least one lane dry/passable. | Rainfall $> 20\text{ mm/h}$ or visibility $< 500\text{ m}$ with unverified citizen hazard report. |
| **BLOCKED (2)** | Official police order declaring road closed/impassable; emergency barrier deployed. | FloodNet mask showing entire roadway width submerged under water ($> 30\text{ cm}$ depth). | Confirmed fallen high-voltage wire or citizen-reported structural bridge wash-away. |

---

## 4. Leakage Prevention Rules for Ground Truth

1. **Feature Exclusion Rule:** If a physical observation (e.g. FloodNet aerial image or gauge reading) is used as the source for a **GOLD** or **SILVER** label, that exact raw observation CANNOT be simultaneously provided as an unmasked model input feature in the same training row.
2. **No Invented Classes:** If an independent source only reports `SAFE` vs `BLOCKED` (such as a binary road closure log), the `RISKY` class must **NOT** be artificially synthesized for that observation. It remains a binary record.
3. **Distribution Consistency:** Features excluded during training due to label creation must be evaluated for inference compatibility so that production inference is not degraded.
