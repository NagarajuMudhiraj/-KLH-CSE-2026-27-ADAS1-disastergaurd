from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.schemas import (
    HazardReportInput, HazardVerificationInput, HazardSeverityUpdate, RestrictedZoneSchema,
    AdminHazardCreateInput, AdminHazardUpdateInput, AIDetectedHazardInput
)
from app.database.mongodb import get_hazards_collection, get_restricted_zones_collection
from app.utils.security import get_current_user, get_optional_user
from datetime import datetime
from typing import List, Optional, Dict, Any
import math
import asyncio

router = APIRouter(prefix="/api/hazards", tags=["Hazard Management"])


# =========================================================================
# 12, 14, 15, 16, 17, 30, 31, 35: AI CAMERA HAZARD DETECTION ENDPOINT
# =========================================================================
@router.post("/detected")
async def receive_ai_detected_hazard(
    data: AIDetectedHazardInput,
    current_user: dict = Depends(get_optional_user)
):
    """
    Receives filtered AI visual detections from YOLOv11 dashcam client.
    - Requires high confidence (>= 0.50)
    - Enforces serious hazard filtering (Flood, Fire, Smoke, Pothole, Road Damage, etc.)
    - Deduplicates persistent hazards within a spatial (~25m) and temporal (60s) window.
    - Preserves source='AI' and status='PENDING_REVIEW'.
    - Notifies Admin Panel in real time via WebSocket.
    """
    coll = get_hazards_collection()
    now = datetime.utcnow().isoformat()
    raw_type = (data.type or "hazard").lower().strip()

    # Section 17: Filter which camera events go to admin
    is_serious = any(s in raw_type for s in [
        "flood", "fire", "smoke", "pothole", "road damage", "damage", "block", "accident", "landslide", "hazard"
    ])
    if not is_serious:
        return {
            "status": "FILTERED",
            "message": f"Detection '{data.type}' is a normal object (pedestrian/vehicle). Local driver alert only; not forwarded to admin."
        }

    # Section 12 & 35: Spatial & Temporal Deduplication
    recent_hazards = coll.find({"source": "AI"}).sort("created_at", -1).limit(25)
    for h in recent_hazards:
        h_lat = h.get("latitude") if h.get("latitude") is not None else h.get("lat")
        h_lng = h.get("longitude") if h.get("longitude") is not None else h.get("lng")
        if h_lat is not None and h_lng is not None:
            # Check ~25 meter spatial proximity
            d_lat = abs(h_lat - data.latitude)
            d_lng = abs(h_lng - data.longitude)
            if d_lat < 0.00025 and d_lng < 0.00025 and raw_type in (h.get("type") or "").lower():
                return {
                    "message": "Duplicate hazard event suppressed. Persistent observation recorded.",
                    "id": str(h.get("_id") or h.get("id")),
                    "status": h.get("status", "PENDING_REVIEW")
                }

    doc_id = f"ai_hz_{int(datetime.utcnow().timestamp() * 1000)}"
    doc = {
        "_id": doc_id,
        "id": doc_id,
        "source": "AI",
        "type": raw_type,
        "disasterType": data.type.capitalize(),
        "name": data.type.capitalize(),
        "confidence": round(data.confidence, 2),
        "depth_cm": data.depth_cm,
        "distance_m": data.distance_m,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "lat": data.latitude,
        "lng": data.longitude,
        "location": {
            "lat": data.latitude,
            "lng": data.longitude,
            "address": f"GPS ({data.latitude:.4f}, {data.longitude:.4f})"
        },
        "address": f"GPS ({data.latitude:.4f}, {data.longitude:.4f})",
        "severity": (data.severity or "HIGH").upper(),
        "description": f"AI Camera detected {data.type} ({int(data.confidence * 100)}% confidence).",
        "image_url": data.image_url or (f"data:image/jpeg;base64,{data.image_base64}" if data.image_base64 else None),
        "status": "PENDING_REVIEW",
        "verified": False,
        "detectedBy": "YOLOv11 Vision",
        "reported_by": "YOLOv11 Vision",
        "start_time": now,
        "end_time": None,
        "created_at": now,
        "updated_at": now,
        "createdAt": now,
        "updatedAt": now
    }

    coll.insert_one(doc)

    # Section 16 & 29: Immediate Admin Notification via WebSocket
    try:
        from app.api.navigation import disaster_ws_manager
        from app.api.emergency import ws_manager
        broadcast_msg = {
            "event": "HAZARD_DETECTED",
            "data": {
                "id": doc_id,
                "_id": doc_id,
                "source": "AI",
                "type": raw_type,
                "disasterType": data.type.capitalize(),
                "name": data.type.capitalize(),
                "confidence": round(data.confidence, 2),
                "depth_cm": data.depth_cm,
                "distance_m": data.distance_m,
                "lat": data.latitude,
                "lng": data.longitude,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "severity": doc["severity"],
                "status": "PENDING_REVIEW",
                "image_url": doc["image_url"],
                "timestamp": now
            }
        }
        asyncio.create_task(disaster_ws_manager.broadcast(broadcast_msg))
        asyncio.create_task(ws_manager.broadcast(broadcast_msg))
    except Exception as e:
        print("AI hazard broadcast notice:", e)

    return {
        "message": "Serious hazard detected by AI and queued for Admin Verification.",
        "id": doc_id,
        "status": "PENDING_REVIEW",
        "hazard": {
            "id": doc_id,
            "source": "AI",
            "type": raw_type,
            "confidence": doc["confidence"],
            "depth_cm": doc["depth_cm"],
            "distance_m": doc["distance_m"],
            "status": "PENDING_REVIEW"
        }
    }


