import os
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss, confusion_matrix
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier

def get_preprocessor(numeric_features, categorical_features):
    transformers = []
    if numeric_features:
        transformers.append(('num', StandardScaler(), numeric_features))
    if categorical_features:
        transformers.append(('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features))
    return ColumnTransformer(transformers=transformers, remainder='drop')

def eval_model(pipe, X_train, y_train, X_test, y_test):
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    if hasattr(pipe, "predict_proba"):
        probs = pipe.predict_proba(X_test)[:, 1]
    else:
        probs = preds
    
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    auc = roc_auc_score(y_test, probs) if len(np.unique(y_test)) > 1 else None
    brier = brier_score_loss(y_test, probs) if hasattr(pipe, "predict_proba") else None
    cm = confusion_matrix(y_test, preds, labels=[0, 1])
    
    tn, fp, fn, tp = cm.ravel()
    return {
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1': float(f1),
        'roc_auc': float(auc) if auc is not None else None,
        'brier_score': float(brier) if brier is not None else None,
        'confusion_matrix': cm.tolist(),
        'counts': {'TP': int(tp), 'TN': int(tn), 'FP': int(fp), 'FN': int(fn)}
    }

def main():
    csv_path = os.path.join("data", "processed", "road_risk_dataset_v7.csv")
    df = pd.read_csv(csv_path)
    
    target_col = 'target_flood_exposure'
    num_cols = ['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'elevation_m', 'road_length_m']
    cat_cols = ['road_type', 'road_surface']
    all_features = num_cols + cat_cols

    print("==================================================")
    print("PHASE 12 GENERALIZATION & PROXY AUDIT")
    print("==================================================")

    # 1. Road Repeat & Overlap Analysis
    print("\n--- 1. ROAD REPEAT & OVERLAP ANALYSIS ---")
    test_events_A = ['INDOFLOODS-gauge-925-6', 'INDOFLOODS-gauge-916-11', 'INDOFLOODS-gauge-939-10', 'INDOFLOODS-gauge-917-6']
    val_events_A = ['INDOFLOODS-gauge-925-3', 'INDOFLOODS-gauge-916-8', 'BASELINE_DRY_20190315_BHADRA']
    
    train_df_A = df[~df['event_id'].isin(test_events_A + val_events_A)]
    val_df_A = df[df['event_id'].isin(val_events_A)]
    test_df_A = df[df['event_id'].isin(test_events_A)]

    train_roads_A = set(train_df_A['road_segment_id'].unique())
    val_roads_A = set(val_df_A['road_segment_id'].unique())
    test_roads_A = set(test_df_A['road_segment_id'].unique())

    print(f"Strategy A Total Unique Roads: {len(df['road_segment_id'].unique())}")
    print(f"Train Roads Count: {len(train_roads_A)}")
    print(f"Val Roads Count: {len(val_roads_A)}")
    print(f"Test Roads Count: {len(test_roads_A)}")
    print(f"Train inter Val Roads: {len(train_roads_A & val_roads_A)}")
    print(f"Train inter Test Roads: {len(train_roads_A & test_roads_A)}")
    print(f"Val inter Test Roads: {len(val_roads_A & test_roads_A)}")
    print(f"Train inter Test Events: {len(set(train_df_A['event_id'].unique()) & set(test_df_A['event_id'].unique()))}")

    # 2. Elevation Proxy Test
    print("\n--- 2. ELEVATION PROXY TEST ---")
    df['elevation_band'] = pd.cut(
        df['elevation_m'],
        bins=[-np.inf, 100, 300, 500, 700],
        labels=['<100m', '100-300m', '300-500m', '500-700m']
    )
    elev_audit = df.groupby('elevation_band', observed=False).agg(
        total_obs=('target_flood_exposure', 'count'),
        pos_obs=('target_flood_exposure', 'sum'),
        pos_rate=('target_flood_exposure', 'mean'),
        min_elev=('elevation_m', 'min'),
        max_elev=('elevation_m', 'max'),
        regions=('region', lambda s: list(s.unique()))
    ).reset_index()
    print(elev_audit.to_string())

    # 3. Road Length Proxy Test
    print("\n--- 3. ROAD LENGTH PROXY TEST ---")
    df['length_band'] = pd.cut(
        df['road_length_m'],
        bins=[-np.inf, 1000, 5000, 10000, 20000],
        labels=['<1000m', '1000-5000m', '5000-10000m', '>10000m']
    )
    length_audit = df.groupby('length_band', observed=False).agg(
        total_obs=('target_flood_exposure', 'count'),
        pos_obs=('target_flood_exposure', 'sum'),
        pos_rate=('target_flood_exposure', 'mean'),
        unique_roads=('road_segment_id', 'nunique'),
        roads=('road_segment_id', lambda s: list(s.unique()))
    ).reset_index()
    print(length_audit.to_string())

    # 4. Categorical Proxy & Confounding Test
    print("\n--- 4. CATEGORICAL PROXY & CONFOUNDING TEST ---")
    cat_audit = df.groupby(['road_type', 'road_surface']).agg(
        total_obs=('target_flood_exposure', 'count'),
        pos_obs=('target_flood_exposure', 'sum'),
        pos_rate=('target_flood_exposure', 'mean'),
        regions=('region', lambda s: list(s.unique()))
    ).reset_index()
    print(cat_audit.to_string())

    # 5. Weather Signal Analysis
    print("\n--- 5. WEATHER SIGNAL TEST ---")
    weather_audit = df.groupby('target_flood_exposure').agg(
        mean_rain=('rainfall_24h_mm', 'mean'),
        median_rain=('rainfall_24h_mm', 'median'),
        std_rain=('rainfall_24h_mm', 'std'),
        min_rain=('rainfall_24h_mm', 'min'),
        max_rain=('rainfall_24h_mm', 'max'),
        mean_temp=('temperature_c', 'mean'),
        mean_wind=('wind_speed_kmh', 'mean')
    )
    print(weather_audit.to_string())

    # Rainfall by event
    print("\nRainfall by event:")
    ev_rain = df.groupby(['region', 'event_id', 'target_flood_exposure']).agg(
        rain=('rainfall_24h_mm', 'mean'),
        count=('observation_id', 'count')
    ).reset_index()
    print(ev_rain.to_string())

    # 6. Unseen-Road Evaluation Strategy
    # Partition roads so that Train roads inter Test roads = empty
    # We must ensure test has both positive and negative instances!
    # Roads with positives:
    #   Godavari: TGRAC_ARTERIAL_23 (pos=4), TGRAC_HIGHWAY_43 (pos=4), TGRAC_HIGHWAY_44 (pos=4)
    #   Singur: TGRAC_COLLECTOR_1730 (pos=3), TGRAC_COLLECTOR_1731 (pos=3)
    # Let's hold out 1 exposed road from Godavari (TGRAC_HIGHWAY_44) + 1 exposed road from Singur (TGRAC_COLLECTOR_1731)
    # plus 2 unexposed roads from Godavari/Singur (TGRAC_HIGHWAY_45, TGRAC_COLLECTOR_1732)
    # plus 2 unexposed roads from NizamSagar/Agraharam
    print("\n--- 6. UNSEEN-ROAD EVALUATION ---")
    test_roads = ['TGRAC_HIGHWAY_44', 'TGRAC_HIGHWAY_45', 'TGRAC_COLLECTOR_1731', 'TGRAC_COLLECTOR_1732', 'TGRAC_HIGHWAY_25', 'TGRAC_HIGHWAY_419']
    train_roads = [r for r in df['road_segment_id'].unique() if r not in test_roads]

    train_unseen_road_df = df[df['road_segment_id'].isin(train_roads)]
    test_unseen_road_df = df[df['road_segment_id'].isin(test_roads)]

    print(f"Unseen-Road Train rows: {len(train_unseen_road_df)} (Pos: {(train_unseen_road_df[target_col]==1).sum()}, Neg: {(train_unseen_road_df[target_col]==0).sum()})")
    print(f"Unseen-Road Test rows: {len(test_unseen_road_df)} (Pos: {(test_unseen_road_df[target_col]==1).sum()}, Neg: {(test_unseen_road_df[target_col]==0).sum()})")
    print(f"Train Roads inter Test Roads: {set(train_roads) & set(test_roads)}")

    sp_unseen_road = (train_unseen_road_df[target_col] == 0).sum() / max(1, (train_unseen_road_df[target_col] == 1).sum())

    # Evaluate models on unseen roads
    unseen_road_models = {
        'Dummy': DummyClassifier(strategy='most_frequent'),
        'Logistic Regression': Pipeline([('prep', get_preprocessor(num_cols, cat_cols)), ('clf', LogisticRegression(max_iter=1000, random_state=42))]),
        'Decision Tree': Pipeline([('prep', get_preprocessor(num_cols, cat_cols)), ('clf', DecisionTreeClassifier(max_depth=3, random_state=42))]),
        'Random Forest': Pipeline([('prep', get_preprocessor(num_cols, cat_cols)), ('clf', RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42))]),
        'XGBoost V2': Pipeline([('prep', get_preprocessor(num_cols, cat_cols)), ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=sp_unseen_road, random_state=42, eval_metric='logloss'
        ))])
    }

    print("\nUnseen-Road Test Performance:")
    unseen_road_metrics = {}
    for mname, mobj in unseen_road_models.items():
        res = eval_model(mobj, train_unseen_road_df[all_features], train_unseen_road_df[target_col],
                         test_unseen_road_df[all_features], test_unseen_road_df[target_col])
        unseen_road_metrics[mname] = res
        print(f"{mname:22s} -> Acc: {res['accuracy']:.4f}, Prec: {res['precision']:.4f}, Rec: {res['recall']:.4f}, F1: {res['f1']:.4f}, AUC: {res['roc_auc']}, Counts: {res['counts']}")

    # 7. Feature Ablation on Unseen-Road Holdout (Configurations A through I)
    print("\n--- 7. FEATURE ABLATION ON UNSEEN-ROAD HOLDOUT ---")
    ablation_configs = {
        'A. Weather only': (['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh'], []),
        'B. Road only': (['elevation_m', 'road_length_m'], ['road_type', 'road_surface']),
        'C. Weather + Road': (num_cols, cat_cols),
        'D. Remove elevation': (['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'road_length_m'], cat_cols),
        'E. Remove road length': (['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'elevation_m'], cat_cols),
        'F. Remove road type': (num_cols, ['road_surface']),
        'G. Remove road surface': (num_cols, ['road_type']),
        'H. Elevation only': (['elevation_m'], []),
        'I. Road length only': (['road_length_m'], [])
    }

    ablation_results = {}
    print(f"{'Configuration':25s} | {'Accuracy':>8s} | {'Precision':>9s} | {'Recall':>6s} | {'F1':>6s} | {'ROC-AUC':>8s} | {'Counts (TP/TN/FP/FN)'}")
    print("-" * 85)
    for cname, (n_f, c_f) in ablation_configs.items():
        pipe = Pipeline([
            ('prep', get_preprocessor(n_f, c_f)),
            ('clf', xgb.XGBClassifier(
                n_estimators=50, max_depth=3, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_unseen_road,
                random_state=42, eval_metric='logloss'
            ))
        ])
        res = eval_model(pipe, train_unseen_road_df[n_f + c_f], train_unseen_road_df[target_col],
                         test_unseen_road_df[n_f + c_f], test_unseen_road_df[target_col])
        ablation_results[cname] = res
        auc_str = f"{res['roc_auc']:.4f}" if res['roc_auc'] is not None else "N/A"
        cnt = res['counts']
        print(f"{cname:25s} | {res['accuracy']:8.4f} | {res['precision']:9.4f} | {res['recall']:6.4f} | {res['f1']:6.4f} | {auc_str:>8s} | {cnt['TP']}/{cnt['TN']}/{cnt['FP']}/{cnt['FN']}")

    # 8. Unseen-Region + Unseen-Event Holdout (Strictest Test)
    print("\n--- 8. UNSEEN-REGION + UNSEEN-EVENT EVALUATION ---")
    for held_region in ['Krishna_Agraharam', 'Manjira_NizamSagar', 'Manjira_Singur', 'Godavari_Lower']:
        tr_df = df[df['region'] != held_region]
        te_df = df[df['region'] == held_region]
        
        pos_in_te = (te_df[target_col] == 1).sum()
        neg_in_te = (te_df[target_col] == 0).sum()
        
        print(f"\nHolding out region: {held_region}")
        print(f"  Train rows: {len(tr_df)}, Test rows: {len(te_df)} (Pos: {pos_in_te}, Neg: {neg_in_te})")
        
        if pos_in_te == 0 or neg_in_te == 0:
            print(f"  STATUS: INSUFFICIENT_POSITIVE_HOLDOUT (Only {neg_in_te} negatives, 0 positives). Metric is non-informative.")
            # Still evaluate to test false alarm rate
            pipe = Pipeline([
                ('prep', get_preprocessor(num_cols, cat_cols)),
                ('clf', xgb.XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.05, subsample=0.8,
                                          scale_pos_weight=1.0, random_state=42, eval_metric='logloss'))
            ])
            res = eval_model(pipe, tr_df[all_features], tr_df[target_col], te_df[all_features], te_df[target_col])
            print(f"  Negative Control Performance -> Acc: {res['accuracy']:.4f}, FP: {res['counts']['FP']}, TN: {res['counts']['TN']}")
        else:
            sp = (tr_df[target_col] == 0).sum() / max(1, (tr_df[target_col] == 1).sum())
            pipe = Pipeline([
                ('prep', get_preprocessor(num_cols, cat_cols)),
                ('clf', xgb.XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.05, subsample=0.8,
                                          scale_pos_weight=sp, random_state=42, eval_metric='logloss'))
            ])
            res = eval_model(pipe, tr_df[all_features], tr_df[target_col], te_df[all_features], te_df[target_col])
            auc_str = f"{res['roc_auc']:.4f}" if res['roc_auc'] is not None else "N/A"
            print(f"  Holdout Performance -> Acc: {res['accuracy']:.4f}, Prec: {res['precision']:.4f}, Rec: {res['recall']:.4f}, F1: {res['f1']:.4f}, AUC: {auc_str}, Counts: {res['counts']}")

    # Save summary json
    out_json = os.path.join("models", "road_risk_v2", "phase12_audit_results.json")
    with open(out_json, "w") as f:
        json.dump({
            'unseen_road_metrics': unseen_road_metrics,
            'ablation_results': ablation_results
        }, f, indent=2)
    print(f"\nSaved audit results to {out_json}")

if __name__ == "__main__":
    main()
