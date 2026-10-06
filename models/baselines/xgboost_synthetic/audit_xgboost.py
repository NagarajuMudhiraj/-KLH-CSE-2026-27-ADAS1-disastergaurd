import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from xgboost import XGBClassifier

# Import data generator from train_xgboost
from training.train_xgboost import generate_synthetic_road_data

def run_complete_audit():
    print("=================================================================")
    print("       AUDIT OF XGBOOST ROAD SAFETY CLASSIFICATION MODEL         ")
    print("=================================================================\n")

    # -------------------------------------------------------------
    # 1. DATASET AUDIT
    # -------------------------------------------------------------
    print("### SECTION 1: DATASET AUDIT ###")
    df = generate_synthetic_road_data(n_samples=2500, random_seed=42)
    
    n_samples, n_cols = df.shape
    features = ['rainfall', 'traffic', 'water_level']
    target = 'status'
    
    print(f"Total samples: {n_samples}")
    print(f"Number of features: {len(features)} ({features})")
    print(f"Target column: {target}")
    
    class_dist = df[target].value_counts().sort_index()
    class_pct = df[target].value_counts(normalize=True).sort_index() * 100
    class_names = {0: 'Safe', 1: 'Risky', 2: 'Blocked'}
    print("\nTarget Class Distribution:")
    for c in sorted(class_dist.index):
        print(f"  Class {c} ({class_names[c]}): {class_dist[c]} samples ({class_pct[c]:.2f}%)")
        
    # Missing values
    missing = df.isnull().sum()
    print("\nMissing values per column:")
    for col, count in missing.items():
        print(f"  {col}: {count}")
        
    # Duplicate rows
    dup_rows = df.duplicated().sum()
    dup_features = df.duplicated(subset=features).sum()
    print(f"\nExact duplicate rows: {dup_rows}")
    print(f"Duplicate feature vectors: {dup_features}")
    
    # Duplicate feature vectors with different labels
    dup_diff_labels = df.groupby(features)[target].nunique()
    conflict_count = (dup_diff_labels > 1).sum()
    print(f"Duplicate feature vectors with conflicting labels: {conflict_count}")
    
    # Constant or near constant features
    print("\nFeature Descriptive Statistics:")
    print(df[features].describe().T[['mean', 'std', 'min', '50%', 'max']])
    
    # Check if target column or risk_score in features
    print("\nFeature list provided to model: ", features)
    print("Target column in X?", target in features)
    print("Is 'risk_score' explicitly in df columns?", 'risk_score' in df.columns)

    # -------------------------------------------------------------
    # 2. DATA LEAKAGE & TRAIN/TEST SPLIT AUDIT
    # -------------------------------------------------------------
    print("\n### SECTION 2 & 3: TRAIN / TEST SPLIT AUDIT ###")
    X = df[features]
    y = df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train sample count: {len(X_train)} (80%)")
    print(f"Test sample count:  {len(X_test)} (20%)")
    print(f"Split random seed: 42")
    print(f"Stratification used: Yes")
    
    # Overlapping samples between train and test
    overlap = pd.merge(X_train, X_test, how='inner')
    print(f"Samples overlapping between train and test: {len(overlap)}")

    # -------------------------------------------------------------
    # 4. MULTIPLE METRICS EVALUATION ON TEST SET
    # -------------------------------------------------------------
    print("\n### SECTION 4: UNTOUCHED TEST SET EVALUATION ###")
    # Load original saved model
    with open("models/road_model.pkl", "rb") as f:
        model = pickle.load(f)
        
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    
    test_acc = accuracy_score(y_test, y_pred)
    test_prec_macro = precision_score(y_test, y_pred, average='macro')
    test_rec_macro = recall_score(y_test, y_pred, average='macro')
    test_f1_macro = f1_score(y_test, y_pred, average='macro')
    test_prec_weighted = precision_score(y_test, y_pred, average='weighted')
    test_rec_weighted = recall_score(y_test, y_pred, average='weighted')
    test_f1_weighted = f1_score(y_test, y_pred, average='weighted')
    test_roc_auc_ovr = roc_auc_score(y_test, y_prob, multi_class='ovr', average='macro')
    
    print(f"Accuracy:        {test_acc:.4f} ({test_acc*100:.2f}%)")
    print(f"Precision (Macro): {test_prec_macro:.4f}")
    print(f"Recall (Macro):    {test_rec_macro:.4f}")
    print(f"F1-Score (Macro):  {test_f1_macro:.4f}")
    print(f"ROC-AUC (Macro OVR): {test_roc_auc_ovr:.4f}")
    print(f"Weighted F1:     {test_f1_weighted:.4f}")
    
    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix:")
    print("Pred ->   Safe  Risky  Blocked")
    print(f"Actual Safe:    {cm[0][0]:4d}   {cm[0][1]:4d}     {cm[0][2]:4d}")
    print(f"Actual Risky:   {cm[1][0]:4d}   {cm[1][1]:4d}     {cm[1][2]:4d}")
    print(f"Actual Blocked: {cm[2][0]:4d}   {cm[2][1]:4d}     {cm[2][2]:4d}")
    
    print("\nPer-Class Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Safe', 'Risky', 'Blocked'], digits=4))

    # Misclassified samples inspection
    misclassified_idx = y_test[y_test != y_pred].index
    print(f"Total misclassified test samples: {len(misclassified_idx)} / {len(y_test)}")
    for idx in misclassified_idx:
        row = df.loc[idx]
        actual = class_names[row['status']]
        pred = class_names[model.predict([row[features]])[0]]
        calc_risk = (row['rainfall']*0.3) + (row['traffic']*4.0) + (row['water_level']*1.2)
        print(f"  Sample #{idx}: Rainfall={row['rainfall']:.2f}, Traffic={row['traffic']:.2f}, WaterLevel={row['water_level']:.2f} | Calc Risk={calc_risk:.2f} | Actual={actual} ({row['status']}), Predicted={pred}")

    # -------------------------------------------------------------
    # 5. CROSS-VALIDATION ON TRAINING SET
    # -------------------------------------------------------------
    print("\n### SECTION 5: 5-FOLD STRATIFIED CROSS-VALIDATION ###")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    xgb_cv = XGBClassifier(
        n_estimators=100, max_depth=5, learning_rate=0.1,
        random_state=42, eval_metric='mlogloss'
    )
    
    scoring = ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro', 'roc_auc_ovr']
    cv_results = cross_validate(xgb_cv, X_train, y_train, cv=skf, scoring=scoring)
    
    print("Fold-by-Fold Test Accuracies:")
    for fold, acc in enumerate(cv_results['test_accuracy'], 1):
        print(f"  Fold {fold}: {acc*100:.2f}%")
        
    print(f"Mean Accuracy:    {cv_results['test_accuracy'].mean()*100:.2f}% (+/- {cv_results['test_accuracy'].std()*100:.2f}%)")
    print(f"Mean Precision:   {cv_results['test_precision_macro'].mean():.4f}")
    print(f"Mean Recall:      {cv_results['test_recall_macro'].mean():.4f}")
    print(f"Mean F1-Score:    {cv_results['test_f1_macro'].mean():.4f}")
    print(f"Mean ROC-AUC:     {cv_results['test_roc_auc_ovr'].mean():.4f}")

    # -------------------------------------------------------------
    # 6. BASELINE COMPARISON
    # -------------------------------------------------------------
    print("\n### SECTION 6: BASELINE MODEL COMPARISON ###")
    baselines = {
        "Dummy (Most Frequent)": DummyClassifier(strategy='most_frequent'),
        "Dummy (Stratified)": DummyClassifier(strategy='stratified', random_state=42),
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Decision Tree (Depth=5)": DecisionTreeClassifier(max_depth=5, random_state=42),
        "Random Forest (n=100, Depth=5)": RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
        "XGBoost (Audited)": XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, eval_metric='mlogloss')
    }
    
    baseline_records = []
    for name, b_model in baselines.items():
        b_model.fit(X_train, y_train)
        preds = b_model.predict(X_test)
        probs = b_model.predict_proba(X_test) if hasattr(b_model, "predict_proba") else None
        
        acc = accuracy_score(y_test, preds)
        p_macro = precision_score(y_test, preds, average='macro', zero_division=0)
        r_macro = recall_score(y_test, preds, average='macro', zero_division=0)
        f1_m = f1_score(y_test, preds, average='macro', zero_division=0)
        auc_m = roc_auc_score(y_test, probs, multi_class='ovr', average='macro') if probs is not None else 0.5
        
        baseline_records.append({
            "Model": name,
            "Accuracy": f"{acc*100:.2f}%",
            "Precision (Macro)": f"{p_macro:.4f}",
            "Recall (Macro)": f"{r_macro:.4f}",
            "F1 (Macro)": f"{f1_m:.4f}",
            "ROC-AUC": f"{auc_m:.4f}"
        })
        
    print(pd.DataFrame(baseline_records).to_string(index=False))

    # -------------------------------------------------------------
    # 7. FEATURE IMPORTANCE
    # -------------------------------------------------------------
    print("\n### SECTION 7: FEATURE IMPORTANCE & PERMUTATION IMPORTANCE ###")
    importances = model.feature_importances_
    perm_res = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)
    
    feat_df = pd.DataFrame({
        'Feature': features,
        'XGBoost Importance (Gini/Gain)': importances,
        'Permutation Importance Mean': perm_res.importances_mean,
        'Permutation Importance Std': perm_res.importances_std
    }).sort_values(by='Permutation Importance Mean', ascending=False)
    
    print(feat_df.to_string(index=False))

    # -------------------------------------------------------------
    # 8. SYNTHETIC DATASET INVESTIGATION
    # -------------------------------------------------------------
    print("\n### SECTION 8: SYNTHETIC DATASET MECHANISM AUDIT ###")
    print("Exact rule in train_xgboost.py:")
    print("  risk_score = (rainfall * 0.3) + (traffic * 4.0) + (water_level * 1.2)")
    print("  if wl > 50 or r_score > 120 or rf > 100: label = 2 (Blocked)")
    print("  elif wl > 20 or r_score > 65 or rf > 40: label = 1 (Risky)")
    print("  else: label = 0 (Safe)")
    print("Notice: The target is a ZERO-NOISE, 100% deterministic function of the exact 3 features!")

    # -------------------------------------------------------------
    # 9. LEAKAGE & ABLATION EXPERIMENT
    # -------------------------------------------------------------
    print("\n### SECTION 9: ABLATION EXPERIMENTS ###")
    ablations = {
        "A. Full Model (All 3 Features)": ['rainfall', 'traffic', 'water_level'],
        "B. Remove water_level": ['rainfall', 'traffic'],
        "C. Remove rainfall": ['traffic', 'water_level'],
        "D. Remove traffic": ['rainfall', 'water_level'],
        "E. Only water_level": ['water_level'],
        "F. Only rainfall": ['rainfall'],
        "G. Only traffic": ['traffic']
    }
    
    ablation_records = []
    for ab_name, ab_feats in ablations.items():
        m_ab = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, eval_metric='mlogloss')
        m_ab.fit(X_train[ab_feats], y_train)
        pred_ab = m_ab.predict(X_test[ab_feats])
        acc_ab = accuracy_score(y_test, pred_ab)
        f1_ab = f1_score(y_test, pred_ab, average='macro')
        ablation_records.append({
            "Configuration": ab_name,
            "Features Used": str(ab_feats),
            "Test Accuracy": f"{acc_ab*100:.2f}%",
            "Macro F1": f"{f1_ab:.4f}"
        })
    print(pd.DataFrame(ablation_records).to_string(index=False))

    # Noise injection test (realistic sensor noise)
    print("\nRobustness to Real-World Sensor Noise (Adding Gaussian Noise to Features):")
    noise_levels = [0.0, 0.05, 0.10, 0.20, 0.30]
    for nl in noise_levels:
        np.random.seed(42)
        X_test_noisy = X_test.copy()
        if nl > 0:
            for col in features:
                std_val = X_test[col].std()
                X_test_noisy[col] += np.random.normal(0, nl * std_val, size=len(X_test))
        pred_noisy = model.predict(X_test_noisy)
        acc_noisy = accuracy_score(y_test, pred_noisy)
        f1_noisy = f1_score(y_test, pred_noisy, average='macro')
        print(f"  Noise Level {int(nl*100)}%: Test Accuracy = {acc_noisy*100:.2f}%, Macro F1 = {f1_noisy:.4f}")

    # -------------------------------------------------------------
    # 10. FINAL INDEPENDENT TEST SET (UNSEEN SEED, UNTOUCHED SAMPLES)
    # -------------------------------------------------------------
    print("\n### SECTION 10: INDEPENDENT TEST SET EVALUATION ###")
    df_independent = generate_synthetic_road_data(n_samples=1000, random_seed=9999)
    X_indep = df_independent[features]
    y_indep = df_independent[target]
    
    y_indep_pred = model.predict(X_indep)
    y_indep_prob = model.predict_proba(X_indep)
    
    indep_acc = accuracy_score(y_indep, y_indep_pred)
    indep_f1 = f1_score(y_indep, y_indep_pred, average='macro')
    indep_auc = roc_auc_score(y_indep, y_indep_prob, multi_class='ovr', average='macro')
    
    print(f"Independent Test Sample Count: 1,000 (Random Seed 9999)")
    print(f"Independent Accuracy:        {indep_acc:.4f} ({indep_acc*100:.2f}%)")
    print(f"Independent Macro F1:        {indep_f1:.4f}")
    print(f"Independent ROC-AUC:         {indep_auc:.4f}")
    print("\nIndependent Confusion Matrix:")
    cm_indep = confusion_matrix(y_indep, y_indep_pred)
    print("Pred ->   Safe  Risky  Blocked")
    print(f"Actual Safe:    {cm_indep[0][0]:4d}   {cm_indep[0][1]:4d}     {cm_indep[0][2]:4d}")
    print(f"Actual Risky:   {cm_indep[1][0]:4d}   {cm_indep[1][1]:4d}     {cm_indep[1][2]:4d}")
    print(f"Actual Blocked: {cm_indep[2][0]:4d}   {cm_indep[2][1]:4d}     {cm_indep[2][2]:4d}")
    print("\nIndependent Classification Report:")
    print(classification_report(y_indep, y_indep_pred, target_names=['Safe', 'Risky', 'Blocked'], digits=4))

if __name__ == '__main__':
    run_complete_audit()