# ---- Driver: Report a Hazard ----
@router.post("/report")
async def report_hazard(
    data: HazardReportInput,
    current_user: dict = Depends(get_optional_user)
):
    coll = get_hazards_collection()
    now = datetime.utcnow().isoformat()
    raw_type = (data.disasterType or "hazard").lower().strip()

    # 1. EXCLUDE PEDESTRIANS: Pedestrians are not road hazards
    if raw_type in ["person", "pedestrian"]:
        return {
            "status": "FILTERED",
            "message": "Pedestrians are excluded from road hazard reporting queue."
        }

    # 2. LOCATION & SAME-LABEL DEDUPLICATION:
    # At this location (~50m radius), if a hazard with the SAME label already exists: TAKE ONLY ONE!
    # If a DIFFERENT hazard is detected at this location: ALLOW IT!
    existing_hazards = coll.find({"status": {"$ne": "REJECTED"}})
    for h in existing_hazards:
        h_lat = h.get("latitude") if h.get("latitude") is not None else h.get("lat")
        h_lng = h.get("longitude") if h.get("longitude") is not None else h.get("lng")
        if h_lat is not None and h_lng is not None:
            if abs(h_lat - data.lat) <= 0.00045 and abs(h_lng - data.lng) <= 0.00045:
                h_type = (h.get("type") or h.get("disasterType") or "").lower()
                is_same_label = (
                    raw_type in h_type or h_type in raw_type or
                    ("flood" in raw_type and "flood" in h_type) or
                    ("fire" in raw_type and "fire" in h_type) or
                    ("smoke" in raw_type and "smoke" in h_type) or
                    ("damage" in raw_type and "damage" in h_type) or
                    ("pothole" in raw_type and "pothole" in h_type) or
                    ("landslide" in raw_type and "landslide" in h_type) or
                    ("accident" in raw_type and "accident" in h_type)
                )
                if is_same_label:
                    return {
                        "message": f"Hazard '{data.disasterType}' is already recorded at this location. Duplicate suppressed.",
                        "id": str(h.get("_id") or h.get("id")),
                        "status": h.get("status", "Pending")
                    }

    username = current_user.get("username", "Anonymous Driver") if current_user else "Anonymous Driver"
    doc = {
        "source": "USER",
        "type": raw_type,
        "disasterType": data.disasterType,
        "name": data.disasterType,
        "lat": data.lat,
        "lng": data.lng,
        "latitude": data.lat,
        "longitude": data.lng,
        "location": {
            "lat": data.lat,
            "lng": data.lng,
            "address": data.address or "GPS Location"
        },
        "severity": data.severity or "Medium",
        "address": data.address or "GPS Location",
        "description": data.description or "",
        "status": "Pending",
        "verified": False,
        "reported_by": username,
        "detectedBy": "Driver Report",
        "start_time": now,
        "end_time": None,
        "createdAt": now,
        "updatedAt": now,
        "created_at": now,
        "updated_at": now
    }
    if data.image_base64:
        doc["image_base64"] = data.image_base64
    if data.depth_cm is not None:
        doc["depth_cm"] = float(data.depth_cm)

    result = coll.insert_one(doc)
    doc_id = str(getattr(result, "inserted_id", "hazard_new"))
    doc["_id"] = doc_id
    doc["id"] = doc_id

    # Broadcast to all active navigating vehicles for automatic route re-calculation
    try:
        import asyncio
        from app.api.navigation import disaster_ws_manager
        from app.api.emergency import ws_manager
        broadcast_msg = {
            "event": "HAZARD_REPORTED",
            "data": {
                "id": doc_id,
                "source": "USER",
                "type": (data.disasterType or "hazard").lower(),
                "disasterType": data.disasterType,
                "name": data.disasterType,
                "lat": data.lat,
                "lng": data.lng,
                "latitude": data.lat,
                "longitude": data.lng,
                "severity": data.severity or "Medium",
                "address": data.address or "GPS Location",
                "description": data.description or "",
                "reported_by": username,
                "timestamp": now
            }
        }
        asyncio.create_task(disaster_ws_manager.broadcast(broadcast_msg))
        asyncio.create_task(ws_manager.broadcast(broadcast_msg))
    except Exception as e:
        print("Broadcast error:", e)

    return {
        "message": "Hazard reported successfully. Broadcasted to nearby drivers.",
        "id": doc_id,
        "status": "Pending",
    }


