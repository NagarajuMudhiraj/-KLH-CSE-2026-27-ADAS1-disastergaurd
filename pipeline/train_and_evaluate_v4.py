import os
import sys
import json
import time
import hashlib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc, brier_score_loss, confusion_matrix
)
from sklearn.inspection import permutation_importance
import xgboost as xgb

def get_preprocessor(numeric_features):
    return ColumnTransformer(
        transformers=[('num', StandardScaler(), numeric_features)],
        remainder='drop'
    )

def eval_metrics(pipe, X_train, y_train, X_test, y_test):
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
    
    unique_classes = np.unique(y_test)
    if len(unique_classes) > 1:
        roc_auc = float(roc_auc_score(y_test, probs))
        pr_p, pr_r, _ = precision_recall_curve(y_test, probs)
        pr_auc = float(auc(pr_r, pr_p))
    else:
        roc_auc = None
        pr_auc = None
        
    brier = float(brier_score_loss(y_test, probs)) if hasattr(pipe, "predict_proba") else None
    cm = confusion_matrix(y_test, preds, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    return {
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1': float(f1),
        'roc_auc': roc_auc,
        'pr_auc': pr_auc,
        'brier_score': brier,
        'confusion_matrix': cm.tolist(),
        'counts': {'TP': int(tp), 'TN': int(tn), 'FP': int(fp), 'FN': int(fn)},
        'class_diversity': 'INSUFFICIENT_CLASS_DIVERSITY' if len(unique_classes) <= 1 else 'SUFFICIENT',
        'preds': preds.tolist(),
        'probs': probs.tolist()
    }

def main():
    print("==================================================")
    print("PHASE 16: XGBOOST V4 HYDROLOGY TRAINING & BENCHMARK")
    print("==================================================")
    
    v9_path = os.path.join("data", "processed", "road_risk_dataset_v9.csv")
    with open(v9_path, "rb") as f:
        actual_checksum = hashlib.sha256(f.read()).hexdigest()
        
    chk_file = os.path.join("models", "road_risk_v4", "dataset_checksum.txt")
    with open(chk_file, "r") as f:
        expected_checksum = f.read().strip()
        
    assert actual_checksum == expected_checksum, f"Checksum mismatch: {actual_checksum} vs {expected_checksum}"
    print(f"Dataset V9 verified: SHA-256 = {actual_checksum}")
    
    df = pd.read_csv(v9_path)
    assert len(df) == 68, f"Row count must be 68, found {len(df)}"
    
    # Verify exact 8 V4 features
    v4_features = [
        'rainfall_24h_mm',
        'rainfall_72h_mm',
        'rainfall_7d_mm',
        'temperature_c',
        'wind_speed_kmh',
        'upstream_rainfall_72h_mm',
        'catchment_mean_rainfall_72h_mm',
        'hand_m'
    ]
    target_col = 'target_flood_exposure'
    
    assert len(v4_features) == 8, "V4 must have exactly 8 features"
    for feat in v4_features:
        assert feat in df.columns, f"Missing feature {feat}"
        assert df[feat].isna().sum() == 0, f"Nulls found in {feat}"
        
    # Check that forbidden proxy features are NOT in feature list
    forbidden = [
        'road_length_m', 'road_type', 'road_surface', 'elevation_m',
        'relative_elevation_m', 'distance_to_flood_m', 'gauge_water_level_m',
        'gauge_warning_level_m', 'flood_stage', 'flood_intersection_ratio',
        'event_id', 'road_segment_id', 'road_name', 'observation_id'
    ]
    for col in forbidden:
        assert col not in v4_features, f"Forbidden feature {col} found in V4 feature list!"
        
    print(f"Features verified ({len(v4_features)}): {v4_features}")
    print(f"Target counts: {dict(df[target_col].value_counts())}")
    
    # ----------------------------------------------------
    # Strategy A: Event-Held-Out Evaluation
    # ----------------------------------------------------
    print("\n--- Strategy A: Event-Held-Out Evaluation ---")
    test_events_A = ['INDOFLOODS-gauge-925-6', 'INDOFLOODS-gauge-916-11', 'INDOFLOODS-gauge-939-10', 'INDOFLOODS-gauge-917-6']
    val_events_A = ['INDOFLOODS-gauge-925-3', 'INDOFLOODS-gauge-916-8', 'BASELINE_DRY_20190315_BHADRA']
    
    train_df_A = df[~df['event_id'].isin(test_events_A + val_events_A)]
    val_df_A = df[df['event_id'].isin(val_events_A)]
    test_df_A = df[df['event_id'].isin(test_events_A)]
    
    y_tr_A = train_df_A[target_col].values
    y_val_A = val_df_A[target_col].values
    y_te_A = test_df_A[target_col].values
    
    sp_A = (y_tr_A == 0).sum() / max(1, (y_tr_A == 1).sum())
    
    pipe_A = Pipeline([
        ('prep', get_preprocessor(v4_features)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_A,
            random_state=42, eval_metric='logloss'
        ))
    ])
    
    res_val_A = eval_metrics(pipe_A, train_df_A[v4_features], y_tr_A, val_df_A[v4_features], y_val_A)
    res_te_A = eval_metrics(pipe_A, train_df_A[v4_features], y_tr_A, test_df_A[v4_features], y_te_A)
    
    print(f"Event-Held-Out Test (N={len(test_df_A)}, Pos={(y_te_A==1).sum()}, Neg={(y_te_A==0).sum()}):")
    print(f"  Acc: {res_te_A['accuracy']:.4f}, Prec: {res_te_A['precision']:.4f}, Rec: {res_te_A['recall']:.4f}, F1: {res_te_A['f1']:.4f}")
    print(f"  ROC-AUC: {res_te_A['roc_auc']:.4f}, PR-AUC: {res_te_A['pr_auc']:.4f}, Brier: {res_te_A['brier_score']:.4f}")
    print(f"  Confusion Matrix: {res_te_A['confusion_matrix']} (TP={res_te_A['counts']['TP']}, TN={res_te_A['counts']['TN']}, FP={res_te_A['counts']['FP']}, FN={res_te_A['counts']['FN']})")
    
    # ----------------------------------------------------
    # Strategy B: Primary Test — Unseen Roads
    # ----------------------------------------------------
    print("\n--- Strategy B: Unseen-Road Evaluation (Primary Anti-Memorization) ---")
    test_roads_B = ['TGRAC_HIGHWAY_44', 'TGRAC_HIGHWAY_45', 'TGRAC_COLLECTOR_1731', 'TGRAC_COLLECTOR_452']
    val_roads_B = ['TGRAC_ARTERIAL_23', 'TGRAC_COLLECTOR_1732', 'TGRAC_HIGHWAY_423']
    train_roads_B = [r for r in df['road_segment_id'].unique() if r not in test_roads_B + val_roads_B]
    
    train_df_B = df[df['road_segment_id'].isin(train_roads_B)]
    val_df_B = df[df['road_segment_id'].isin(val_roads_B)]
    test_df_B = df[df['road_segment_id'].isin(test_roads_B)]
    
    y_tr_B = train_df_B[target_col].values
    y_val_B = val_df_B[target_col].values
    y_te_B = test_df_B[target_col].values
    
    # Overlap assertions
    assert set(train_roads_B).intersection(set(test_roads_B)) == set(), "Road overlap between train and test!"
    assert set(train_roads_B).intersection(set(val_roads_B)) == set(), "Road overlap between train and val!"
    
    sp_B = (y_tr_B == 0).sum() / max(1, (y_tr_B == 1).sum())
    
    pipe_B = Pipeline([
        ('prep', get_preprocessor(v4_features)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_B,
            random_state=42, eval_metric='logloss'
        ))
    ])
    
    res_val_B = eval_metrics(pipe_B, train_df_B[v4_features], y_tr_B, val_df_B[v4_features], y_val_B)
    res_te_B = eval_metrics(pipe_B, train_df_B[v4_features], y_tr_B, test_df_B[v4_features], y_te_B)
    
    print(f"Unseen-Road Test (N={len(test_df_B)}, Pos={(y_te_B==1).sum()}, Neg={(y_te_B==0).sum()}):")
    print(f"  Acc: {res_te_B['accuracy']:.4f}, Prec: {res_te_B['precision']:.4f}, Rec: {res_te_B['recall']:.4f}, F1: {res_te_B['f1']:.4f}")
    print(f"  ROC-AUC: {res_te_B['roc_auc']:.4f}, PR-AUC: {res_te_B['pr_auc']:.4f}, Brier: {res_te_B['brier_score']:.4f}")
    print(f"  Confusion Matrix: {res_te_B['confusion_matrix']} (TP={res_te_B['counts']['TP']}, TN={res_te_B['counts']['TN']}, FP={res_te_B['counts']['FP']}, FN={res_te_B['counts']['FN']})")
    
    # ----------------------------------------------------
    # Strategy C: Cross-Basin Evaluation
    # ----------------------------------------------------
    print("\n--- Strategy C: Cross-Basin Evaluation ---")
    # Fold A: Train on Krishna/Manjira regions, Test on Godavari Lower region
    tr_df_cb_A = df[df['region'] != 'Godavari_Lower']
    te_df_cb_A = df[df['region'] == 'Godavari_Lower']
    sp_cb_A = (tr_df_cb_A[target_col] == 0).sum() / max(1, (tr_df_cb_A[target_col] == 1).sum())
    
    pipe_cb_A = Pipeline([
        ('prep', get_preprocessor(v4_features)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_cb_A,
            random_state=42, eval_metric='logloss'
        ))
    ])
    res_cb_A = eval_metrics(pipe_cb_A, tr_df_cb_A[v4_features], tr_df_cb_A[target_col],
                            te_df_cb_A[v4_features], te_df_cb_A[target_col])
    print(f"Fold A (Krishna/Manjira -> Godavari Test, N={len(te_df_cb_A)}, Pos={(te_df_cb_A[target_col]==1).sum()}, Neg={(te_df_cb_A[target_col]==0).sum()}):")
    print(f"  Acc: {res_cb_A['accuracy']:.4f}, Prec: {res_cb_A['precision']:.4f}, Rec: {res_cb_A['recall']:.4f}, F1: {res_cb_A['f1']:.4f}, ROC-AUC: {res_cb_A['roc_auc']}")
    print(f"  Counts: {res_cb_A['counts']}")
    
    # Fold B: Train on Godavari + NizamSagar + Agraharam, Test on Singur Basin
    tr_df_cb_B = df[df['region'] != 'Manjira_Singur']
    te_df_cb_B = df[df['region'] == 'Manjira_Singur']
    sp_cb_B = (tr_df_cb_B[target_col] == 0).sum() / max(1, (tr_df_cb_B[target_col] == 1).sum())
    
    pipe_cb_B = Pipeline([
        ('prep', get_preprocessor(v4_features)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_cb_B,
            random_state=42, eval_metric='logloss'
        ))
    ])
    res_cb_B = eval_metrics(pipe_cb_B, tr_df_cb_B[v4_features], tr_df_cb_B[target_col],
                            te_df_cb_B[v4_features], te_df_cb_B[target_col])
    print(f"Fold B (Godavari/NizamSagar/Agraharam -> Singur Test, N={len(te_df_cb_B)}, Pos={(te_df_cb_B[target_col]==1).sum()}, Neg={(te_df_cb_B[target_col]==0).sum()}):")
    print(f"  Acc: {res_cb_B['accuracy']:.4f}, Prec: {res_cb_B['precision']:.4f}, Rec: {res_cb_B['recall']:.4f}, F1: {res_cb_B['f1']:.4f}, ROC-AUC: {res_cb_B['roc_auc']}")
    print(f"  Counts: {res_cb_B['counts']}")

    # Pure Basin Column Split Check
    tr_df_basin = df[df['basin'] == 'Godavari Basin']
    te_df_basin = df[df['basin'] != 'Godavari Basin']
    print(f"Pure Basin Split (Godavari -> Krishna): Test N={len(te_df_basin)}, Pos={(te_df_basin[target_col]==1).sum()}, Neg={(te_df_basin[target_col]==0).sum()}")

    # ----------------------------------------------------
    # Strategy D: Combined Generalization
    # ----------------------------------------------------
    print("\n--- Strategy D: Combined Generalization ---")
    comb_test = df[(df['region'] == 'Manjira_Singur') & (df['event_id'] == 'INDOFLOODS-gauge-916-11')]
    comb_train = df[(df['region'] != 'Manjira_Singur') & (df['event_id'] != 'INDOFLOODS-gauge-916-11')]
    sp_comb = (comb_train[target_col] == 0).sum() / max(1, (comb_train[target_col] == 1).sum())
    
    pipe_comb = Pipeline([
        ('prep', get_preprocessor(v4_features)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_comb,
            random_state=42, eval_metric='logloss'
        ))
    ])
    res_comb = eval_metrics(pipe_comb, comb_train[v4_features], comb_train[target_col],
                            comb_test[v4_features], comb_test[target_col])
    print(f"Combined Generalization (Singur Peak Event 916-11, N={len(comb_test)}, Pos={(comb_test[target_col]==1).sum()}, Neg={(comb_test[target_col]==0).sum()}):")
    print(f"  Acc: {res_comb['accuracy']:.4f}, Prec: {res_comb['precision']:.4f}, Rec: {res_comb['recall']:.4f}, F1: {res_comb['f1']:.4f}, ROC-AUC: {res_comb['roc_auc']}")
    print(f"  Counts: {res_comb['counts']}")

    # ----------------------------------------------------
    # Feature Ablation on Validation Split (Strategy B)
    # ----------------------------------------------------
    print("\n--- Feature Ablation Experiments (Unseen-Road Validation Split) ---")
    local_weather = ['rainfall_24h_mm', 'rainfall_72h_mm', 'rainfall_7d_mm', 'temperature_c', 'wind_speed_kmh']
    
    ablation_map = {
        'A. Local weather only': local_weather,
        'B. Local weather + HAND': local_weather + ['hand_m'],
        'C. Local weather + Upstream rainfall': local_weather + ['upstream_rainfall_72h_mm'],
        'D. Local weather + Catchment rainfall': local_weather + ['catchment_mean_rainfall_72h_mm'],
        'E. Local weather + HAND + Catchment rainfall': local_weather + ['hand_m', 'catchment_mean_rainfall_72h_mm'],
        'F. Full V4 (All 8 features)': v4_features,
        'G. Full V4 minus rainfall_24h': [f for f in v4_features if f != 'rainfall_24h_mm'],
        'H. Full V4 minus rainfall_72h': [f for f in v4_features if f != 'rainfall_72h_mm'],
        'I. Full V4 minus rainfall_7d': [f for f in v4_features if f != 'rainfall_7d_mm'],
        'J. Full V4 minus upstream_rainfall': [f for f in v4_features if f != 'upstream_rainfall_72h_mm'],
        'K. Full V4 minus catchment_rainfall': [f for f in v4_features if f != 'catchment_mean_rainfall_72h_mm'],
        'L. Full V4 minus HAND': [f for f in v4_features if f != 'hand_m']
    }
    
    ablation_results = {}
    print(f"{'Configuration':52s} | {'Accuracy':>8s} | {'Precision':>9s} | {'Recall':>6s} | {'F1':>6s} | {'ROC-AUC':>8s} | {'Counts (TP/TN/FP/FN)'}")
    print("-" * 115)
    for cname, feats in ablation_map.items():
        pipe_abl = Pipeline([
            ('prep', get_preprocessor(feats)),
            ('clf', xgb.XGBClassifier(
                n_estimators=50, max_depth=3, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_B,
                random_state=42, eval_metric='logloss'
            ))
        ])
        abl_res = eval_metrics(pipe_abl, train_df_B[feats], y_tr_B, val_df_B[feats], y_val_B)
        ablation_results[cname] = abl_res
        auc_s = f"{abl_res['roc_auc']:.4f}" if abl_res['roc_auc'] is not None else "N/A"
        cnt = abl_res['counts']
        print(f"{cname:52s} | {abl_res['accuracy']:8.4f} | {abl_res['precision']:9.4f} | {abl_res['recall']:6.4f} | {abl_res['f1']:6.4f} | {auc_s:>8s} | {cnt['TP']}/{cnt['TN']}/{cnt['FP']}/{cnt['FN']}")

    # ----------------------------------------------------
    # Feature Importance (Strategy B Model)
    # ----------------------------------------------------
    print("\n--- Feature Importance (Strategy B Unseen-Road Model) ---")
    pipe_B.fit(train_df_B[v4_features], y_tr_B)
    prep_b = pipe_B.named_steps['prep']
    clf_b = pipe_B.named_steps['clf']
    
    gain_scores = clf_b.feature_importances_
    gain_dict = {f: float(gain_scores[i]) for i, f in enumerate(v4_features)}
    print("XGBoost Gain Importance:")
    for f, score in sorted(gain_dict.items(), key=lambda x: x[1], reverse=True):
        print(f"  {f:35s}: {score:.4f}")
        
    val_trans = prep_b.transform(val_df_B[v4_features])
    perm_val = permutation_importance(clf_b, val_trans, y_val_B, n_repeats=10, random_state=42)
    perm_val_dict = {v4_features[i]: float(perm_val.importances_mean[i]) for i in range(len(v4_features))}
    
    test_trans = prep_b.transform(test_df_B[v4_features])
    perm_test = permutation_importance(clf_b, test_trans, y_te_B, n_repeats=10, random_state=42)
    perm_test_dict = {v4_features[i]: float(perm_test.importances_mean[i]) for i in range(len(v4_features))}

    # ----------------------------------------------------
    # Error Analysis on Strategy B Test Set
    # ----------------------------------------------------
    print("\n--- Error Analysis (Strategy B Unseen-Road Test Set) ---")
    test_df_B_copy = test_df_B.copy().reset_index(drop=True)
    test_df_B_copy['pred_label'] = res_te_B['preds']
    test_df_B_copy['pred_prob'] = [round(p, 4) for p in res_te_B['probs']]
    
    errors = test_df_B_copy[test_df_B_copy['pred_label'] != test_df_B_copy[target_col]]
    error_list = []
    print(f"Total Errors on Unseen-Road Test: {len(errors)} out of {len(test_df_B)}")
    for _, row in errors.iterrows():
        err_type = "False Positive" if row['pred_label'] == 1 else "False Negative"
        print(f"  Obs {row['observation_id']} ({row['region']}, {row['event_id']}, {row['road_segment_id']}):")
        print(f"    Type: {err_type}, True: {row[target_col]}, Pred: {row['pred_label']} (Prob: {row['pred_prob']})")
        print(f"    Features: rain24={row['rainfall_24h_mm']}mm, rain72={row['rainfall_72h_mm']}mm, rain7d={row['rainfall_7d_mm']}mm, up72={row['upstream_rainfall_72h_mm']}mm, catch72={row['catchment_mean_rainfall_72h_mm']}mm, hand={row['hand_m']}m")
        error_list.append({
            'observation_id': row['observation_id'],
            'event_id': row['event_id'],
            'region': row['region'],
            'road_segment_id': row['road_segment_id'],
            'road_name': row['road_name'],
            'error_type': err_type,
            'true_label': int(row[target_col]),
            'pred_label': int(row['pred_label']),
            'pred_prob': float(row['pred_prob']),
            'rainfall_24h_mm': float(row['rainfall_24h_mm']),
            'rainfall_72h_mm': float(row['rainfall_72h_mm']),
            'rainfall_7d_mm': float(row['rainfall_7d_mm']),
            'upstream_rainfall_72h_mm': float(row['upstream_rainfall_72h_mm']),
            'catchment_mean_rainfall_72h_mm': float(row['catchment_mean_rainfall_72h_mm']),
            'hand_m': float(row['hand_m']),
            'temperature_c': float(row['temperature_c']),
            'wind_speed_kmh': float(row['wind_speed_kmh'])
        })

    # ----------------------------------------------------
    # Latency Benchmark
    # ----------------------------------------------------
    print("\n--- Latency Benchmark ---")
    sample_df = test_df_B[v4_features].iloc[:1]
    
    # A. Feature retrieval from memory lookup / cache
    t0 = time.perf_counter()
    for _ in range(1000):
        _ = sample_df.to_dict(orient='records')[0]
    t_retrieval_ms = ((time.perf_counter() - t0) / 1000) * 1000
    
    # B. Feature preparation (StandardScaler)
    t0 = time.perf_counter()
    for _ in range(1000):
        _ = prep_b.transform(sample_df)
    t_prep_ms = ((time.perf_counter() - t0) / 1000) * 1000
    
    # C. XGBoost model inference
    sample_trans = prep_b.transform(sample_df)
    t0 = time.perf_counter()
    for _ in range(1000):
        _ = clf_b.predict_proba(sample_trans)
    t_infer_ms = ((time.perf_counter() - t0) / 1000) * 1000
    
    t_total_ms = t_retrieval_ms + t_prep_ms + t_infer_ms
    print(f"Latency breakdown per sample (averaged over 1000 runs):")
    print(f"  A. Feature retrieval (cached/in-memory): {t_retrieval_ms:.3f} ms")
    print(f"  B. Feature preparation (StandardScaler): {t_prep_ms:.3f} ms")
    print(f"  C. XGBoost inference (predict_proba):    {t_infer_ms:.3f} ms")
    print(f"  D. Total local end-to-end latency:       {t_total_ms:.3f} ms")

    # ----------------------------------------------------
    # Save Model Artifacts
    # ----------------------------------------------------
    out_dir = os.path.join("models", "road_risk_v4")
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. model.json
    clf_b.save_model(os.path.join(out_dir, "model.json"))
    
    # 2. training_config.json
    training_config = {
        'model_name': 'road_risk_v4',
        'algorithm': 'XGBClassifier',
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'xgboost_version': xgb.__version__,
        'random_seed': 42,
        'n_estimators': 50,
        'max_depth': 3,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'scale_pos_weight': float(sp_B),
        'eval_metric': 'logloss',
        'objective': 'binary:logistic',
        'features': v4_features
    }
    with open(os.path.join(out_dir, "training_config.json"), "w") as f:
        json.dump(training_config, f, indent=2)
        
    # 3. evaluation_metrics.json
    eval_metrics_summary = {
        'strategy_A_event_held_out': {
            'validation': {k: v for k, v in res_val_A.items() if k not in ['preds', 'probs']},
            'test': {k: v for k, v in res_te_A.items() if k not in ['preds', 'probs']}
        },
        'strategy_B_unseen_road': {
            'validation': {k: v for k, v in res_val_B.items() if k not in ['preds', 'probs']},
            'test': {k: v for k, v in res_te_B.items() if k not in ['preds', 'probs']}
        },
        'strategy_C_cross_basin': {
            'fold_A_krishna_to_godavari': {k: v for k, v in res_cb_A.items() if k not in ['preds', 'probs']},
            'fold_B_godavari_to_singur': {k: v for k, v in res_cb_B.items() if k not in ['preds', 'probs']}
        },
        'strategy_D_combined_generalization': {k: v for k, v in res_comb.items() if k not in ['preds', 'probs']},
        'feature_importance_gain': gain_dict,
        'permutation_importance_validation': perm_val_dict,
        'permutation_importance_test': perm_test_dict,
        'errors_unseen_road_test': error_list,
        'latency_benchmark_ms': {
            'feature_retrieval_cached': t_retrieval_ms,
            'feature_preparation': t_prep_ms,
            'xgboost_inference': t_infer_ms,
            'total_local_end_to_end': t_total_ms
        }
    }
    with open(os.path.join(out_dir, "evaluation_metrics.json"), "w") as f:
        json.dump(eval_metrics_summary, f, indent=2)
        
    # 4. ablation_results.json
    with open(os.path.join(out_dir, "ablation_results.json"), "w") as f:
        json.dump({k: {m: v for m, v in res.items() if m not in ['preds', 'probs']} for k, res in ablation_results.items()}, f, indent=2)

    # 5. generalization_results.json
    gen_results = {
        'unseen_road': {
            'test_accuracy': res_te_B['accuracy'],
            'test_precision': res_te_B['precision'],
            'test_recall': res_te_B['recall'],
            'test_f1': res_te_B['f1'],
            'test_roc_auc': res_te_B['roc_auc'],
            'test_pr_auc': res_te_B['pr_auc'],
            'test_brier_score': res_te_B['brier_score'],
            'counts': res_te_B['counts']
        },
        'cross_basin_fold_A': {
            'test_accuracy': res_cb_A['accuracy'],
            'test_precision': res_cb_A['precision'],
            'test_recall': res_cb_A['recall'],
            'test_f1': res_cb_A['f1'],
            'test_roc_auc': res_cb_A['roc_auc'],
            'counts': res_cb_A['counts']
        },
        'cross_basin_fold_B': {
            'test_accuracy': res_cb_B['accuracy'],
            'test_precision': res_cb_B['precision'],
            'test_recall': res_cb_B['recall'],
            'test_f1': res_cb_B['f1'],
            'test_roc_auc': res_cb_B['roc_auc'],
            'counts': res_cb_B['counts']
        },
        'combined_generalization': {
            'test_accuracy': res_comb['accuracy'],
            'test_precision': res_comb['precision'],
            'test_recall': res_comb['recall'],
            'test_f1': res_comb['f1'],
            'test_roc_auc': res_comb['roc_auc'],
            'counts': res_comb['counts']
        }
    }
    with open(os.path.join(out_dir, "generalization_results.json"), "w") as f:
        json.dump(gen_results, f, indent=2)
        
    print(f"\nAll V4 artifacts saved successfully to {out_dir}/.")

if __name__ == "__main__":
    main()
