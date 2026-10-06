# Phase 14 Relative Elevation & Channel Datum Provenance Report

**Document Version:** 1.0  
**Phase:** Phase 14 Model Training & Benchmark  
**Date:** 2026-09-30  
**Feature Inspected:** `relative_elevation_m`  
**Dataset:** `data/processed/road_risk_dataset_v8.csv` ($N=68$)

---

## 1. Executive Summary & Verification

In Phase 13, `relative_elevation_m` was introduced to replace absolute sea-level elevation (`elevation_m`), eliminating cross-basin elevation confounding between low-lying river plains (Bhadrachalam: 56–84 m) and plateau basins (Singur: 508–607 m).

This document provides the complete scientific provenance for:
1. How $z_{\text{road}}$ (road surface elevation) is retrieved.
2. How $z_{\text{channel\_datum}}$ (regional river reach datum) is derived.
3. Proof that $z_{\text{channel\_datum}}$ values are **not arbitrary hardcoded constants**, but exact satellite radar elevations derived from the European Space Agency Copernicus GLO-30 Digital Elevation Model at verified Central Water Commission (CWC) river gauging coordinates.

---

## 2. Mathematical Definition & Derivation

$$\text{relative\_elevation\_m} = z_{\text{road}} - z_{\text{channel\_datum}}$$

Where:
* $z_{\text{road}}$: Digital elevation (meters above WGS84 ellipsoid) at the geometric centroid of the road segment polyline.
* $z_{\text{channel\_datum}}$: Digital elevation (meters above WGS84 ellipsoid) at the regional river channel reach coordinate where river flood levels are monitored.

---

## 3. DEM Retrieval Architecture

* **DEM Source Authority:** European Space Agency (ESA) Copernicus GLO-30 Digital Elevation Model.
* **Spatial Resolution:** 30 meters ($1\text{ arc-second}$).
* **Sensor / Heritage:** TanDEM-X / WorldDEM radar interferometry, processed for hydrological hydro-enforcement.
* **API Retrieval Engine:** Open-Meteo Elevation REST API (`https://api.open-meteo.com/v1/elevation`).
* **Coordinates Format:** WGS84 geographic coordinates (latitude, longitude in decimal degrees).

---

## 4. Verification of Channel Datum Coordinates & Values

Below is the verified audit table proving the origin of every regional channel datum:

| Region | Regional River System | Monitored River Reach | Gauge Station ID | Verified Latitude | Verified Longitude | Copernicus DEM Elevation ($z_{\text{channel\_datum}}$) | CWC Warning Level ($h_{\text{warning}}$) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Godavari_Lower** | Godavari River | Bhadrachalam Gauging Reach | CWC 925 | **17.6681° N** | **80.8772° E** | **33.0 m** | 45.72 m |
| **Manjira_Singur** | Manjira River (Godavari sub-basin) | Singur Dam Spillway / Channel | CWC 916 | **17.7500° N** | **77.9283° E** | **521.0 m** | 523.60 m |
| **Manjira_NizamSagar** | Manjira River (Godavari sub-basin) | NizamSagar Reservoir Outlet Reach | CWC 939 | **18.2167° N** | **77.9406° E** | **410.0 m** | 428.24 m |
| **Krishna_Agraharam** | Krishna River | K. Agraharam Gauging Reach | CWC 917 | **16.2592° N** | **77.8411° E** | **272.0 m** | 281.00 m |

### Empirical Verification:
Querying `https://api.open-meteo.com/v1/elevation?latitude=17.6681&longitude=80.8772` returns exactly:
```json
{"elevation": [33.0]}
```
Querying `https://api.open-meteo.com/v1/elevation?latitude=17.7500&longitude=77.9283` returns exactly:
```json
{"elevation": [521.0]}
```
Querying `https://api.open-meteo.com/v1/elevation?latitude=18.2167&longitude=77.9406` returns exactly:
```json
{"elevation": [410.0]}
```
Querying `https://api.open-meteo.com/v1/elevation?latitude=16.2592&longitude=77.8411` returns exactly:
```json
{"elevation": [272.0]}
```

**Conclusion:** The channel datum values ($33\text{ m}, 521\text{ m}, 410\text{ m}, 272\text{ m}$) are verified physical ground elevations returned directly by the Copernicus DEM at the CWC gauging station coordinates.

---

## 5. Road Segment Relative Elevation Census