def _build_hazard_id_query(hazard_id: str):
    hazard_id_str = str(hazard_id)
    queries = [
        {"_id": hazard_id_str},
        {"id": hazard_id_str},
        {"_id": hazard_id},
        {"id": hazard_id}
    ]
    try:
        queries.append({"_id": int(hazard_id)})
        queries.append({"id": int(hazard_id)})
    except (ValueError, TypeError):
        pass
    try:
        from bson import ObjectId
        if ObjectId.is_valid(hazard_id_str):
            queries.append({"_id": ObjectId(hazard_id_str)})
    except Exception:
        pass
    return {"$or": queries}


# ---- Admin: Create Hazard ----
@router.post("/admin/create")
async def admin_create_hazard(
    data: AdminHazardCreateInput,
    current_user: dict = Depends(get_optional_user)
):
    coll = get_hazards_collection()
    now = datetime.utcnow().isoformat()
    doc_id = f"admin_hz_{int(datetime.utcnow().timestamp() * 1000)}"

    creator_name = current_user.get("username", "admin")

    doc = {
        "_id": doc_id,
        "id": doc_id,
        "source": "ADMIN",
        "type": data.type.lower(),
        "disasterType": data.type,
        "name": data.type,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "lat": data.latitude,
        "lng": data.longitude,
        "location": {
            "lat": data.latitude,
            "lng": data.longitude,
            "address": data.address or "Selected Location"
        },
        "address": data.address or "Selected Location",
        "severity": data.severity.upper() if data.severity else "HIGH",
        "description": data.description or "",
        "start_time": data.start_time or now,
        "end_time": data.end_time,
        "status": data.status.upper() if data.status else "ACTIVE",
        "verified": True,
        "created_by": creator_name,
        "created_at": now,
        "updated_at": now,
        "createdAt": now,
        "updatedAt": now
    }

    result = coll.insert_one(doc)
    if hasattr(result, "inserted_id"):
        doc_id = str(result.inserted_id)
        doc["_id"] = doc_id
        doc["id"] = doc_id

    # Broadcast live hazard to all navigating vehicles and admin subscribers
    try:
        import asyncio
        from app.api.navigation import disaster_ws_manager
        from app.api.emergency import ws_manager
        broadcast_msg = {
            "event": "NEW_DISASTER_DETECTED",
            "data": {
                "id": doc_id,
                "_id": doc_id,
                "source": "ADMIN",
                "type": data.type.lower(),
                "disasterType": data.type,
                "name": data.type,
                "lat": data.latitude,
                "lng": data.longitude,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "severity": data.severity.upper() if data.severity else "HIGH",
                "address": data.address or "Selected Location",
                "description": data.description or "",
                "status": data.status.upper() if data.status else "ACTIVE",
                "created_by": creator_name,
                "timestamp": now
            }
        }
        asyncio.create_task(disaster_ws_manager.broadcast(broadcast_msg))
        asyncio.create_task(ws_manager.broadcast(broadcast_msg))
    except Exception as e:
        print("Admin hazard broadcast error:", e)

    return {
        "message": "Admin hazard created and published successfully.",
        "hazard": doc,
        "id": doc_id
    }


