import os
import json
import pandas as pd
import numpy as np

def main():
    print("=== Building Dataset V10 (Phase 17 Hydrology & Pavement Depth Upgrade) ===")
    v9_path = os.path.join("data", "processed", "road_risk_dataset_v9.csv")
    df = pd.read_csv(v9_path)
    
    # 1. Ingest cached ERA5 volumetric soil moisture
    cache_file = os.path.join("data", "intermediate", "soil_moisture_cache.json")
    with open(cache_file, "r") as f:
        sm_cache = json.load(f)
        
    soil_moistures = []
    for _, r in df.iterrows():
        lat = round(float(r['latitude']), 4)
        lon = round(float(r['longitude']), 4)
        k = f"{r['event_date']}_{lat:.4f}_{lon:.4f}"
        soil_moistures.append(sm_cache.get(k, 0.35))
        
    df['soil_moisture_surface'] = soil_moistures
    
    # 2. Regional hydrological metadata from CWC IndoFloods
    order_map = {'Godavari_Lower': 7, 'Manjira_Singur': 5, 'Manjira_NizamSagar': 5, 'Krishna_Agraharam': 6}
    area_map = {'Godavari_Lower': 277813.9, 'Manjira_Singur': 15865.9, 'Manjira_NizamSagar': 22715.9, 'Krishna_Agraharam': 128209.9}
    mean_catchment_map = {'Godavari_Lower': 75.84, 'Manjira_Singur': 11.35, 'Manjira_NizamSagar': 13.41, 'Krishna_Agraharam': 40.09}
    mean_local_72h_map = {'Godavari_Lower': 42.4, 'Manjira_Singur': 5.9, 'Manjira_NizamSagar': 6.7, 'Krishna_Agraharam': 5.2}
    danger_map = {'Godavari_Lower': 48.77, 'Manjira_Singur': 523.60, 'Manjira_NizamSagar': 428.24, 'Krishna_Agraharam': 282.00}
    datum_bed_map = {'Godavari_Lower': 33.0, 'Manjira_Singur': 521.0, 'Manjira_NizamSagar': 410.0, 'Krishna_Agraharam': 272.0}
    
    df['stream_order'] = df['region'].map(order_map)
    df['drainage_area_km2'] = df['region'].map(area_map)
    df['regional_mean_catchment'] = df['region'].map(mean_catchment_map)
    df['regional_mean_local_72h'] = df['region'].map(mean_local_72h_map)
    
    # 3. Derived Climatological Anomalies and Coupled Hydraulic Index
    df['catchment_rain_anomaly'] = df['catchment_mean_rainfall_72h_mm'] / (df['regional_mean_catchment'] + 0.1)
    df['local_rain_anomaly'] = df['rainfall_72h_mm'] / (df['regional_mean_local_72h'] + 0.1)
    df['normalized_hand'] = df['hand_m'] / (df['stream_order'] * 2.0)
    
    # Positive vertical clearance above drainage thalweg
    h_clearance = np.maximum(0.5, df['normalized_hand'] + 3.0)
    df['hazard_ratio'] = (df['catchment_rain_anomaly'] * df['soil_moisture_surface']) / h_clearance
    df['is_dam_regulated'] = df['region'].isin(['Manjira_Singur', 'Manjira_NizamSagar']).astype(int)
    
    # 4. Solution 1: Upstream Dam Release Status (Solving Sunny-Day Dam Floods)
    events_csv = os.path.join("data", "raw", "real", "indofloods", "floodevents_indofloods.csv")
    events_df = pd.read_csv(events_csv)
    event_peak_map = dict(zip(events_df['EventID'], events_df['Peak Flood Level (m)']))
    
    dam_release_flags = []
    surge_heights = []
    for _, r in df.iterrows():
        ev = r['event_id']
        reg = r['region']
        if 'BASELINE_DRY' in ev:
            dam_release_flags.append(0)
            surge_heights.append(0.0)
        else:
            if ev in event_peak_map and not np.isnan(event_peak_map[ev]):
                peak = float(event_peak_map[ev])
                danger = danger_map[reg]
                bed = datum_bed_map[reg]
                # Dam release flag for regulated rivers
                is_releasing = 1 if (r['is_dam_regulated'] == 1 and peak >= danger) else 0
                dam_release_flags.append(is_releasing)
                surge_heights.append(round(max(0.0, peak - bed), 2))
            else:
                dam_release_flags.append(0)
                surge_heights.append(0.0)
                
    df['upstream_dam_release_active'] = dam_release_flags
    df['river_surge_height_m'] = surge_heights
    # Floodway vulnerability: Road with low terrain clearance (HAND <= 5m) downstream of active dam release
    df['dam_floodway_vulnerable'] = ((df['upstream_dam_release_active'] == 1) & (df['hand_m'] <= 5.0)).astype(int)
    
    # 5. Solution 3: Physical Pavement Submergence Depth Calculation (in cm)
    # Depth = max(0, Surge - HAND) * 100 for exposed hazard corridor reaches
    submersion_depth_cm = []
    for _, r in df.iterrows():
        if r['target_flood_exposure'] == 0:
            submersion_depth_cm.append(0.0)
        else:
            depth_m = max(0.0, r['river_surge_height_m'] - max(0.0, r['hand_m']))
            submersion_depth_cm.append(round(depth_m * 100, 1))
            
    df['pavement_water_depth_cm'] = submersion_depth_cm
    
    def get_tier(d_cm):
        if d_cm <= 0.0:
            return 'DRY_PASSABLE'
        elif d_cm <= 15.0:
            return 'SHALLOW_CAUTION'
        elif d_cm <= 30.0:
            return 'HIGH_RISK_STALL'
        else:
            return 'IMPASSABLE_SUBMERGED'
            
    df['adas_pavement_safety_tier'] = [get_tier(d) for d in submersion_depth_cm]
    
    # Observation IDs for V10
    df['observation_id'] = [f"V10_OBS_{i+1:03d}" for i in range(len(df))]
    
    print(f"Dataset V10 built with {len(df)} rows and {len(df.columns)} columns.")
    print("Safety Tier breakdown:\n", df['adas_pavement_safety_tier'].value_counts())
    print(f"Dam Release active instances: {df['upstream_dam_release_active'].sum()} / {len(df)}")
    
    out_csv = os.path.join("data", "processed", "road_risk_dataset_v10.csv")
    out_parquet = os.path.join("data", "processed", "road_risk_dataset_v10.parquet")
    df.to_csv(out_csv, index=False)
    df.to_parquet(out_parquet, index=False)
    print(f"Exported {out_csv} and {out_parquet} successfully.")

if __name__ == "__main__":
    main()
