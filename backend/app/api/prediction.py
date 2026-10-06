import asyncio
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from typing import Optional
from app.services.fusion_service import fusion_engine
from app.database.mongodb import get_predictions_collection
from app.utils.security import get_optional_user
from datetime import datetime

router = APIRouter(prefix="/api", tags=["Predictions"])

@router.post("/predict-image")
async def predict_disaster_image(
    file: UploadFile = File(...),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    current_user: dict = Depends(get_optional_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    contents = await file.read()
    username = current_user.get("username", "Live Driver Camera") if current_user else "Live Driver Camera"
    
    try:
        results = fusion_engine.evaluate_environment(image_bytes=contents, lat=lat, lng=lng)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI model prediction failed: {str(e)}")

    visual = results["visual_evidence"]
    risk = results["risk_assessment"]

    # Optional: Log periodic scan asynchronously without blocking live video frame loop
    try:
        pred_coll = get_predictions_collection()
        pred_doc = {
            "username": username,
            "type": "camera_frame",
            "prediction": visual.get("prediction", "No hazard detected"),
            "confidence": visual.get("confidence", 0.0),
            "detections_count": len(visual.get("detections", [])),
            "riskScore": risk.get("risk_score", 0),
            "riskLevel": risk.get("risk_level", "SAFE"),
            "createdAt": datetime.utcnow().isoformat()
        }
        pred_coll.insert_one(pred_doc)
    except Exception:
        pass

    # Real-Time Driver Detection: Exclude pedestrians, send remaining hazards with location-based same-label deduplication
    prediction_str = visual.get("prediction", "")
    pred_lower = prediction_str.lower().strip()
    detections = visual.get("detections", [])

    # 1. EXCLUDE PEDESTRIANS: If prediction or all detections are only pedestrians, do not queue as hazard
    is_pedestrian_only = (pred_lower in ["person", "pedestrian"]) or (
        bool(detections) and all(d.get("class_name", "").lower() in ["person", "pedestrian"] for d in detections)
    )

    # 2. Check for actual hazards: Flood, Fire, Smoke, Road Damage, Pothole, Landslide, Accident, Block
    is_hazard = (not is_pedestrian_only) and (
        any(h_type in pred_lower for h_type in ["flood", "water", "fire", "smoke", "damage", "pothole", "accident", "landslide", "block"]) or 
        (risk.get("risk_level") in ["HIGH", "CRITICAL"] and not is_pedestrian_only)
    )

    if is_hazard:
        try:
            from app.database.mongodb import get_hazards_collection
            from app.api.navigation import disaster_ws_manager
            from app.api.emergency import ws_manager

            hazards_coll = get_hazards_collection()
            now = datetime.utcnow().isoformat()
            hazard_lat = lat if lat is not None else 17.4321
            hazard_lng = lng if lng is not None else 78.4567

            # 3. LOCATION & SAME-LABEL DEDUPLICATION:
            # At this location (~50m radius), if a hazard with the SAME label already exists: TAKE ONLY ONE!
            # If a DIFFERENT hazard is detected at this location: ALLOW IT!
            existing_hazards = hazards_coll.find({"status": {"$ne": "REJECTED"}})
            is_same_hazard_at_location = False
            existing_match_id = None

            for eh in existing_hazards:
                e_lat = eh.get("latitude") if eh.get("latitude") is not None else eh.get("lat")
                e_lng = eh.get("longitude") if eh.get("longitude") is not None else eh.get("lng")
                if e_lat is not None and e_lng is not None:
                    # Spatial proximity (~50 meters ~ 0.00045 degrees)
                    if abs(e_lat - hazard_lat) <= 0.00045 and abs(e_lng - hazard_lng) <= 0.00045:
                        eh_type = (eh.get("disasterType") or eh.get("type") or eh.get("name") or "").lower().strip()
                        # Check if SAME label:
                        has_same_label = (
                            pred_lower in eh_type or eh_type in pred_lower or
                            ("flood" in pred_lower and "flood" in eh_type) or
                            ("fire" in pred_lower and "fire" in eh_type) or
                            ("smoke" in pred_lower and "smoke" in eh_type) or
                            ("damage" in pred_lower and "damage" in eh_type) or
                            ("pothole" in pred_lower and "pothole" in eh_type) or
                            ("landslide" in pred_lower and "landslide" in eh_type) or
                            ("accident" in pred_lower and "accident" in eh_type)
                        )
                        if has_same_label:
                            is_same_hazard_at_location = True
                            existing_match_id = eh.get("id") or eh.get("_id")
                            # If new detection has higher confidence, update the existing record
                            new_conf = round(visual.get("confidence", 0.85), 2)
                            if new_conf > (eh.get("confidence") or 0):
                                hazards_coll.update_one(
                                    {"_id": eh["_id"]},
                                    {"$set": {
                                        "confidence": new_conf,
                                        "image_url": visual.get("annotated_image_url", eh.get("image_url")),
                                        "updated_at": now
                                    }}
                                )
                            break

            # Only insert if no hazard with the SAME label exists at this location
            # (Different hazards at the same location are allowed!)
            if not is_same_hazard_at_location:
                doc_id = f"driver_det_{int(datetime.utcnow().timestamp() * 1000)}"
                hazard_doc = {
                    "_id": doc_id,
                    "id": doc_id,
                    "source": "AI",
                    "type": pred_lower,
                    "disasterType": prediction_str,
                    "name": prediction_str,
                    "confidence": round(visual.get("confidence", 0.85), 2),
                    "latitude": hazard_lat,
                    "longitude": hazard_lng,
                    "lat": hazard_lat,
                    "lng": hazard_lng,
                    "location": {
                        "lat": hazard_lat,
                        "lng": hazard_lng,
                        "address": f"Driver GPS ({hazard_lat:.4f}, {hazard_lng:.4f})"
                    },
                    "address": f"Driver GPS ({hazard_lat:.4f}, {hazard_lng:.4f})",
                    "severity": risk.get("risk_level", "HIGH"),
                    "description": f"Real-time driver camera detected {prediction_str} with {int(visual.get('confidence', 0.85) * 100)}% confidence.",
                    "image_url": visual.get("annotated_image_url", ""),
                    "status": "PENDING_REVIEW",
                    "verified": False,
                    "detectedBy": f"Driver Dashcam ({username})",
                    "reported_by": username,
                    "start_time": now,
                    "createdAt": now,
                    "created_at": now,
                    "timestamp": now
                }
                hazards_coll.insert_one(hazard_doc)

                # Broadcast live to Admin Queue via WebSocket
                broadcast_msg = {
                    "event": "NEW_DISASTER_DETECTED",
                    "data": hazard_doc
                }
                asyncio.create_task(disaster_ws_manager.broadcast(broadcast_msg))
                asyncio.create_task(ws_manager.broadcast(broadcast_msg))
            else:
                print(f"Location deduplication: Hazard '{prediction_str}' already registered at ({hazard_lat:.4f}, {hazard_lng:.4f}). Duplicate suppressed.")
        except Exception as e:
            print("Driver hazard queue notice:", e)

    # Flatten response for API consumers
    flat_results = {
        "prediction": visual.get("prediction", "No hazard detected"),
        "confidence": visual.get("confidence", 0.0),
        "detections": visual.get("detections", []),
        "annotated_image_url": visual.get("annotated_image_url", ""),
        "inference_time_ms": visual.get("inference_time_ms", 0),
        "riskScore": risk.get("risk_score", 0),
        "riskLevel": risk.get("risk_level", "SAFE"),
        "recommendation": risk.get("recommendation", ""),
        "visual_evidence": visual,
        "risk_assessment": risk
    }

    return flat_results