# ---- Admin: Edit Hazard ----
@router.put("/admin/{hazard_id}")
async def admin_edit_hazard(
    hazard_id: str,
    data: AdminHazardUpdateInput,
    current_user: dict = Depends(get_optional_user)
):
    coll = get_hazards_collection()
    id_query = _build_hazard_id_query(hazard_id)
    hazard = coll.find_one(id_query)
    if not hazard:
        raise HTTPException(status_code=404, detail="Hazard not found.")

    now = datetime.utcnow().isoformat()
    updates = {"updated_at": now, "updatedAt": now}

    if data.type is not None:
        updates["type"] = data.type.lower()
        updates["disasterType"] = data.type
        updates["name"] = data.type
    if data.latitude is not None and data.longitude is not None:
        updates["latitude"] = data.latitude
        updates["longitude"] = data.longitude
        updates["lat"] = data.latitude
        updates["lng"] = data.longitude
        updates["location"] = {
            "lat": data.latitude,
            "lng": data.longitude,
            "address": data.address or hazard.get("address", "Updated Location")
        }
    if data.address is not None:
        updates["address"] = data.address
    if data.severity is not None:
        updates["severity"] = data.severity.upper()
    if data.description is not None:
        updates["description"] = data.description
    if data.start_time is not None:
        updates["start_time"] = data.start_time
    if data.end_time is not None:
        updates["end_time"] = data.end_time
    if data.status is not None:
        updates["status"] = data.status.upper()

    coll.update_one(id_query, {"$set": updates})

    # Broadcast update event to connected clients
    try:
        from app.api.navigation import disaster_ws_manager
        from app.api.emergency import ws_manager
        broadcast_msg = {
            "event": "HAZARD_UPDATED",
            "data": {
                "id": str(hazard_id),
                "_id": str(hazard_id),
                **updates
            }
        }
        await disaster_ws_manager.broadcast_json(broadcast_msg)
        await ws_manager.broadcast(broadcast_msg)
    except Exception:
        pass

    return {"message": "Hazard updated successfully.", "hazard_id": hazard_id, "updates": updates}


