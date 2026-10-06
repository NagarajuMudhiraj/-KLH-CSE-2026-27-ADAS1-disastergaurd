import os
import pandas as pd
import numpy as np

def main():
    print("=== Building Dataset V9 (Phase 15 Representation Upgrade) ===")
    v8_path = os.path.join("data", "processed", "road_risk_dataset_v8.csv")
    hand_path = os.path.join("data", "intermediate", "hand_pilot_v4.csv")
    p_path = os.path.join("data", "raw", "real", "indofloods", "precipitation_variables_indofloods.csv")
    
    df_v8 = pd.read_csv(v8_path)
    df_hand = pd.read_csv(hand_path)
    p_df = pd.read_csv(p_path)
    
    # 1. Merge HAND values
    df_v9 = df_v8.merge(df_hand[['road_segment_id', 'hand_m']], on='road_segment_id', how='left')
    assert df_v9['hand_m'].isna().sum() == 0, "All rows must have a valid HAND value"
    
    # 2. Add catchment_mean_rainfall_72h_mm from INDOFLOODS T3d
    # Map event_id to T3d in INDOFLOODS
    event_t3d_map = dict(zip(p_df['EventID'], p_df['T3d']))
    
    # For dry baseline events, catchment rainfall is 0.0 mm
    catchment_rain = []
    for _, row in df_v9.iterrows():
        ev = row['event_id']
        if ev in event_t3d_map:
            catchment_rain.append(round(float(event_t3d_map[ev]), 2))
        elif 'BASELINE_DRY' in ev:
            catchment_rain.append(0.0)
        else:
            catchment_rain.append(row['upstream_rainfall_72h_mm'])
            
    df_v9['catchment_mean_rainfall_72h_mm'] = catchment_rain
    
    # 3. Add basin identifier column
    basin_map = {
        'Godavari_Lower': 'Godavari Basin',
        'Manjira_Singur': 'Krishna Basin (Manjira Sub-basin)',
        'Manjira_NizamSagar': 'Krishna Basin (Manjira Sub-basin)',
        'Krishna_Agraharam': 'Krishna Basin (Lower Krishna Reach)'
    }
    df_v9['basin'] = df_v9['region'].map(basin_map)
    
    # 4. Map observation IDs to V9
    df_v9['observation_id'] = [f"V9_OBS_{i+1:03d}" for i in range(len(df_v9))]
    
    print(f"Dataset V9 constructed with {len(df_v9)} rows and {len(df_v9.columns)} columns.")
    print("New Representation Columns:")
    print("  - hand_m (min: {:.1f}m, max: {:.1f}m, mean: {:.1f}m)".format(df_v9['hand_m'].min(), df_v9['hand_m'].max(), df_v9['hand_m'].mean()))
    print("  - catchment_mean_rainfall_72h_mm (mean: {:.2f}mm, max: {:.2f}mm)".format(df_v9['catchment_mean_rainfall_72h_mm'].mean(), df_v9['catchment_mean_rainfall_72h_mm'].max()))
    print("Target distribution:\n", df_v9['target_flood_exposure'].value_counts())
    
    # 5. Export CSV & Parquet
    out_csv = os.path.join("data", "processed", "road_risk_dataset_v9.csv")
    out_parquet = os.path.join("data", "processed", "road_risk_dataset_v9.parquet")
    
    df_v9.to_csv(out_csv, index=False)
    df_v9.to_parquet(out_parquet, index=False)
    print(f"Exported {out_csv} and {out_parquet} successfully.")

if __name__ == "__main__":
    main()
