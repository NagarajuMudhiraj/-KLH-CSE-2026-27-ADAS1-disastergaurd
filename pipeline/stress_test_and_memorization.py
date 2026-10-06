import os
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss
import xgboost as xgb

def get_preprocessor(numeric_features, categorical_features):
    transformers = []
    if numeric_features:
        transformers.append(('num', StandardScaler(), numeric_features))
    if categorical_features:
        transformers.append(('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features))
    return ColumnTransformer(transformers=transformers, remainder='drop')

def main():
    csv_path = os.path.join("data", "processed", "road_risk_dataset_v7.csv")
    df = pd.read_csv(csv_path)
    
    num_cols = ['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh', 'elevation_m', 'road_length_m']
    cat_cols = ['road_type', 'road_surface']
    target_col = 'target_flood_exposure'

    # 1. Leave-One-Event-Out Stress Test
    # Only test events that have at least 1 positive and 1 negative, or evaluate across all 9 flood events
    flood_events = [e for e in df['event_id'].unique() if not e.startswith('BASELINE_')]
    print(f"=== Leave-One-Event-Out Stress Test ({len(flood_events)} Flood Events) ===")
    
    loo_results = []
    for held_out in flood_events:
        train_df = df[df['event_id'] != held_out]
        test_df = df[df['event_id'] == held_out]
        
        y_train = train_df[target_col].values
        y_test = test_df[target_col].values
        
        scale_pos = (y_train == 0).sum() / max(1, (y_train == 1).sum())
        
        pipe = Pipeline([
            ('prep', get_preprocessor(num_cols, cat_cols)),
            ('clf', xgb.XGBClassifier(
                n_estimators=50, max_depth=3, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, scale_pos_weight=scale_pos,
                random_state=42, eval_metric='logloss'
            ))
        ])
        pipe.fit(train_df[num_cols + cat_cols], y_train)
        preds = pipe.predict(test_df[num_cols + cat_cols])
        probs = pipe.predict_proba(test_df[num_cols + cat_cols])[:, 1]
        
        acc = accuracy_score(y_test, preds)
        rec = recall_score(y_test, preds, zero_division=0)
        prec = precision_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        
        loo_results.append({
            'held_out_event': held_out,
            'region': test_df['region'].iloc[0],
            'n_rows': len(test_df),
            'pos_count': int((y_test == 1).sum()),
            'neg_count': int((y_test == 0).sum()),
            'accuracy': float(acc),
            'precision': float(prec),
            'recall': float(rec),
            'f1': float(f1)
        })
        print(f"Held out {held_out:25s} ({test_df['region'].iloc[0]}): Acc={acc:.3f}, Prec={prec:.3f}, Rec={rec:.3f}, F1={f1:.3f} (Pos={int((y_test==1).sum())}, Neg={int((y_test==0).sum())})")

    df_loo = pd.DataFrame(loo_results)
    print("\nLOO Stress Test Mean Metrics:")
    print(df_loo[['accuracy', 'precision', 'recall', 'f1']].mean().to_dict())

    # 2. Road-ID Memorization & Proxy Audit
    print("\n=== Road-ID Memorization & Proxy Audit ===")
    # Split into 80/20 train/test
    # Model A: Full (Weather + Road)
    # Model B: Weather Only
    # Model C: Road Only
    test_events_A = ['INDOFLOODS-gauge-925-6', 'INDOFLOODS-gauge-916-11', 'INDOFLOODS-gauge-939-10', 'INDOFLOODS-gauge-917-6']
    train_df = df[~df['event_id'].isin(test_events_A)]
    test_df = df[df['event_id'].isin(test_events_A)]
    
    y_tr = train_df[target_col].values
    y_te = test_df[target_col].values
    sp = (y_tr == 0).sum() / max(1, (y_tr == 1).sum())

    configs = {
        'Model A (Weather + Road)': (num_cols, cat_cols),
        'Model B (Weather Only)': (['rainfall_24h_mm', 'temperature_c', 'wind_speed_kmh'], []),
        'Model C (Road Only)': (['elevation_m', 'road_length_m'], ['road_type', 'road_surface'])
    }
    
    mem_results = {}
    for cname, (n_f, c_f) in configs.items():
        pipe = Pipeline([
            ('prep', get_preprocessor(n_f, c_f)),
            ('clf', xgb.XGBClassifier(
                n_estimators=50, max_depth=3, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, scale_pos_weight=sp,
                random_state=42, eval_metric='logloss'
            ))
        ])
        pipe.fit(train_df[n_f + c_f], y_tr)
        preds = pipe.predict(test_df[n_f + c_f])
        probs = pipe.predict_proba(test_df[n_f + c_f])[:, 1]
        
        acc = accuracy_score(y_te, preds)
        prec = precision_score(y_te, preds, zero_division=0)
        rec = recall_score(y_te, preds, zero_division=0)
        f1 = f1_score(y_te, preds, zero_division=0)
        auc = roc_auc_score(y_te, probs) if len(np.unique(y_te)) > 1 else None
        brier = brier_score_loss(y_te, probs)
        
        mem_results[cname] = {
            'accuracy': float(acc), 'precision': float(prec), 'recall': float(rec),
            'f1': float(f1), 'roc_auc': float(auc) if auc is not None else None,
            'brier_score': float(brier)
        }
        print(f"{cname:25s} -> Acc: {acc:.3f}, Prec: {prec:.3f}, Rec: {rec:.3f}, F1: {f1:.3f}, AUC: {auc:.3f}, Brier: {brier:.4f}")

    # Export to models/road_risk_v2/stress_test_metrics.json
    out_json = os.path.join("models", "road_risk_v2", "stress_test_metrics.json")
    with open(out_json, 'w') as f:
        json.dump({'leave_one_event_out': loo_results, 'memorization_comparison': mem_results}, f, indent=2)
    print(f"\nSaved stress test results to {out_json}")

if __name__ == "__main__":
    main()