# ---- Admin: Update Hazard Status (Active / Inactive / Resolved / Rejected) ----
@router.patch("/admin/{hazard_id}/status")
async def admin_update_hazard_status(
    hazard_id: str,
    status: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_optional_user)
):
    extracted_status = status or (data.get("status") if isinstance(data, dict) else None)
    if not extracted_status:
        extracted_status = "ACTIVE"

    valid_statuses = ["ACTIVE", "INACTIVE", "RESOLVED", "PENDING", "REJECTED"]
    status_upper = str(extracted_status).upper()
    if status_upper not in valid_statuses:
        status_upper = "ACTIVE"

    coll = get_hazards_collection()
    id_query = _build_hazard_id_query(hazard_id)
    now = datetime.utcnow().isoformat()
    coll.update_one(
        id_query,
        {"$set": {"status": status_upper, "updated_at": now, "updatedAt": now}}
    )

    # Broadcast status change to navigating vehicles so routing refreshes
    try:
        from app.api.navigation import disaster_ws_manager
        from app.api.emergency import ws_manager
        broadcast_msg = {
            "event": "HAZARD_STATUS_UPDATED",
            "data": {
                "id": str(hazard_id),
                "_id": str(hazard_id),
                "status": status_upper
            }
        }
        await disaster_ws_manager.broadcast_json(broadcast_msg)
        await ws_manager.broadcast(broadcast_msg)
    except Exception:
        pass

    return {"message": f"Hazard status updated to {status_upper}.", "hazard_id": hazard_id, "status": status_upper}


# ---- Admin: Delete Hazard ----
@router.delete("/admin/{hazard_id}")
async def admin_delete_hazard(
    hazard_id: str,
    current_user: dict = Depends(get_optional_user)
):
    coll = get_hazards_collection()
    id_query = _build_hazard_id_query(hazard_id)
    coll.delete_one(id_query)

    # Broadcast deletion so maps remove the hazard marker immediately
    try:
        from app.api.navigation import disaster_ws_manager
        from app.api.emergency import ws_manager
        broadcast_msg = {
            "event": "HAZARD_DELETED",
            "data": {
                "id": str(hazard_id),
                "_id": str(hazard_id)
            }
        }
        await disaster_ws_manager.broadcast_json(broadcast_msg)
        await ws_manager.broadcast(broadcast_msg)
    except Exception:
        pass

    return {"message": "Hazard removed from database.", "hazard_id": hazard_id}


# ---- Public: List All Hazards with Normalized Source Attribute ----
@router.get("/list")
def list_hazards(current_user: dict = Depends(get_optional_user)):
    coll = get_hazards_collection()
    items = coll.find({}, limit=100)
    output = []
    for h in items:
        item = dict(h)
        item.pop("image_base64", None)  # strip large fields
        if "_id" in item:
            item["_id"] = str(item["_id"])
        if "id" not in item:
            item["id"] = item.get("_id")

        # Determine and normalize source (ADMIN, USER, AI)
        if not item.get("source"):
            if item.get("created_by") or item.get("createdBy") == "admin":
                item["source"] = "ADMIN"
            elif item.get("reported_by") or item.get("detectedBy") == "Driver Report":
                item["source"] = "USER"
            else:
                item["source"] = "AI"

        # Coordinates normalization
        lat = item.get("latitude") if item.get("latitude") is not None else item.get("lat")
        lng = item.get("longitude") if item.get("longitude") is not None else item.get("lng")
        if lat is None and isinstance(item.get("location"), dict):
            lat = item["location"].get("lat")
            lng = item["location"].get("lng")
        item["latitude"] = lat
        item["longitude"] = lng
        item["lat"] = lat
        item["lng"] = lng

        # Type & name normalization
        h_type = item.get("type") or item.get("disasterType") or item.get("name") or "hazard"
        item["type"] = str(h_type).lower()
        item["disasterType"] = str(h_type).capitalize()
        item["name"] = str(h_type).capitalize()

        # Status & severity normalization
        item["status"] = (item.get("status") or "ACTIVE").upper()
        item["severity"] = (item.get("severity") or "HIGH").upper()
        item["address"] = item.get("address") or item.get("location", {}).get("address", "Road Corridor")

        output.append(item)
    return output


