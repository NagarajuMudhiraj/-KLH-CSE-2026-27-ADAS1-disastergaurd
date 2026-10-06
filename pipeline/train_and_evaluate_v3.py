import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, precision_recall_curve, auc, brier_score_loss, confusion_matrix
from sklearn.inspection import permutation_importance
import xgboost as xgb

def get_preprocessor(numeric_features, categorical_features):
    transformers = []
    if numeric_features:
        transformers.append(('num', StandardScaler(), numeric_features))
    if categorical_features:
        transformers.append(('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features))
    return ColumnTransformer(transformers=transformers, remainder='drop')

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
    
    if len(np.unique(y_test)) > 1:
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
        'preds': preds.tolist(),
        'probs': probs.tolist()
    }

def main():
    print("==================================================")
    print("PHASE 14: XGBOOST V3 TRAINING & RIGOROUS BENCHMARK")
    print("==================================================")
    
    # 1. Verify Dataset V8 and Checksum
    v8_path = os.path.join("data", "processed", "road_risk_dataset_v8.csv")
    with open(v8_path, "rb") as f:
        actual_checksum = hashlib.sha256(f.read()).hexdigest()
    expected_checksum = "1dce0d6ef702c2159d4d0ad0a57b16ab9327eafa66267a52eacba750cd10db5c"
    assert actual_checksum == expected_checksum, f"Checksum mismatch: {actual_checksum} vs {expected_checksum}"
    print(f"Dataset V8 frozen & verified: SHA-256 = {actual_checksum}")
    
    df = pd.read_csv(v8_path)
    assert len(df) == 68, "Row count must be 68"
    assert 'road_length_m' not in df.columns, "road_length_m must remain permanently removed"
    
    # Feature set definition (9 features: 7 numeric, 2 categorical)
    num_cols = [
        'rainfall_24h_mm', 'rainfall_72h_mm', 'rainfall_7d_mm',
        'temperature_c', 'wind_speed_kmh', 'relative_elevation_m',
        'upstream_rainfall_72h_mm'
    ]
    cat_cols = ['road_type', 'road_surface']
    all_features = num_cols + cat_cols
    target_col = 'target_flood_exposure'
    
    print(f"Total Model Features: {len(all_features)} ({len(num_cols)} numeric, {len(cat_cols)} categorical)")
    print(f"Feature List: {all_features}")
    
    # 2. Evaluation Strategy A: Event-Held-Out Split
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
        ('prep', get_preprocessor(num_cols, cat_cols)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_A,
            random_state=42, eval_metric='logloss'
        ))
    ])
    
    res_val_A = eval_metrics(pipe_A, train_df_A[all_features], y_tr_A, val_df_A[all_features], y_val_A)
    res_te_A = eval_metrics(pipe_A, train_df_A[all_features], y_tr_A, test_df_A[all_features], y_te_A)
    
    print(f"Event-Held-Out Test (N=16, Pos=5, Neg=11):")
    print(f"  Acc: {res_te_A['accuracy']:.4f}, Prec: {res_te_A['precision']:.4f}, Rec: {res_te_A['recall']:.4f}, F1: {res_te_A['f1']:.4f}")
    print(f"  ROC-AUC: {res_te_A['roc_auc']:.4f}, PR-AUC: {res_te_A['pr_auc']:.4f}, Brier: {res_te_A['brier_score']:.4f}")
    print(f"  Confusion Matrix: {res_te_A['confusion_matrix']} (TP={res_te_A['counts']['TP']}, TN={res_te_A['counts']['TN']}, FP={res_te_A['counts']['FP']}, FN={res_te_A['counts']['FN']})")
    
    # 3. Evaluation Strategy B: Unseen-Road Evaluation (Anti-Memorization Benchmark)
    print("\n--- Strategy B: Unseen-Road Evaluation ---")
    test_roads_B = ['TGRAC_HIGHWAY_44', 'TGRAC_HIGHWAY_45', 'TGRAC_COLLECTOR_1731', 'TGRAC_COLLECTOR_452']
    val_roads_B = ['TGRAC_ARTERIAL_23', 'TGRAC_COLLECTOR_1732', 'TGRAC_HIGHWAY_423']
    train_roads_B = [r for r in df['road_segment_id'].unique() if r not in test_roads_B + val_roads_B]
    
    train_df_B = df[df['road_segment_id'].isin(train_roads_B)]
    val_df_B = df[df['road_segment_id'].isin(val_roads_B)]
    test_df_B = df[df['road_segment_id'].isin(test_roads_B)]
    
    y_tr_B = train_df_B[target_col].values
    y_val_B = val_df_B[target_col].values
    y_te_B = test_df_B[target_col].values
    
    sp_B = (y_tr_B == 0).sum() / max(1, (y_tr_B == 1).sum())
    
    pipe_B = Pipeline([
        ('prep', get_preprocessor(num_cols, cat_cols)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_B,
            random_state=42, eval_metric='logloss'
        ))
    ])
    
    res_val_B = eval_metrics(pipe_B, train_df_B[all_features], y_tr_B, val_df_B[all_features], y_val_B)
    res_te_B = eval_metrics(pipe_B, train_df_B[all_features], y_tr_B, test_df_B[all_features], y_te_B)
    
    print(f"Unseen-Road Test (N=18, Pos=7, Neg=11):")
    print(f"  Acc: {res_te_B['accuracy']:.4f}, Prec: {res_te_B['precision']:.4f}, Rec: {res_te_B['recall']:.4f}, F1: {res_te_B['f1']:.4f}")
    print(f"  ROC-AUC: {res_te_B['roc_auc']:.4f}, PR-AUC: {res_te_B['pr_auc']:.4f}, Brier: {res_te_B['brier_score']:.4f}")
    print(f"  Confusion Matrix: {res_te_B['confusion_matrix']} (TP={res_te_B['counts']['TP']}, TN={res_te_B['counts']['TN']}, FP={res_te_B['counts']['FP']}, FN={res_te_B['counts']['FN']})")
    
    # 4. Evaluation Strategy C: Cross-Basin Evaluation
    print("\n--- Strategy C: Cross-Basin Evaluation ---")
    # Fold A: Train on Krishna/Manjira Basin, Test on Godavari Basin
    tr_df_cb_A = df[df['region'] != 'Godavari_Lower']
    te_df_cb_A = df[df['region'] == 'Godavari_Lower']
    sp_cb_A = (tr_df_cb_A[target_col] == 0).sum() / max(1, (tr_df_cb_A[target_col] == 1).sum())
    
    pipe_cb_A = Pipeline([
        ('prep', get_preprocessor(num_cols, cat_cols)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_cb_A,
            random_state=42, eval_metric='logloss'
        ))
    ])
    res_cb_A = eval_metrics(pipe_cb_A, tr_df_cb_A[all_features], tr_df_cb_A[target_col],
                            te_df_cb_A[all_features], te_df_cb_A[target_col])
    print(f"Fold A (Krishna/Manjira -> Godavari Test, N=20, Pos=12, Neg=8):")
    print(f"  Acc: {res_cb_A['accuracy']:.4f}, Prec: {res_cb_A['precision']:.4f}, Rec: {res_cb_A['recall']:.4f}, F1: {res_cb_A['f1']:.4f}, ROC-AUC: {res_cb_A['roc_auc']:.4f}")
    print(f"  Counts: {res_cb_A['counts']}")

    # Fold B: Train on Godavari + NizamSagar + Agraharam, Test on Singur Basin
    tr_df_cb_B = df[df['region'] != 'Manjira_Singur']
    te_df_cb_B = df[df['region'] == 'Manjira_Singur']
    sp_cb_B = (tr_df_cb_B[target_col] == 0).sum() / max(1, (tr_df_cb_B[target_col] == 1).sum())
    
    pipe_cb_B = Pipeline([
        ('prep', get_preprocessor(num_cols, cat_cols)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_cb_B,
            random_state=42, eval_metric='logloss'
        ))
    ])
    res_cb_B = eval_metrics(pipe_cb_B, tr_df_cb_B[all_features], tr_df_cb_B[target_col],
                            te_df_cb_B[all_features], te_df_cb_B[target_col])
    print(f"Fold B (Godavari/NizamSagar/Agraharam -> Singur Test, N=16, Pos=6, Neg=10):")
    print(f"  Acc: {res_cb_B['accuracy']:.4f}, Prec: {res_cb_B['precision']:.4f}, Rec: {res_cb_B['recall']:.4f}, F1: {res_cb_B['f1']:.4f}, ROC-AUC: {res_cb_B['roc_auc']:.4f}")
    print(f"  Counts: {res_cb_B['counts']}")

    # 5. Combined Generalization: Unseen Roads + Unseen Event + Geographically Distinct
    print("\n--- Strategy D: Combined Generalization ---")
    # Hold out Singur test roads during Singur event 916-11
    # Train on Godavari & other regions
    comb_test = df[(df['region'] == 'Manjira_Singur') & (df['event_id'] == 'INDOFLOODS-gauge-916-11')]
    comb_train = df[(df['region'] != 'Manjira_Singur') & (df['event_id'] != 'INDOFLOODS-gauge-916-11')]
    sp_comb = (comb_train[target_col] == 0).sum() / max(1, (comb_train[target_col] == 1).sum())
    
    pipe_comb = Pipeline([
        ('prep', get_preprocessor(num_cols, cat_cols)),
        ('clf', xgb.XGBClassifier(
            n_estimators=50, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_comb,
            random_state=42, eval_metric='logloss'
        ))
    ])
    res_comb = eval_metrics(pipe_comb, comb_train[all_features], comb_train[target_col],
                            comb_test[all_features], comb_test[target_col])
    print(f"Combined Generalization (Singur Peak Event 916-11, N=4, Pos=2, Neg=2):")
    print(f"  Acc: {res_comb['accuracy']:.4f}, Prec: {res_comb['precision']:.4f}, Rec: {res_comb['recall']:.4f}, F1: {res_comb['f1']:.4f}, AUC: {res_comb['roc_auc']}")
    print(f"  Counts: {res_comb['counts']}")

    # 6. Feature Ablation Experiments on Unseen-Road Validation Split
    print("\n--- Feature Ablation Experiments (Unseen-Road Validation Split) ---")
    weather_only = ['rainfall_24h_mm', 'rainfall_72h_mm', 'rainfall_7d_mm', 'temperature_c', 'wind_speed_kmh']
    
    ablation_map = {
        'A. Weather only': (weather_only, []),
        'B. Weather + relative elevation': (weather_only + ['relative_elevation_m'], []),
        'C. Weather + upstream rainfall': (weather_only + ['upstream_rainfall_72h_mm'], []),
        'D. Weather + relative elevation + upstream rainfall': (weather_only + ['relative_elevation_m', 'upstream_rainfall_72h_mm'], []),
        'E. Full V3': (num_cols, cat_cols),
        'F. Full V3 minus relative elevation': ([c for c in num_cols if c != 'relative_elevation_m'], cat_cols),
        'G. Full V3 minus upstream rainfall': ([c for c in num_cols if c != 'upstream_rainfall_72h_mm'], cat_cols),
        'H. Full V3 minus road_type': (num_cols, ['road_surface']),
        'I. Full V3 minus road_surface': (num_cols, ['road_type'])
    }
    
    ablation_results = {}
    print(f"{'Configuration':50s} | {'Accuracy':>8s} | {'Precision':>9s} | {'Recall':>6s} | {'F1':>6s} | {'ROC-AUC':>8s} | {'Counts (TP/TN/FP/FN)'}")
    print("-" * 110)
    for cname, (n_f, c_f) in ablation_map.items():
        pipe_abl = Pipeline([
            ('prep', get_preprocessor(n_f, c_f)),
            ('clf', xgb.XGBClassifier(
                n_estimators=50, max_depth=3, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp_B,
                random_state=42, eval_metric='logloss'
            ))
        ])
        abl_res = eval_metrics(pipe_abl, train_df_B[n_f + c_f], y_tr_B, val_df_B[n_f + c_f], y_val_B)
        ablation_results[cname] = abl_res
        auc_s = f"{abl_res['roc_auc']:.4f}" if abl_res['roc_auc'] is not None else "N/A"
        cnt = abl_res['counts']
        print(f"{cname:50s} | {abl_res['accuracy']:8.4f} | {abl_res['precision']:9.4f} | {abl_res['recall']:6.4f} | {abl_res['f1']:6.4f} | {auc_s:>8s} | {cnt['TP']}/{cnt['TN']}/{cnt['FP']}/{cnt['FN']}")

    # 7. Feature Importance
    print("\n--- Feature Importance (Strategy B Unseen-Road Model) ---")
    pipe_B.fit(train_df_B[all_features], y_tr_B)
    prep = pipe_B.named_steps['prep']
    clf = pipe_B.named_steps['clf']
    
    # Feature names out of ColumnTransformer
    cat_encoder = prep.named_transformers_['cat']
    cat_feature_names = cat_encoder.get_feature_names_out(cat_cols).tolist()
    feature_names_transformed = num_cols + cat_feature_names
    
    gain_scores = clf.feature_importances_
    gain_dict = {f: float(gain_scores[i]) for i, f in enumerate(feature_names_transformed)}
    print("XGBoost Gain Importance:")
    for f, score in sorted(gain_dict.items(), key=lambda x: x[1], reverse=True):
        print(f"  {f:30s}: {score:.4f}")
        
    # Permutation importance on Validation Split
    val_trans = prep.transform(val_df_B[all_features])
    perm_val = permutation_importance(clf, val_trans, y_val_B, n_repeats=10, random_state=42)
    perm_val_dict = {feature_names_transformed[i]: float(perm_val.importances_mean[i]) for i in range(len(feature_names_transformed))}
    
    # Permutation importance on Test Split (Diagnostic only)
    test_trans = prep.transform(test_df_B[all_features])
    perm_test = permutation_importance(clf, test_trans, y_te_B, n_repeats=10, random_state=42)
    perm_test_dict = {feature_names_transformed[i]: float(perm_test.importances_mean[i]) for i in range(len(feature_names_transformed))}

    # 8. Error Analysis on Strategy B Test Set
    print("\n--- Error Analysis (Strategy B Unseen-Road Test Set) ---")
    test_df_B_copy = test_df_B.copy().reset_index(drop=True)
    test_df_B_copy['pred_label'] = res_te_B['preds']
    test_df_B_copy['pred_prob'] = [round(p, 4) for p in res_te_B['probs']]
    
    errors = test_df_B_copy[test_df_B_copy['pred_label'] != test_df_B_copy[target_col]]
    error_list = []
    print(f"Total Errors on Unseen-Road Test: {len(errors)} out of {len(test_df_B)}")
    for _, row in errors.iterrows():
        err_type = "False Positive" if row['pred_label'] == 1 else "False Negative"
        print(f"  Observation {row['observation_id']} ({row['region']}, {row['event_id']}, {row['road_segment_id']}):")
        print(f"    Type: {err_type}, True: {row[target_col]}, Pred: {row['pred_label']} (Prob: {row['pred_prob']})")
        print(f"    Features: rain24={row['rainfall_24h_mm']}mm, rain72={row['rainfall_72h_mm']}mm, rain7d={row['rainfall_7d_mm']}mm, up72={row['upstream_rainfall_72h_mm']}mm, rel_elev={row['relative_elevation_m']}m")
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
            'relative_elevation_m': float(row['relative_elevation_m']),
            'temperature_c': float(row['temperature_c']),
            'wind_speed_kmh': float(row['wind_speed_kmh']),
            'road_type': row['road_type'],
            'road_surface': row['road_surface']
        })

    # 9. Save All Model Artifacts to models/road_risk_v3/
    out_dir = os.path.join("models", "road_risk_v3")
    os.makedirs(out_dir, exist_ok=True)
    
    # Save model.json
    pipe_B.named_steps['clf'].save_model(os.path.join(out_dir, "model.json"))
    
    # Save training_config.json
    training_config = {
        'model_name': 'road_risk_v3',
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
        'objective': 'binary:logistic'
    }
    with open(os.path.join(out_dir, "training_config.json"), "w") as f:
        json.dump(training_config, f, indent=2)
        
    # Save evaluation_metrics.json
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
        'errors_unseen_road_test': error_list
    }
    with open(os.path.join(out_dir, "evaluation_metrics.json"), "w") as f:
        json.dump(eval_metrics_summary, f, indent=2)
        
    # Save ablation_results.json
    with open(os.path.join(out_dir, "ablation_results.json"), "w") as f:
        json.dump({k: {m: v for m, v in res.items() if m not in ['preds', 'probs']} for k, res in ablation_results.items()}, f, indent=2)
        
    print(f"\nSaved all artifacts to {out_dir}/ successfully.")

if __name__ == "__main__":
    main()