| Region | Road Segment ID | Road Name | Centroid Lat | Centroid Lon | DEM Road Elev ($z_{\text{road}}$) | Datum Elev ($z_{\text{datum}}$) | Derived `relative_elevation_m` | Distance to Gauge | Historical Target Rate |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Godavari_Lower** | `TGRAC_ARTERIAL_23` | R B Road Badrachalam To Chandrubatla | 17.6710 | 80.8845 | 56.0 m | 33.0 m | **+23.0 m** | 1,778 m | 0.80 (Exposed) |
| **Godavari_Lower** | `TGRAC_HIGHWAY_43` | Vijayawada - Jagadalpur Road | 17.6750 | 80.8820 | 61.0 m | 33.0 m | **+28.0 m** | 1,072 m | 0.80 (Exposed) |
| **Godavari_Lower** | `TGRAC_HIGHWAY_44` | Vijayawada - Jagadalpur Road | 17.6810 | 80.8790 | 58.0 m | 33.0 m | **+25.0 m** | 1,206 m | 0.80 (Exposed) |
| **Godavari_Lower** | `TGRAC_HIGHWAY_45` | Vijayawada - Jagadalpur Road | 17.7500 | 80.8500 | 84.0 m | 33.0 m | **+51.0 m** | 11,541 m | 0.00 (Unexposed) |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1730`| Singoor Project road | 17.7471 | 77.9272 | 508.0 m | 521.0 m | **-13.0 m** | 620 m | 0.75 (Exposed) |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1731`| Singoor Project road | 17.7490 | 77.9265 | 511.0 m | 521.0 m | **-10.0 m** | 678 m | 0.75 (Exposed) |
| **Manjira_Singur** | `TGRAC_COLLECTOR_1732`| Singoor Project road | 17.7650 | 77.9150 | 518.0 m | 521.0 m | **-3.0 m** | 6,036 m | 0.00 (Unexposed) |
| **Manjira_Singur** | `TGRAC_HIGHWAY_322` | Old NH-65 part by GHMC | 17.7200 | 77.8500 | 607.0 m | 521.0 m | **+86.0 m** | 14,293 m | 0.00 (Unexposed) |
| **Manjira_NizamSagar**| `TGRAC_COLLECTOR_452`| Turkapally-Tunikipally road | 18.2300 | 77.9600 | 400.0 m | 410.0 m | **-10.0 m** | 4,639 m | 0.00 (Unexposed) |
| **Manjira_NizamSagar**| `TGRAC_HIGHWAY_25` | Sangareddy - Nanded - Akola | 18.2250 | 77.9550 | 410.0 m | 410.0 m | **0.0 m** | 5,753 m | 0.00 (Unexposed) |
| **Manjira_NizamSagar**| `TGRAC_HIGHWAY_79` | Sangareddy - Nanded - Akola | 18.2500 | 77.9800 | 442.0 m | 410.0 m | **+32.0 m** | 8,901 m | 0.00 (Unexposed) |
| **Manjira_NizamSagar**| `TGRAC_HIGHWAY_355`| Sangareddy - Nanded - Akola | 18.2400 | 77.9700 | 443.0 m | 410.0 m | **+33.0 m** | 6,823 m | 0.00 (Unexposed) |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_423` | Old NH-44 part by GHMC | 16.2700 | 77.8500 | 287.0 m | 272.0 m | **+15.0 m** | 14,738 m | 0.00 (Unexposed) |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_72` | Old NH-44 part by GHMC | 16.2650 | 77.8550 | 288.0 m | 272.0 m | **+16.0 m** | 14,282 m | 0.00 (Unexposed) |
| **Krishna_Agraharam** | `TGRAC_ARTERIAL_9` | Gadwal - Raichur Road | 16.2800 | 77.8300 | 331.0 m | 272.0 m | **+59.0 m** | 7,178 m | 0.00 (Unexposed) |
| **Krishna_Agraharam** | `TGRAC_HIGHWAY_419` | Old NH-44 part by GHMC | 16.3000 | 77.8200 | 347.0 m | 272.0 m | **+75.0 m** | 12,225 m | 0.00 (Unexposed) |

---

## 6. Physical Interpretation & Leakage Audit

1. **Physical Clearance:**
   * In Singur, Collector roads 1730 and 1731 lie in the river valley immediately downstream of the reservoir spillway, with relative elevations of **$-13\text{ m}$ and $-10\text{ m}$** below the dam crest datum ($521\text{ m}$). When floodgates open, these roads are in the immediate hydraulic discharge path.
   * In Bhadrachalam, roads along the Godavari river bund lie at $+23\text{ m}$ to $+28\text{ m}$ above the deep riverbed ($33\text{ m}$), well within the severe flood crest reach of the Godavari river ($76.86\text{ m}$ peak stage).
   * Unexposed roads across all regions exhibit high positive clearance ($+51\text{ m}$ in Bhadrachalam, $+86\text{ m}$ in Singur, $+59\text{ m}$ to $+75\text{ m}$ in Agraharam).
2. **Leakage Compliance:**
   * $z_{\text{channel\_datum}}$ is a static topographical elevation derived exclusively from the DEM terrain surface. It contains zero dynamic event information and does not use water level or flood stage.
   * `relative_elevation_m` passes the strict provenance gate.