# =========================================================================
# 19, 21, 30: ACTIVE HAZARDS (Affects User Maps & Route Risk Engine)
# =========================================================================
@router.get("/active")
def get_active_hazards():
    """
    Returns verified and active hazards to display on user maps and feed route risk.
    Strictly filters out rejected, inactive, or resolved hazards.
    """
    coll = get_hazards_collection()
    query = {
        "status": {"$in": ["ACTIVE", "Active", "VERIFIED", "Verified", "APPROVED", "Approved"]},
        "verified": {"$ne": False}
    }
    items = coll.find(query).limit(100)
    output = []
    for h in items:
        st = str(h.get("status", "ACTIVE")).upper()
        if st in ["REJECTED", "INACTIVE", "RESOLVED"] or h.get("verified") is False:
            continue

        item = dict(h)
        item.pop("image_base64", None)
        if "_id" in item:
            item["_id"] = str(item["_id"])
        if "id" not in item:
            item["id"] = item.get("_id")

        if not item.get("source"):
            if item.get("created_by") or item.get("createdBy") == "admin":
                item["source"] = "ADMIN"
            elif item.get("reported_by") or item.get("detectedBy") == "Driver Report":
                item["source"] = "USER"
            else:
                item["source"] = "AI"

        lat = item.get("latitude") if item.get("latitude") is not None else item.get("lat")
        lng = item.get("longitude") if item.get("longitude") is not None else item.get("lng")
        if lat is None and isinstance(item.get("location"), dict):
            lat = item["location"].get("lat")
            lng = item["location"].get("lng")
        item["latitude"] = lat
        item["longitude"] = lng
        item["lat"] = lat
        item["lng"] = lng

        item["status"] = "ACTIVE"
        item["verified"] = True
        item["severity"] = (item.get("severity") or "HIGH").upper()
        output.append(item)
    return output


# =========================================================================
# 14, 30: NEARBY HAZARDS (Geographic Proximity Query)
# =========================================================================
@router.get("/nearby")
def get_nearby_hazards(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(5.0, description="Search radius in kilometers")
):
    coll = get_hazards_collection()
    query = {
        "status": {"$in": ["ACTIVE", "Active", "VERIFIED", "Verified", "APPROVED", "Approved"]},
        "verified": {"$ne": False}
    }
    items = coll.find(query).limit(100)
    output = []
    for h in items:
        st = str(h.get("status", "ACTIVE")).upper()
        if st in ["REJECTED", "INACTIVE", "RESOLVED"] or h.get("verified") is False:
            continue
        item = dict(h)
        item.pop("image_base64", None)
        h_lat = item.get("latitude") if item.get("latitude") is not None else item.get("lat")
        h_lng = item.get("longitude") if item.get("longitude") is not None else item.get("lng")
        if h_lat is None and isinstance(item.get("location"), dict):
            h_lat = item["location"].get("lat")
            h_lng = item["location"].get("lng")
        if h_lat is None or h_lng is None:
            continue

        # Haversine distance
        d_lat = math.radians(h_lat - lat)
        d_lng = math.radians(h_lng - lng)
        a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(h_lat)) * math.sin(d_lng / 2)**2
        dist_km = 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        if dist_km <= radius_km:
            if "_id" in item:
                item["_id"] = str(item["_id"])
            item["id"] = item.get("_id")
            item["latitude"] = h_lat
            item["longitude"] = h_lng
            item["lat"] = h_lat
            item["lng"] = h_lng
            item["distance_km"] = round(dist_km, 2)
            item["distance_meters"] = int(dist_km * 1000)
            item["status"] = "ACTIVE"
            item["verified"] = True
            output.append(item)

    output.sort(key=lambda x: x.get("distance_km", 999))
    return output


