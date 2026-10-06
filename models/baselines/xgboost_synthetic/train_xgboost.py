"""
XGBoost Road Safety Prediction Model Training Script
Trains an XGBClassifier on synthetic/disaster metrics:
- Rainfall (mm/h)
- Traffic Level (1-10)
- Water Level (cm)
Predicts: 0: Safe, 1: Risky, 2: Blocked
"""

import os
import pickle
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

def generate_synthetic_road_data(n_samples=2500, random_seed=42):
    np.random.seed(random_seed)
    
    # Feature distributions
    rainfall = np.random.uniform(0, 150, n_samples)      # mm/hour
    traffic = np.random.uniform(1, 10, n_samples)         # 1 to 10 scale
    water_level = np.random.uniform(0, 100, n_samples)    # cm depth
    
    # Calculate safety risk score using disaster physics rules
    # Higher water level and rainfall strongly contribute to blocked/risky state
    risk_score = (rainfall * 0.3) + (traffic * 4.0) + (water_level * 1.2)
    
    labels = []
    for r_score, wl, rf in zip(risk_score, water_level, rainfall):
        if wl > 50 or r_score > 120 or rf > 100:
            labels.append(2)  # Blocked
        elif wl > 20 or r_score > 65 or rf > 40:
            labels.append(1)  # Risky
        else:
            labels.append(0)  # Safe
            
    df = pd.DataFrame({
        'rainfall': rainfall,
        'traffic': traffic,
        'water_level': water_level,
        'status': labels
    })
    
    return df

def train_and_save_model():
    print("Generating synthetic disaster telemetry dataset...")
    df = generate_synthetic_road_data()
    
    X = df[['rainfall', 'traffic', 'water_level']]
    y = df['status']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("Training XGBoost Classifier...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='mlogloss'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("\n--- Model Evaluation ---")
    print("Accuracy:", (y_pred == y_test).mean())
    print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=['Safe', 'Risky', 'Blocked']))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
    
    # Save model
    os.makedirs("models", exist_ok=True)
    model_path = os.path.join("models", "road_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
        
    print(f"\nModel saved successfully to {model_path}!")

if __name__ == "__main__":
    train_and_save_model()
