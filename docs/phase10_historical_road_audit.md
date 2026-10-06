# Phase 10 Historical Road-Network Validity Audit

**Document Version:** 1.0  
**Phase:** Phase 10 Scaling & Dataset Hardening  
**Audit Date:** 2026-09-30  
**Focus:** Mitigating Temporal Asynchrony Between Current GIS Vector Networks (TGRAC ~2020) and Historical Disaster Events (1983–2020).

---

## 1. The Core Temporal Asynchrony Problem

The road geometries used in this project originate from the **Telangana Remote Sensing Applications Centre (TGRAC / TRAC)** Roads & Buildings layer (`RnB_Folder/RnB_Roads/MapServer`). This authoritative vector GIS dataset reflects the state road infrastructure as surveyed and digitized circa **2018–2022**.

However, historical flood events in INDOFLOODS span from **1983 to 2020**.

If an observation pairs a 1983 or 1994 flood event with a rural road that was only constructed in 2012 under the Pradhan Mantri Gram Sadak Yojana (PMGSY), treating the modern polyline as "historical ground truth" is anachronistic and scientifically invalid.

---

## 2. Classification Schema for Historical Road Validity

To eliminate silent temporal back-projection, every observation in Dataset V7 is assigned an explicit attribute:
$$\text{road\_historical\_validity} \in \{\text{VERIFIED}, \text{PROBABLE}, \text{UNCERTAIN}\}$$

| Validity Tier | Definition & Engineering Criteria | Applicable Road Classes & Historical Vintages |
|---|---|---|
| **VERIFIED** | The roadway existed with confirmed spatial alignment, arterial status, and gazetted legal identity at the time of the flood event. | 1. **National Highways (NH)**: Arterial routes gazetted prior to the event (e.g. NH-30 / old NH-221, NH-65 / old NH-9) for events between 2000–2020.<br>2. **State Highways (SH)**: Major state routes (e.g. SH-12 Bhadrachalam corridor) for events between 2005–2020.<br>3. **Any road segment** observed during events from **2016 to 2020** (contemporary with TGRAC baseline). |
| **PROBABLE** | The roadway follows an established physical right-of-way, village-to-market connection, or major district road that predates the modern surface, though minor widening or realignment may have occurred. | 1. **Major District Roads (MDR)**: Established inter-mandal connectors (e.g. MDR-60 Singoor Project Road) for events between 2005–2015.<br>2. **State Highways** for events between 2000–2005.<br>3. **Documented rural roads** with PMGSY Phase 1 registration (`DRRP_ID_PMGSY1 > 0`) for events post-2005. |
| **UNCERTAIN** | The roadway cannot be confirmed to have existed in its modern paved vector form at the time of the event; likely was an unpaved cart-track, newly opened greenfield alignment, or built decades after the event. | 1. **All Pre-2000 Events** (e.g., 1983, 1984, 1990 events at Jewangi, 1994, 1998 at K. Agraharam).<br>2. **Local / Other District Roads (ODR)** paired with events prior to 2010 where PMGSY construction dates are unknown.<br>3. **Proposed roads** or roads flagged as unpaved earthen tracks (`Road_Surface = Earthen`) in older event windows. |

---

## 3. Policy on Evaluation and Model Training

1. **Benchmark Exclusion:** All rows flagged as `UNCERTAIN` must be **excluded** from high-integrity evaluation and test sets.
2. **Core Training Preference:** Model training sets must draw preferentially from `VERIFIED` and `PROBABLE` observations.
3. **No Silent Upgrades:** If a road's historical presence is unverified, it must not be labeled `VERIFIED`.

---

## 4. Empirical Audit of Phase 10 Candidate Road Segments

* **National Highways (NH-30, NH-65):** `VERIFIED`. NH-30 has served as the sole interstate artery through Bhadrachalam across Andhra Pradesh/Telangana and Chhattisgarh for over 40 years.
* **State Highways (SH-12):** `VERIFIED`. Established PWD/R&B corridor linking Khammam, Kothagudem, and Bhadrachalam.
* **MDR-60 (Singoor Project Road):** `VERIFIED` for 2019/2020 events; `PROBABLE` for older events. Built during initial Singur Dam irrigation works (commissioned 1989).
* **Jewangi & K. Agraharam 1980s/1990s rural roads:** `UNCERTAIN`. Pre-2000 rural connections in these basins have been filtered out of the core eligible event set.