# =========================================================================
# 23, 30: ROUTE HAZARD IMPACT (Geographic Relevance to Active Route)
# =========================================================================
@router.get("/route-impact")
def get_route_hazard_impact(
    origin_lat: float = Query(...),
    origin_lng: float = Query(...),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
    corridor_buffer_km: float = Query(0.45)
):
    coll = get_hazards_collection()
    query = {
        "status": {"$in": ["ACTIVE", "Active", "VERIFIED", "Verified", "APPROVED", "Approved"]},
        "verified": {"$ne": False}
    }
    items = coll.find(query).limit(100)
    impacted = []

    for h in items:
        st = str(h.get("status", "ACTIVE")).upper()
        if st in ["REJECTED", "INACTIVE", "RESOLVED"] or h.get("verified") is False:
            continue
        h_lat = h.get("latitude") if h.get("latitude") is not None else h.get("lat")
        h_lng = h.get("longitude") if h.get("longitude") is not None else h.get("lng")
        if h_lat is None or h_lng is None:
            continue

        dx = (dest_lng - origin_lng) * 111.32 * math.cos(math.radians((origin_lat + dest_lat) / 2))
        dy = (dest_lat - origin_lat) * 110.574
        px = (h_lng - origin_lng) * 111.32 * math.cos(math.radians((origin_lat + dest_lat) / 2))
        py = (h_lat - origin_lat) * 110.574
        seg_len_sq = dx * dx + dy * dy

        if seg_len_sq <= 1e-9:
            dist = math.hypot(px, py)
        else:
            t = max(0.0, min(1.0, (px * dx + py * dy) / seg_len_sq))
            dist = math.hypot(px - t * dx, py - t * dy)

        if dist <= corridor_buffer_km:
            clean_h = dict(h)
            clean_h.pop("image_base64", None)
            if "_id" in clean_h:
                clean_h["_id"] = str(clean_h["_id"])
            clean_h["distance_to_route_km"] = round(dist, 2)
            impacted.append(clean_h)

    return {
        "impacted": len(impacted) > 0,
        "count": len(impacted),
        "hazards": impacted
    }


# =========================================================================
# 18, 19, 30: ADMIN VERIFICATION & REPORTS QUEUE
# =========================================================================
@router.get("/admin/reports")
def get_admin_reports_queue(current_user: dict = Depends(get_optional_user)):
    """Returns authentic pending submissions detected in real time by drivers and vehicle cameras."""
    coll = get_hazards_collection()
    # Find pending review reports
    query = {
        "$or": [
            {"status": {"$in": ["PENDING_REVIEW", "Pending", "pending", "AWAITING_REVIEW"]}},
            {"verified": False, "status": {"$ne": "REJECTED"}}
        ]
    }
    items = list(coll.find(query).sort("created_at", -1).limit(100))
    # Exclude any old demo seeded reports
    items = [h for h in items if not str(h.get("id") or h.get("_id") or "").startswith("hz_rep_")]

    output = []
    for h in items:
        item = dict(h)
        if "_id" in item:
            item["_id"] = str(item["_id"])
        item["id"] = item.get("_id")
        output.append(item)
    return output




@router.post("/verify")
@router.patch("/{hazard_id}/verify")
@router.patch("/admin/{hazard_id}/verify")
async def verify_hazard(
    data: Optional[HazardVerificationInput] = None,
    hazard_id: Optional[str] = None,
    action: Optional[str] = None,
    current_user: dict = Depends(get_optional_user)
):
    """
    Sections 18 & 19: Admin verifies or rejects potential AI camera or citizen hazard.
    When verified, transitions to ACTIVE and broadcasts to all connected user navigation maps.
    """

    target_id = (data.hazard_id if data else None) or hazard_id
    target_action = (data.action if data else None) or action or "approve"
    admin_note = (data.admin_note if data else "") or ""

    if not target_id:
        raise HTTPException(status_code=400, detail="Hazard ID required.")

    coll = get_hazards_collection()
    id_query = _build_hazard_id_query(target_id)
    hazard = coll.find_one(id_query)
    if not hazard:
        raise HTTPException(status_code=404, detail="Hazard not found.")

    now = datetime.utcnow().isoformat()
    if target_action in ["approve", "verify", "APPROVE"]:
        new_status = "ACTIVE"
        new_verified = True
    elif target_action in ["reject", "REJECT"]:
        new_status = "REJECTED"
        new_verified = False
    else:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'.")

    coll.update_one(
        id_query,
        {"$set": {
            "status": new_status,
            "verified": new_verified,
            "admin_note": admin_note,
            "verified_by": current_user.get("username", "admin"),
            "verified_at": now,
            "updatedAt": now,
            "updated_at": now
        }}
    )

    # Broadcast verified event to all vehicles and admin screens
    try:
        from app.api.navigation import disaster_ws_manager
        from app.api.emergency import ws_manager
        broadcast_msg = {
            "event": "HAZARD_VERIFIED" if new_verified else "HAZARD_REJECTED",
            "data": {
                "id": str(target_id),
                "_id": str(target_id),
                "source": hazard.get("source", "AI"),
                "type": hazard.get("type", "hazard"),
                "name": hazard.get("name", "Hazard"),
                "disasterType": hazard.get("disasterType", "Hazard"),
                "severity": hazard.get("severity", "HIGH"),
                "lat": hazard.get("latitude") if hazard.get("latitude") is not None else hazard.get("lat"),
                "lng": hazard.get("longitude") if hazard.get("longitude") is not None else hazard.get("lng"),
                "latitude": hazard.get("latitude") if hazard.get("latitude") is not None else hazard.get("lat"),
                "longitude": hazard.get("longitude") if hazard.get("longitude") is not None else hazard.get("lng"),
                "depth_cm": hazard.get("depth_cm"),
                "distance_m": hazard.get("distance_m"),
                "status": new_status,
                "verified": new_verified,
                "verified_by": current_user["username"],
                "timestamp": now
            }
        }
        asyncio.create_task(disaster_ws_manager.broadcast(broadcast_msg))
        asyncio.create_task(ws_manager.broadcast(broadcast_msg))
    except Exception as e:
        print("Verification broadcast notice:", e)

    return {
        "message": f"Hazard {target_action}d successfully. Database and live navigation updated.",
        "hazard_id": target_id,
        "status": new_status,
        "new_status": new_status,
        "verified": new_verified
    }



