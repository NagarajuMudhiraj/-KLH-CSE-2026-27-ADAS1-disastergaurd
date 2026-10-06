# ADAS Road-Risk Dataset Quality Report
**Generated:** 2026-09-30T05:54:27.579936+00:00  
**Total Records Processed:** 85  
**Leakage Audit Gate:** PASSED

## 1. Target Label Distribution
| Class | Count | Share (%) |
| :--- | :--- | :--- |
| **SAFE** | 22 | 25.88% |
| **RISKY** | 45 | 52.94% |
| **BLOCKED** | 18 | 21.18% |

## 2. Source Provenance Breakdown
| Source Classification | Count | Share (%) |
| :--- | :--- | :--- |
| `REALISTIC_SIMULATION` | 85 | 100.0% |

## 3. Data Quality Tier Breakdown
| Quality Tier | Count | Share (%) |
| :--- | :--- | :--- |
| `HIGH` | 85 | 100.0% |

## 4. Canonical Feature Summary (25 Features)
| Feature Name | Min | Max | Mean | Std | Zero Rate (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `rainfall_mm_h` | 0.0 | 17.46 | 1.824 | 4.834 | 87.1% |
| `rainfall_10min_mm` | 0.0 | 22.04 | 3.873 | 6.469 | 61.2% |
| `rainfall_1h_mm` | 0.0 | 154.3 | 26.98 | 43.86 | 61.2% |
| `visibility_m` | 0.0 | 9376.4 | 4508.718 | 3716.695 | 32.9% |
| `temperature_c` | 8.9 | 32.2 | 22.595 | 4.391 | 0.0% |
| `wind_speed_kmh` | 0.0 | 56.8 | 13.172 | 13.23 | 14.1% |
| `traffic_level` | 3.0 | 3.0 | 3.0 | 0.0 | 0.0% |
| `vehicle_density` | 30.0 | 30.0 | 30.0 | 0.0 | 0.0% |
| `congestion_change` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `vehicle_speed_kmh` | 40.0 | 40.0 | 40.0 | 0.0 | 0.0% |
| `acceleration_mps2` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `braking_intensity` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `road_slope_pct` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `elevation_m` | 200.0 | 200.0 | 200.0 | 0.0 | 0.0% |
| `road_type` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `vehicle_count` | 0.0 | 5.0 | 0.647 | 1.165 | 68.2% |
| `person_count` | 0.0 | 2.0 | 0.176 | 0.513 | 88.2% |
| `fire_detected` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `smoke_detected` | 0.0 | 1.0 | 0.118 | 0.322 | 88.2% |
| `flood_detected` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `obstacle_count` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `hazard_count` | 0.0 | 3.0 | 0.588 | 0.872 | 64.7% |
| `hazard_distance_m` | 14.8 | 500.0 | 334.689 | 223.946 | 0.0% |
| `flood_report` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `road_closure_report` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |

## 5. Leakage & Invariant Audit Status
- **Valid for Ingestion:** True
- **Total Violations Detected:** 106
- **Critical Violations:** 0