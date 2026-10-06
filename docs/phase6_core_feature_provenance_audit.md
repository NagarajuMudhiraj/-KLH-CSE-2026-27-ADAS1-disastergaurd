# Phase 6 Core Feature Provenance Audit

**Decision:** no proposed core feature passes for the current V4 training set.
`road_risk_dataset_v4` is intentionally empty; this is a provenance gate, not a claim that FloodNet labels are false.

| Feature | V3 actual source/value method | Timestamp + coordinate relationship | Unit | Real historical value? | Inference path | Phase 6 classification |
|---|---|---|---|---|---|---|
| `rainfall_mm_h` | Eight literals in `build_phase5_dataset.py`, attributed to Open-Meteo ERA5 | Builder rotates hours across rows; joins to Houston centre while row coordinates are artificial | mm/h | Not verified for an image capture | Historical/realtime weather API at a real coordinate | FUTURE_PENDING_SOURCE_METADATA |
| `rainfall_1h_mm` | Same literal ERA5 slot as rate | Same failure | mm per hour interval | Not verified per observation | Same | FUTURE_PENDING_SOURCE_METADATA |
| `temperature_c` | Eight literal ERA5 samples | Same failure | °C | Not verified per observation | Same | FUTURE_PENDING_SOURCE_METADATA |
| `wind_speed_kmh` | Eight literal ERA5 samples | Same failure | km/h | Not verified per observation | Same | FUTURE_PENDING_SOURCE_METADATA |
| `traffic_level` | Constant `2.0` | No source timestamp or location | undocumented ordinal scale | **No — hardcoded** | Commercial/DOT provider may support future inference | FUTURE; excluded from real training |
| `road_slope_pct` | Constant `0.5` | No DEM sample or segment geometry | percent grade | **No — hardcoded** | DEM sampled along matched road geometry | EXCLUDED |
| `elevation_m` | One Houston-centre Open-Elevation value reused | Source coordinate is not a source-native image/road coordinate | m | Static value exists, but not for the claimed segment | DEM query at real road point | FUTURE_PENDING_GEOMETRY |
| `road_type` | Constant code `1` | No OSM way/tag relation | undocumented categorical code | **No — hardcoded** | OSM highway tag at a matched road geometry | EXCLUDED |

## Phase 5 correction

Phase 5 correctly warned about live-weather and fallback risks, but its V3 builder still writes the traffic, slope and road-type constants above, and creates each row's coordinate/time. Therefore its claim of per-observation historical alignment is not supported by the implementation.

## FloodNet limitation

FloodNet is a human-annotated, aerial, post-Hurricane-Harvey source and is SILVER ground truth for image-derived road condition. It is neither an official municipal closure feed nor a per-image road-GPS/time source in this repository. Its aerial viewpoint is also not interchangeable with the vehicle/dashcam YOLO branch. No FloodNet/YOLO feature is admitted to the first tabular model.
