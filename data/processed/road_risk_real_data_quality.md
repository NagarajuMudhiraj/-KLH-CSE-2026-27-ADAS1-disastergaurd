# ADAS Phase 4 Real Data Quality & Ground-Truth Report
**Generated:** 2026-09-30T07:00:26.985911+00:00  
**Total Real Observations:** 50  
**Simulated Observations in File:** 0  
**Leakage-Free Status:** PASSED (LEAKAGE-FREE)
**Independent Ground-Truth Status:** VALID

## 1. Real vs Simulated Data Distribution
| Classification | Count | Percentage |
| :--- | :--- | :--- |
| `REAL` | 50 | 100.0% |
| `REALISTIC_SIMULATION` | 0 | 0.0% |

## 2. Independent Ground-Truth Label Coverage
| Target Class | Real Count | Share (%) | Quality Tier | Independent Source |
| :--- | :--- | :--- | :--- | :--- |
| **SAFE** | 22 | 44.0% | SILVER | FloodNet Human Semantic Annotations |
| **RISKY** | 10 | 20.0% | SILVER | FloodNet Human Semantic Annotations |
| **BLOCKED** | 18 | 36.0% | SILVER | FloodNet Human Semantic Annotations |

## 3. Ground-Truth Quality Tier Breakdown
| Quality Tier | Verified Samples | Criteria |
| :--- | :--- | :--- |
| **GOLD** | 0 | Official police / municipal road closure decrees (None accessible via live API) |
| **SILVER** | 50 | Verified FloodNet human aerial disaster image annotations |
| **BRONZE** | 0 | Crowd-sourced / automated physical heuristics |

## 4. Candidate Event-Level Partitions
| Partition | Count | Strategy |
| :--- | :--- | :--- |
| `TRAIN_CANDIDATE` | 32 | Disaster flight session / road-segment blocking |
| `VALIDATION_CANDIDATE` | 9 | Disaster flight session / road-segment blocking |
| `TEST_CANDIDATE` | 9 | Disaster flight session / road-segment blocking |

**Distinct Events Tracked:** Hurricane_Harvey_FloodNet  
**Distinct Road Segments:** 8  
**Geographic Bounding Box:** Lat [29.7604, 29.8584], Lon [-95.3698, -95.2718]

## 5. Canonical Feature Distributions (Real Observations)
| Feature Name | Min | Max | Mean | Std | Zero Rate (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `rainfall_mm_h` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `rainfall_10min_mm` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `rainfall_1h_mm` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `visibility_m` | 10000.0 | 10000.0 | 10000.0 | 0.0 | 0.0% |
| `temperature_c` | 25.4 | 25.4 | 25.4 | 0.0 | 0.0% |
| `wind_speed_kmh` | 10.7 | 10.7 | 10.7 | 0.0 | 0.0% |
| `traffic_level` | 2.0 | 2.0 | 2.0 | 0.0 | 0.0% |
| `vehicle_density` | 20.0 | 20.0 | 20.0 | 0.0 | 0.0% |
| `congestion_change` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `vehicle_speed_kmh` | 40.0 | 40.0 | 40.0 | 0.0 | 0.0% |
| `acceleration_mps2` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `braking_intensity` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `road_slope_pct` | 0.5 | 0.5 | 0.5 | 0.0 | 0.0% |
| `elevation_m` | 18.329 | 18.329 | 18.329 | 0.0 | 0.0% |
| `road_type` | 1.0 | 1.0 | 1.0 | 0.0 | 0.0% |
| `vehicle_count` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `person_count` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `fire_detected` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `smoke_detected` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `flood_detected` | 0.0 | 1.0 | 0.08 | 0.271 | 92.0% |
| `obstacle_count` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `hazard_count` | 0.0 | 1.0 | 0.58 | 0.494 | 42.0% |
| `hazard_distance_m` | 25.0 | 500.0 | 224.5 | 234.44 | 0.0% |
| `flood_report` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |
| `road_closure_report` | 0.0 | 0.0 | 0.0 | 0.0 | 100.0% |

## 6. Leakage Audit & Invariant Checks
- **Critical Leakage Violations:** 0
- **Ground-Truth Deficiencies:** 0
- **Samples Excluded / Filtered:** 0