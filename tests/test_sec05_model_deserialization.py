import sys
import os
import numpy as np

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

def test_sec05_xgboost_json_inference():
    # 1. Verify pickle is not used in ai_service
    import app.services.ai_service as ai_module
    assert not hasattr(ai_module, "pickle"), "Vulnerability: pickle is still imported in ai_service!"

    from app.services.ai_service import ai_engine
    assert ai_engine.xgboost_model is not None, "Failed to load XGBoost model from JSON"

    # 2. Test direct legacy XGBClassifier JSON predict on sample inputs
    test_inputs = np.array([
        [0.0, 0.2, 0.0],
        [50.0, 0.8, 15.0],
        [120.0, 0.9, 45.0],
        [10.0, 0.5, 5.0],
        [200.0, 1.0, 80.0]
    ])
    preds = ai_engine.xgboost_model.predict(test_inputs)
    probs = ai_engine.xgboost_model.predict_proba(test_inputs)
    print("Direct legacy JSON model class predictions:", preds)
    print("Direct legacy JSON model probabilities:\n", probs)
    assert len(preds) == 5
    assert preds[0] == 0, f"Expected 0 (Safe), got {preds[0]}"
    assert preds[1] == 1, f"Expected 1 (Risky), got {preds[1]}"
    assert preds[2] == 2, f"Expected 2 (Blocked), got {preds[2]}"
    assert preds[3] == 0, f"Expected 0 (Safe), got {preds[3]}"
    assert preds[4] == 2, f"Expected 2 (Blocked), got {preds[4]}"

    print("SEC-05 TEST PASSED: XGBoost JSON loading verified without pickle; sample predictions match expected classes.")

    print("SEC-05 TEST PASSED: XGBoost JSON loading verified without pickle; sample predictions accurate.")

if __name__ == "__main__":
    test_sec05_xgboost_json_inference()
