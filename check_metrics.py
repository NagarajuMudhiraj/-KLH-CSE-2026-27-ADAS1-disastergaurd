import pandas as pd
import numpy as np

# 1. YOLOv11s Metrics
df_yolo = pd.read_csv('runs/detect/yolo11_master_disaster_detector/results.csv')
df_yolo.columns = [c.strip() for c in df_yolo.columns]

last = df_yolo.iloc[-1]
p_last = last['metrics/precision(B)']
r_last = last['metrics/recall(B)']
f1_last = 2 * p_last * r_last / (p_last + r_last) if (p_last + r_last) > 0 else 0

best = df_yolo.loc[df_yolo['metrics/mAP50(B)'].idxmax()]
p_best = best['metrics/precision(B)']
r_best = best['metrics/recall(B)']
f1_best = 2 * p_best * r_best / (p_best + r_best) if (p_best + r_best) > 0 else 0

print("=== 1. YOLOv11s COMPUTER VISION METRICS ===")
print(f"Final Epoch (50):")
print(f"  Precision:    {p_last:.4f} ({p_last*100:.2f}%)")
print(f"  Recall:       {r_last:.4f} ({r_last*100:.2f}%)")
print(f"  F1 Score:     {f1_last:.4f} ({f1_last*100:.2f}%)")
print(f"  mAP@0.5:      {last['metrics/mAP50(B)']:.4f} ({last['metrics/mAP50(B)']*100:.2f}%)")
print(f"  mAP@0.5:0.95: {last['metrics/mAP50-95(B)']:.4f} ({last['metrics/mAP50-95(B)']*100:.2f}%)")

print(f"\nPeak Performance Epoch ({int(best['epoch'])}):")
print(f"  Precision:    {p_best:.4f} ({p_best*100:.2f}%)")
print(f"  Recall:       {r_best:.4f} ({r_best*100:.2f}%)")
print(f"  F1 Score:     {f1_best:.4f} ({f1_best*100:.2f}%)")
print(f"  mAP@0.5:      {best['metrics/mAP50(B)']:.4f} ({best['metrics/mAP50(B)']*100:.2f}%)")
print(f"  mAP@0.5:0.95: {best['metrics/mAP50-95(B)']:.4f} ({best['metrics/mAP50-95(B)']*100:.2f}%)")

# 2. XGBoost Road Safety Metrics
from training.train_xgboost import generate_synthetic_road_data
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier

df_xgb = generate_synthetic_road_data(n_samples=2500, random_seed=42)
X = df_xgb[['rainfall', 'traffic', 'water_level']]
y = df_xgb['status']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
clf = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)

acc = accuracy_score(y_test, y_pred)
prec_macro = precision_score(y_test, y_pred, average='macro')
rec_macro = recall_score(y_test, y_pred, average='macro')
f1_macro = f1_score(y_test, y_pred, average='macro')
prec_weighted = precision_score(y_test, y_pred, average='weighted')
rec_weighted = recall_score(y_test, y_pred, average='weighted')
f1_weighted = f1_score(y_test, y_pred, average='weighted')
roc_auc = roc_auc_score(y_test, y_proba, multi_class='ovr')

print("\n=== 2. XGBOOST ROAD SAFETY CLASSIFICATION METRICS ===")
print(f"  Accuracy:               {acc:.4f} ({acc*100:.2f}%)")
print(f"  Precision (Macro):      {prec_macro:.4f} ({prec_macro*100:.2f}%)")
print(f"  Recall (Macro):         {rec_macro:.4f} ({rec_macro*100:.2f}%)")
print(f"  F1-Score (Macro):       {f1_macro:.4f} ({f1_macro*100:.2f}%)")
print(f"  Precision (Weighted):   {prec_weighted:.4f} ({prec_weighted*100:.2f}%)")
print(f"  Recall (Weighted):      {rec_weighted:.4f} ({rec_weighted*100:.2f}%)")
print(f"  F1-Score (Weighted):    {f1_weighted:.4f} ({f1_weighted*100:.2f}%)")
print(f"  ROC-AUC (One-vs-Rest):  {roc_auc:.4f} ({roc_auc*100:.2f}%)")
