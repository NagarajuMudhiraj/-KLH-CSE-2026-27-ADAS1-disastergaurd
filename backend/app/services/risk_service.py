from typing import Dict, Any, List

class RiskService:
    """Centralized engine for calculating road risk (0-100)."""
    
    def calculate_risk(
        self,
        yolo_detections: List[Dict[str, Any]],
        xgboost_prediction: Dict[str, Any] = None,
        gps_location: Dict[str, float] = None,
        road_status: str = "Unknown"
    ) -> Dict[str, Any]:
        
        score = 0
        reasons = []
        recommended_action = "Proceed with normal caution."
        
        # 1. Process YOLO Hazards
        hazard_count = len(yolo_detections)
        if hazard_count > 0:
            reasons.append(f"Visual evidence: {hazard_count} hazard(s) detected.")
            
            highest_severity_score = 0
            for det in yolo_detections:
                severity = det.get("severity", "LOW")
                conf = det.get("confidence", 0.0)
                cls = det.get("class_name", "Hazard")
                
                reasons.append(f"• {cls} ({severity} severity, {int(conf*100)}% confidence)")
                
                if severity == "CRITICAL":
                    highest_severity_score = max(highest_severity_score, 80)
                elif severity == "HIGH":
                    highest_severity_score = max(highest_severity_score, 60)
                elif severity == "MEDIUM":
                    highest_severity_score = max(highest_severity_score, 40)
                elif severity == "LOW":
                    highest_severity_score = max(highest_severity_score, 20)
                    
            score += highest_severity_score
            # Add small penalty for multiple hazards
            if hazard_count > 1:
                score += (hazard_count - 1) * 5
                
        # 2. Process XGBoost Prediction
        if xgboost_prediction:
            xgb_status = xgboost_prediction.get("prediction", "Safe")
            xgb_conf = xgboost_prediction.get("confidence", 0.0)
            
            reasons.append(f"Environmental conditions model predicts: {xgb_status.upper()} RISK ({int(xgb_conf*100)}% confidence)")
            
            if xgb_status == "Blocked":
                score += 50
            elif xgb_status == "Risky":
                score += 30
                
        # Clamp score between 0 and 100
        score = max(0, min(100, score))
        
        # 3. Determine Final Risk Level
        if score <= 30:
            risk_level = "SAFE"
            recommended_action = "Route is clear."
        elif score <= 50:
            risk_level = "LOW"
            recommended_action = "Drive carefully."
        elif score <= 70:
            risk_level = "MODERATE"
            recommended_action = "Exercise heightened caution."
        elif score <= 85:
            risk_level = "HIGH"
            recommended_action = "Consider alternative routes."
        else:
            risk_level = "CRITICAL"
            recommended_action = "Avoid current road immediately."
            
        return {
            "risk_score": score,
            "risk_level": risk_level,
            "reasons": reasons,
            "recommended_action": recommended_action,
            "timestamp": "Generated in real-time" # Ideally pass actual time
        }

risk_engine = RiskService()