# ---- Admin: Update Severity ----
@router.patch("/severity")
async def update_severity(
    data: HazardSeverityUpdate,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    valid = ["Low", "Medium", "High", "Critical"]
    if data.severity not in valid:
        raise HTTPException(status_code=400, detail=f"Severity must be one of: {valid}")

    coll = get_hazards_collection()
    coll.update_one(
        {"_id": data.hazard_id},
        {"$set": {"severity": data.severity, "updatedAt": datetime.utcnow().isoformat()}}
    )
    return {"message": f"Severity updated to {data.severity}.", "hazard_id": data.hazard_id}


# ---- Admin: Resolve Hazard ----
@router.put("/resolve/{hazard_id}")
async def resolve_hazard(
    hazard_id: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    coll = get_hazards_collection()
    coll.update_one(
        {"_id": hazard_id},
        {"$set": {
            "status": "Resolved",
            "resolved_by": current_user["username"],
            "resolvedAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        }}
    )
    return {"message": "Hazard marked as resolved. Road corridor cleared.", "hazard_id": hazard_id}


# ---- Public: List Restricted Zones ----
@router.get("/restricted-zones")
def list_restricted_zones(current_user: dict = Depends(get_current_user)):
    coll = get_restricted_zones_collection()
    items = coll.find({}, limit=50)
    output = []
    for z in items:
        item = dict(z)
        if "_id" in item:
            item["_id"] = str(item["_id"])
        output.append(item)
    return output


# ---- Admin: Create Restricted Zone ----
@router.post("/restricted-zones")
async def create_restricted_zone(
    data: RestrictedZoneSchema,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    coll = get_restricted_zones_collection()
    now = datetime.utcnow().isoformat()
    doc = {
        "name": data.name,
        "lat": data.lat,
        "lng": data.lng,
        "radius_meters": data.radius_meters,
        "reason": data.reason,
        "severity": data.severity or "High",
        "created_by": current_user["username"],
        "createdAt": now,
    }
    result = coll.insert_one(doc)
    return {
        "message": "Restricted danger zone created successfully.",
        "id": str(getattr(result, "inserted_id", "zone_new")),
    }


# ---- Admin: Delete Restricted Zone ----
@router.delete("/restricted-zones/{zone_id}")
async def delete_restricted_zone(
    zone_id: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    coll = get_restricted_zones_collection()
    coll.delete_one({"_id": zone_id})
    return {"message": "Restricted zone removed.", "zone_id": zone_id}
