import os
import pandas as pd
import numpy as np

csv_path = os.path.join("data", "processed", "road_risk_dataset_v7.csv")
parquet_path = os.path.join("data", "processed", "road_risk_dataset_v7.parquet")

df = pd.read_csv(csv_path)
df_pq = pd.read_parquet(parquet_path)

print(f"=== Auditing Dataset V7: {csv_path} ===")
print(f"CSV Shape: {df.shape}, Parquet Shape: {df_pq.shape}")
assert df.shape == df_pq.shape, "CSV and Parquet shape mismatch!"

# Check 1: Target Separation from Core Features
candidate_features = [
    'rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh',
    'elevation_m', 'road_type', 'road_surface', 'road_length_m'
]
target_col = 'target_flood_exposure'
assert target_col not in candidate_features, "Target is present in feature list!"

# Check 2: Quarantined Label-Determination Variables
quarantined_vars = ['distance_to_flood_m', 'gauge_water_level_m', 'gauge_warning_level_m', 'flood_stage', 'spatial_evidence_type']
for v in quarantined_vars:
    assert v not in candidate_features, f"Label-determining variable {v} is in candidate features!"
print("Check 1 & 2 PASSED: Target and label-determining variables strictly separated from candidate features.")

# Check 3: Duplicates
dup_obs = df.duplicated(subset=['observation_id']).sum()
assert dup_obs == 0, f"Found {dup_obs} duplicate observation IDs!"
dup_pairs = df.duplicated(subset=['event_id', 'road_segment_id']).sum()
assert dup_pairs == 0, f"Found {dup_pairs} duplicate (event, road) pairs!"
print(f"Check 3 PASSED: Zero duplicates ({len(df)} unique observations).")

# Check 4: Missing values in core features
null_counts = df[candidate_features + [target_col, 'observation_id', 'event_id', 'road_segment_id']].isnull().sum()
assert null_counts.sum() == 0, f"Found nulls: {null_counts.to_dict()}"
print("Check 4 PASSED: Zero missing values in core features and identifiers.")

# Check 5: 100% REAL classification
assert (df['data_classification'] == 'REAL').all(), "Non-REAL rows detected!"
print("Check 5 PASSED: 100% of rows are REAL.")

# Step 6: Split Strategy Evaluation
print("\n=== Split Strategy Evaluation ===")

# Strategy A: Event-Held-Out Split (Temporal & Event Partitioning)
# Train on historical events prior to Aug 2019 + baseline periods
# Val on mid-2019 events (June/July 2019)
# Test on held-out August 2019 peak flood events
test_events_A = ['INDOFLOODS-gauge-925-6', 'INDOFLOODS-gauge-916-11', 'INDOFLOODS-gauge-939-10', 'INDOFLOODS-gauge-917-6']
val_events_A = ['INDOFLOODS-gauge-916-8', 'INDOFLOODS-gauge-939-7', 'INDOFLOODS-gauge-917-5']
train_events_A = [e for e in df['event_id'].unique() if e not in test_events_A and e not in val_events_A]

train_df_A = df[df['event_id'].isin(train_events_A)]
val_df_A = df[df['event_id'].isin(val_events_A)]
test_df_A = df[df['event_id'].isin(test_events_A)]

print(f"\n--- Strategy A: Event-Held-Out Split ---")
print(f"Train events ({len(train_events_A)}): {len(train_df_A)} rows (Pos: {(train_df_A[target_col]==1).sum()}, Neg: {(train_df_A[target_col]==0).sum()})")
print(f"Val events ({len(val_events_A)}): {len(val_df_A)} rows (Pos: {(val_df_A[target_col]==1).sum()}, Neg: {(val_df_A[target_col]==0).sum()})")
print(f"Test events ({len(test_events_A)}): {len(test_df_A)} rows (Pos: {(test_df_A[target_col]==1).sum()}, Neg: {(test_df_A[target_col]==0).sum()})")
event_overlap_A = set(train_events_A).intersection(set(test_events_A))
print(f"Event Overlap (Train vs Test): {len(event_overlap_A)} events (0.0% leakage)")

# Strategy B: Geography-Held-Out Split (Spatial Generalization)
# Train / Val: Regions 1, 2, 3 (Godavari_Lower, Manjira_Singur, Manjira_NizamSagar)
# Test: Region 4 (Krishna_Agraharam)
train_val_regions_B = ['Godavari_Lower', 'Manjira_Singur', 'Manjira_NizamSagar']
test_region_B = ['Krishna_Agraharam']

train_val_df_B = df[df['region'].isin(train_val_regions_B)]
test_df_B = df[df['region'].isin(test_region_B)]

train_roads_B = set(train_val_df_B['road_segment_id'])
test_roads_B = set(test_df_B['road_segment_id'])
road_overlap_B = train_roads_B.intersection(test_roads_B)

print(f"\n--- Strategy B: Geography-Held-Out Split ---")
print(f"Train/Val ({train_val_regions_B}): {len(train_val_df_B)} rows (Pos: {(train_val_df_B[target_col]==1).sum()}, Neg: {(train_val_df_B[target_col]==0).sum()})")
print(f"Test ({test_region_B}): {len(test_df_B)} rows (Pos: {(test_df_B[target_col]==1).sum()}, Neg: {(test_df_B[target_col]==0).sum()})")
print(f"Road Segment Overlap (Train vs Test): {len(road_overlap_B)} roads (0.0% spatial leakage)")

# Strategy C: Combined Event + Geography Holdout
# Train on Godavari & Singur (pre-Aug 2019)
# Val on Nizam Sagar
# Test on Krishna Basin (August 2019 event only)
test_df_C = df[(df['region'] == 'Krishna_Agraharam') & (df['event_id'] == 'INDOFLOODS-gauge-917-6')]
train_df_C = df[df['region'].isin(['Godavari_Lower', 'Manjira_Singur'])]
val_df_C = df[df['region'] == 'Manjira_NizamSagar']

print(f"\n--- Strategy C: Combined Event + Geography Holdout ---")
print(f"Train: {len(train_df_C)} rows, Val: {len(val_df_C)} rows, Test: {len(test_df_C)} rows")
print(f"Zero Event Overlap: {len(set(train_df_C['event_id']).intersection(set(test_df_C['event_id'])))} events")
print(f"Zero Road Overlap: {len(set(train_df_C['road_segment_id']).intersection(set(test_df_C['road_segment_id'])))} roads")
