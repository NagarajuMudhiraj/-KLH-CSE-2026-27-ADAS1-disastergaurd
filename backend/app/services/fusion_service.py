from typing import Dict, Any, Optional
from app.services.ai_service import ai_engine
from app.services.risk_service import risk_engine

class FusionService:
    """Orchestrates AI perception, prediction, and risk calculation."""

    def evaluate_environment(
        self,
        image_bytes: Optional[bytes] = None,
        rainfall: Optional[float] = None,
        traffic: Optional[float] = None,
        water_level: Optional[float] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Combines YOLO visual detection with XGBoost environmental prediction
        and feeds it into the Risk Engine to generate a final Risk Score.
        """
        # 1. Process Visual Data (YOLOv11)
        yolo_result = {"detections": []}
        if image_bytes:
            yolo_result = ai_engine.predict_image(image_bytes)

        # 2. Process Environmental Data (XGBoost)
        xgb_result = None
        if rainfall is not None and traffic is not None and water_level is not None:
            xgb_result = ai_engine.predict_road_safety(rainfall, traffic, water_level)

        # 3. Compile GPS Location
        gps_location = None
        if lat is not None and lng is not None:
            gps_location = {"lat": lat, "lng": lng}

        # 4. Central Risk Engine Assessment
        final_risk = risk_engine.calculate_risk(
            yolo_detections=yolo_result.get("detections", []),
            xgboost_prediction=xgb_result,
            gps_location=gps_location
        )

        return {
            "risk_assessment": final_risk,
            "visual_evidence": yolo_result,
            "environmental_prediction": xgb_result,
            "location": gps_location
        }

fusion_engine = FusionService()
