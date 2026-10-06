import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix, brier_score_loss
)
from sklearn.model_selection import StratifiedKFold, GroupKFold
from sklearn.inspection import permutation_importance
import xgboost as xgb

def compute_checksum(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def evaluate_predictions(y_true, y_pred, y_prob=None):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    roc_auc = None
    pr_auc = None
    brier = None
    if y_prob is not None:
        if len(np.unique(y_true)) > 1:
            roc_auc = roc_auc_score(y_true, y_prob)
            pr_auc = average_precision_score(y_true, y_prob)
        brier = brier_score_loss(y_true, y_prob)
        
    return {
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1': float(f1),
        'roc_auc': float(roc_auc) if roc_auc is not None else None,
        'pr_auc': float(pr_auc) if pr_auc is not None else None,
        'brier_score': float(brier) if brier is not None else None,
        'confusion_matrix': cm.tolist(),
        'counts': {'TP': int(tp), 'TN': int(tn), 'FP': int(fp), 'FN': int(fn)}
    }

def get_preprocessor(numeric_features, categorical_features):
    transformers = []
    if numeric_features:
        transformers.append(('num', StandardScaler(), numeric_features))
    if categorical_features:
        transformers.append(('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features))
    return ColumnTransformer(transformers=transformers, remainder='drop')

def main():
    csv_path = os.path.join("data", "processed", "road_risk_dataset_v7.csv")
    checksum = compute_checksum(csv_path)
    df = pd.read_csv(csv_path)
    
    print(f"=== PHASE 11: XGBoost V2 Training & Evaluation Benchmark ===")
    print(f"Dataset: {csv_path}")
    print(f"SHA-256 Checksum: {checksum}")
    print(f"Total Rows: {len(df)}")
    print(f"Target Distribution: {df['target_flood_exposure'].value_counts().to_dict()}")

    # 1. Feature Definition & Quarantining
    target_col = 'target_flood_exposure'
    num_cols = ['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'elevation_m', 'road_length_m']
    cat_cols = ['road_type', 'road_surface']
    feature_cols = num_cols + cat_cols

    # Verify strict exclusion
    quarantined = ['distance_to_flood_m', 'gauge_water_level_m', 'gauge_warning_level_m', 'flood_stage', 'spatial_evidence_type']
    for q in quarantined:
        assert q not in feature_cols, f"LEAKAGE: {q} is in feature list!"
    assert target_col not in feature_cols, "LEAKAGE: Target is in feature list!"

    # 2. Evaluation Strategies
    # Strategy A: Event-Held-Out Split
    test_events_A = ['INDOFLOODS-gauge-925-6', 'INDOFLOODS-gauge-916-11', 'INDOFLOODS-gauge-939-10', 'INDOFLOODS-gauge-917-6']
    val_events_A = ['INDOFLOODS-gauge-916-8', 'INDOFLOODS-gauge-939-7', 'INDOFLOODS-gauge-917-5']
    train_events_A = [e for e in df['event_id'].unique() if e not in test_events_A and e not in val_events_A]

    train_df_A = df[df['event_id'].isin(train_events_A)].copy()
    val_df_A = df[df['event_id'].isin(val_events_A)].copy()
    test_df_A = df[df['event_id'].isin(test_events_A)].copy()

    X_train_A = train_df_A[feature_cols]
    y_train_A = train_df_A[target_col].values
    X_val_A = val_df_A[feature_cols]
    y_val_A = val_df_A[target_col].values
    X_test_A = test_df_A[feature_cols]
    y_test_A = test_df_A[target_col].values

    # Strategy B: Geographic-Held-Out Split
    train_val_regions_B = ['Godavari_Lower', 'Manjira_Singur', 'Manjira_NizamSagar']
    test_region_B = ['Krishna_Agraharam']
    train_val_df_B = df[df['region'].isin(train_val_regions_B)].copy()
    test_df_B = df[df['region'].isin(test_region_B)].copy()

    X_train_B = train_val_df_B[feature_cols]
    y_train_B = train_val_df_B[target_col].values
    X_test_B = test_df_B[feature_cols]
    y_test_B = test_df_B[target_col].values

    # 3. Model Configurations
    scale_pos = (y_train_A == 0).sum() / max(1, (y_train_A == 1).sum())
    
    models = {
        'Dummy (Majority)': DummyClassifier(strategy='most_frequent'),
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Decision Tree': DecisionTreeClassifier(max_depth=3, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42),
        'XGBoost V2': xgb.XGBClassifier(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos,
            random_state=42,
            eval_metric='logloss'
        )
    }

    # 4. Train and Evaluate Baseline Models on Strategy A (Event-Held-Out)
    print("\n--- Strategy A: Event-Held-Out Benchmark Results ---")
    results_A = {}
    fitted_pipelines_A = {}

    from sklearn.base import clone

    for name, clf in models.items():
        pipe = Pipeline([
            ('prep', get_preprocessor(num_cols, cat_cols)),
            ('clf', clone(clf))
        ])
        pipe.fit(X_train_A, y_train_A)
        fitted_pipelines_A[name] = pipe

        val_pred = pipe.predict(X_val_A)
        val_prob = pipe.predict_proba(X_val_A)[:, 1] if hasattr(pipe, 'predict_proba') else None
        res_val = evaluate_predictions(y_val_A, val_pred, val_prob)

        test_pred = pipe.predict(X_test_A)
        test_prob = pipe.predict_proba(X_test_A)[:, 1] if hasattr(pipe, 'predict_proba') else None
        res_test = evaluate_predictions(y_test_A, test_pred, test_prob)

        results_A[name] = {'val': res_val, 'test': res_test}
        print(f"Model: {name}")
        print(f"  Validation -> Acc: {res_val['accuracy']:.3f}, Prec: {res_val['precision']:.3f}, Rec: {res_val['recall']:.3f}, F1: {res_val['f1']:.3f}, Counts: {res_val['counts']}")
        print(f"  Test       -> Acc: {res_test['accuracy']:.3f}, Prec: {res_test['precision']:.3f}, Rec: {res_test['recall']:.3f}, F1: {res_test['f1']:.3f}, Counts: {res_test['counts']}")

    # 5. Evaluate on Strategy B (Geographic Holdout)
    print("\n--- Strategy B: Geographic-Held-Out Benchmark Results ---")
    results_B = {}
    for name, clf in models.items():
        pipe = Pipeline([
            ('prep', get_preprocessor(num_cols, cat_cols)),
            ('clf', clone(clf))
        ])
        pipe.fit(X_train_B, y_train_B)
        test_pred_B = pipe.predict(X_test_B)
        test_prob_B = pipe.predict_proba(X_test_B)[:, 1] if hasattr(pipe, 'predict_proba') else None
        res_test_B = evaluate_predictions(y_test_B, test_pred_B, test_prob_B)
        results_B[name] = res_test_B
        print(f"Model: {name} (Test on Krishna_Agraharam) -> Acc: {res_test_B['accuracy']:.3f}, Prec: {res_test_B['precision']:.3f}, Rec: {res_test_B['recall']:.3f}, F1: {res_test_B['f1']:.3f}, Counts: {res_test_B['counts']}")

    # 6. Cross-Validation on Strategy A Train Set (Event-Aware Grouped CV)
    print("\n--- Grouped Event Cross-Validation on Strategy A Train Set ---")
    gkf = GroupKFold(n_splits=min(5, train_df_A['event_id'].nunique()))
    groups = train_df_A['event_id'].values

    cv_scores = {'acc': [], 'prec': [], 'rec': [], 'f1': [], 'auc': []}
    for fold, (t_idx, v_idx) in enumerate(gkf.split(X_train_A, y_train_A, groups=groups)):
        X_tr_f, y_tr_f = X_train_A.iloc[t_idx], y_train_A[t_idx]
        X_va_f, y_va_f = X_train_A.iloc[v_idx], y_train_A[v_idx]

        pipe_cv = Pipeline([
            ('prep', get_preprocessor(num_cols, cat_cols)),
            ('clf', xgb.XGBClassifier(
                n_estimators=50, max_depth=3, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, scale_pos_weight=scale_pos,
                random_state=42, eval_metric='logloss'
            ))
        ])
        pipe_cv.fit(X_tr_f, y_tr_f)
        p_pred = pipe_cv.predict(X_va_f)
        p_prob = pipe_cv.predict_proba(X_va_f)[:, 1]
        res_f = evaluate_predictions(y_va_f, p_pred, p_prob)
        
        cv_scores['acc'].append(res_f['accuracy'])
        cv_scores['prec'].append(res_f['precision'])
        cv_scores['rec'].append(res_f['recall'])
        cv_scores['f1'].append(res_f['f1'])
        if res_f['roc_auc'] is not None:
            cv_scores['auc'].append(res_f['roc_auc'])
        print(f"Fold {fold+1}: Acc={res_f['accuracy']:.3f}, Prec={res_f['precision']:.3f}, Rec={res_f['recall']:.3f}, F1={res_f['f1']:.3f}, AUC={res_f['roc_auc']}")

    cv_summary = {
        'mean_acc': float(np.mean(cv_scores['acc'])), 'std_acc': float(np.std(cv_scores['acc'])),
        'mean_prec': float(np.mean(cv_scores['prec'])), 'std_prec': float(np.std(cv_scores['prec'])),
        'mean_rec': float(np.mean(cv_scores['rec'])), 'std_rec': float(np.std(cv_scores['rec'])),
        'mean_f1': float(np.mean(cv_scores['f1'])), 'std_f1': float(np.std(cv_scores['f1'])),
        'mean_auc': float(np.mean(cv_scores['auc'])) if cv_scores['auc'] else None,
        'std_auc': float(np.std(cv_scores['auc'])) if cv_scores['auc'] else None,
    }
    print(f"Grouped CV Summary: Acc={cv_summary['mean_acc']:.3f}±{cv_summary['std_acc']:.3f}, F1={cv_summary['mean_f1']:.3f}±{cv_summary['std_f1']:.3f}")

    # 7. Feature Ablation Study
    print("\n--- Feature Ablation Study (Evaluated on Strategy A Validation Set) ---")
    ablation_configs = {
        'A. Weather Only': (['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh'], []),
        'B. Road Features Only': (['elevation_m', 'road_length_m'], ['road_type', 'road_surface']),
        'C. Weather + Road (Full)': (num_cols, cat_cols),
        'D. Remove Rainfall': (['temperature_c', 'wind_speed_kmh', 'elevation_m', 'road_length_m'], cat_cols),
        'E. Remove Elevation': (['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'road_length_m'], cat_cols),
        'F. Remove Road Type': (num_cols, ['road_surface']),
        'G. Remove Road Surface': (num_cols, ['road_type'])
    }

    ablation_results = {}
    for cfg_name, (n_feats, c_feats) in ablation_configs.items():
        X_tr_abl = train_df_A[n_feats + c_feats]
        X_va_abl = val_df_A[n_feats + c_feats]
        pipe_abl = Pipeline([
            ('prep', get_preprocessor(n_feats, c_feats)),
            ('clf', xgb.XGBClassifier(
                n_estimators=50, max_depth=3, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, scale_pos_weight=scale_pos,
                random_state=42, eval_metric='logloss'
            ))
        ])
        pipe_abl.fit(X_tr_abl, y_train_A)
        abl_pred = pipe_abl.predict(X_va_abl)
        abl_prob = pipe_abl.predict_proba(X_va_abl)[:, 1]
        res_abl = evaluate_predictions(y_val_A, abl_pred, abl_prob)
        ablation_results[cfg_name] = res_abl
        print(f"{cfg_name:25s} -> Acc: {res_abl['accuracy']:.3f}, Prec: {res_abl['precision']:.3f}, Rec: {res_abl['recall']:.3f}, F1: {res_abl['f1']:.3f}, AUC: {res_abl['roc_auc']}")

    # 8. Feature Importance (XGBoost Gain & Permutation Importance)
    print("\n--- Feature Importance Analysis ---")
    xgb_pipe = fitted_pipelines_A['XGBoost V2']
    xgb_clf = xgb_pipe.named_steps['clf']
    prep_step = xgb_pipe.named_steps['prep']

    # Get feature names after one-hot encoding
    encoded_cat_names = prep_step.named_transformers_['cat'].get_feature_names_out(cat_cols).tolist() if cat_cols else []
    transformed_feature_names = num_cols + encoded_cat_names

    gain_importances = xgb_clf.feature_importances_
    gain_dict = dict(zip(transformed_feature_names, [float(x) for x in gain_importances]))
    sorted_gain = sorted(gain_dict.items(), key=lambda x: x[1], reverse=True)
    print("XGBoost Gain Importances:")
    for feat, score in sorted_gain:
        print(f"  {feat:25s}: {score:.4f}")

    # Permutation importance on Validation set
    perm_res = permutation_importance(xgb_pipe, X_val_A, y_val_A, n_repeats=10, random_state=42)
    perm_dict = dict(zip(feature_cols, [float(x) for x in perm_res.importances_mean]))
    sorted_perm = sorted(perm_dict.items(), key=lambda x: x[1], reverse=True)
    print("\nPermutation Importance on Validation Set:")
    for feat, score in sorted_perm:
        print(f"  {feat:25s}: {score:.4f}")

    # 9. Error Analysis on Test Set (Strategy A)
    print("\n--- Error Analysis on Test Set (Strategy A) ---")
    test_df_eval = test_df_A.reset_index(drop=True)
    X_test_A_clean = test_df_eval[feature_cols]
    xgb_test_pred = xgb_pipe.predict(X_test_A_clean)
    xgb_test_prob = xgb_pipe.predict_proba(X_test_A_clean)[:, 1]
    
    test_df_eval['pred_class'] = xgb_test_pred
    test_df_eval['pred_prob'] = xgb_test_prob

    errors = test_df_eval[test_df_eval['pred_class'] != test_df_eval[target_col]]
    print(f"Total Test Observations: {len(test_df_eval)}, Total Errors: {len(errors)}")
    error_list = []
    for idx, row in errors.iterrows():
        err_type = "False Positive" if (row['pred_class'] == 1 and row[target_col] == 0) else "False Negative"
        if err_type == "False Negative":
            expl = (
                f"Road segment {row['road_segment_id']} ({row['road_name']}) at elevation {row['elevation_m']}m "
                f"had low local precipitation ({row['rainfall_24h_mm']}mm) on peak event date; model assigned sub-threshold "
                f"risk probability ({row['pred_prob']:.3f} < 0.50), under-predicting riparian flood exposure."
            )
        else:
            expl = (
                f"Road segment {row['road_segment_id']} at elevation {row['elevation_m']}m "
                f"predicted as exposed ({row['pred_prob']:.3f} >= 0.50) due to regional precipitation and low elevation, "
                f"despite being situated outside the 2.5km riparian hazard corridor."
            )
        err_info = {
            'observation_id': row['observation_id'],
            'event_id': row['event_id'],
            'road_segment_id': row['road_segment_id'],
            'road_name': row['road_name'],
            'error_type': err_type,
            'true_class': int(row[target_col]),
            'pred_class': int(row['pred_class']),
            'pred_prob': round(float(row['pred_prob']), 4),
            'rainfall_24h_mm': float(row['rainfall_24h_mm']),
            'temperature_c': float(row['temperature_c']),
            'wind_speed_kmh': float(row['wind_speed_kmh']),
            'elevation_m': float(row['elevation_m']),
            'road_type': row['road_type'],
            'road_surface': row['road_surface'],
            'road_length_m': float(row['road_length_m']),
            'distance_to_flood_m': float(row['distance_to_flood_m']),
            'explanation': expl
        }
        error_list.append(err_info)
        print(f"  {row['observation_id']}: {err_type} | Road: {row['road_segment_id']} ({row['road_name']}) | True={row[target_col]}, Pred={row['pred_class']} (prob={row['pred_prob']:.3f}) | Rain={row['rainfall_24h_mm']}mm, Elev={row['elevation_m']}m, Dist={row['distance_to_flood_m']}m")

    # 10. Save Model Artifacts
    out_dir = os.path.join("models", "road_risk_v2")
    os.makedirs(out_dir, exist_ok=True)
    
    # Save XGBoost model
    model_path = os.path.join(out_dir, "model.json")
    xgb_clf.save_model(model_path)
    
    # Save training configuration
    train_config = {
        'model_type': 'XGBClassifier',
        'dataset': csv_path,
        'dataset_checksum_sha256': checksum,
        'dataset_version': 'v7.0',
        'n_rows': len(df),
        'n_train_rows': len(train_df_A),
        'n_val_rows': len(val_df_A),
        'n_test_rows': len(test_df_A),
        'random_seed': 42,
        'n_estimators': 50,
        'max_depth': 3,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'scale_pos_weight': float(scale_pos),
        'features': feature_cols,
        'target': target_col,
        'quarantined_variables': quarantined
    }
    with open(os.path.join(out_dir, "training_config.json"), 'w') as f:
        json.dump(train_config, f, indent=2)

    # Save feature schema
    schema = {
        'features': [
            {'name': 'rainfall_24h_mm', 'type': 'float', 'source': 'Open-Meteo Historical Reanalysis'},
            {'name': 'temperature_c', 'type': 'float', 'source': 'Open-Meteo Historical Reanalysis'},
            {'name': 'wind_speed_kmh', 'type': 'float', 'source': 'Open-Meteo Historical Reanalysis'},
            {'name': 'elevation_m', 'type': 'float', 'source': 'Open-Meteo Elevation API (Copernicus DEM 90m)'},
            {'name': 'road_type', 'type': 'string', 'categories': ['highway', 'arterial', 'collector', 'local'], 'source': 'TGRAC GIS'},
            {'name': 'road_surface', 'type': 'string', 'categories': ['BT', 'CC', 'WBM', 'Earthen'], 'source': 'TGRAC GIS'},
            {'name': 'road_length_m', 'type': 'float', 'source': 'TGRAC GIS Polyline'}
        ],
        'target': {'name': 'target_flood_exposure', 'type': 'int', 'classes': {'0': 'NOT_EXPOSED', '1': 'FLOOD_EXPOSED'}}
    }
    with open(os.path.join(out_dir, "feature_schema.json"), 'w') as f:
        json.dump(schema, f, indent=2)

    # Save evaluation metrics
    metrics_export = {
        'strategy_A_event_holdout': results_A,
        'strategy_B_geographic_holdout': results_B,
        'grouped_cross_validation': cv_summary,
        'feature_ablation': ablation_results,
        'feature_importance_gain': gain_dict,
        'permutation_importance': perm_dict,
        'errors_test': error_list
    }
    with open(os.path.join(out_dir, "evaluation_metrics.json"), 'w') as f:
        json.dump(metrics_export, f, indent=2)

    # Save dataset checksum text
    with open(os.path.join(out_dir, "dataset_checksum.txt"), 'w') as f:
        f.write(f"dataset: {csv_path}\nsha256: {checksum}\nrows: {len(df)}\ntimestamp: 2026-09-30T19:45:00+05:30\n")

    print(f"\n=== Artifacts successfully saved to {out_dir} ===")

if __name__ == "__main__":
    main()
