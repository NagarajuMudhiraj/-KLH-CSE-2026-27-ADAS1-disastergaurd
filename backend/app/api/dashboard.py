from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.database.mongodb import (
    get_predictions_collection,
    get_disasters_collection,
    get_emergency_requests_collection,
    get_users_collection
)
from app.utils.security import get_current_user
from math import asin, cos, radians, sin, sqrt

router = APIRouter(prefix="/api", tags=["Dashboard & Analytics"])

def normalize_hazard_type(val: str) -> str:
    if not val:
        return "Other"
    v = str(val).lower()
    if "flood" in v:
        return "Flood"
    elif "fire" in v:
        return "Fire"
    elif "smoke" in v:
        return "Smoke"
    elif "landslide" in v:
        return "Landslide"
    elif "damage" in v:
        return "Road Damage"
    elif "person" in v or "victim" in v:
        return "Person in Distress"
    elif "vehicle" in v:
        return "Stranded Vehicle"
    return str(val).title()

@router.get("/dashboard")
def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    pred_coll = get_predictions_collection()
    disasters_coll = get_disasters_collection()
    sos_coll = get_emergency_requests_collection()
    users_coll = get_users_collection()

    all_predictions = pred_coll.find({})
    total_predictions = len(all_predictions)

    all_disasters = disasters_coll.find({})
    total_disasters = len(all_disasters)

    all_emergencies = sos_coll.find({})
    active_emergencies = len(all_emergencies)

    all_users = users_coll.find({})
    total_users = max(len(all_users), 1)

    # Calculate status counts
    road_status_counts = {"Safe": 0, "Risky": 0, "Blocked": 0}
    disaster_type_counts = {
        "Flood": 0,
        "Fire": 0,
        "Smoke": 0,
        "Landslide": 0,
        "Road Damage": 0,
        "Person in Distress": 0,
        "Stranded Vehicle": 0
    }

    for p in all_predictions:
        p_val = p.get("prediction")
        if p_val in road_status_counts:
            road_status_counts[p_val] += 1
        elif p_val:
            normalized = normalize_hazard_type(p_val)
            disaster_type_counts[normalized] = disaster_type_counts.get(normalized, 0) + 1

    for d in all_disasters:
        d_type = d.get("disasterType")
        if d_type:
            normalized = normalize_hazard_type(d_type)
            disaster_type_counts[normalized] = disaster_type_counts.get(normalized, 0) + 1

    recent_sos = []
    for sos in list(all_emergencies)[-5:]:
        item = dict(sos)
        if "_id" in item:
            item["_id"] = str(item["_id"])
        recent_sos.append(item)

    return {
        "totalPredictions": total_predictions,
        "totalDisasters": total_disasters,
        "activeEmergencies": active_emergencies,
        "registeredUsers": total_users,
        "roadStatusCounts": road_status_counts,
        "disasterTypeCounts": disaster_type_counts,
        "recentEmergencies": recent_sos
    }

@router.get("/history")
def get_prediction_history(
    user_filter: Optional[str] = Query(None),
    disaster_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    pred_coll = get_predictions_collection()
    query = {}
    if user_filter:
        query["username"] = user_filter
    if disaster_type:
        query["prediction"] = disaster_type

    history = pred_coll.find(query, limit=100)
    output = []
    for h in history:
        item = dict(h)
        if "_id" in item:
            item["_id"] = str(item["_id"])
        output.append(item)

    return output

@router.get("/disasters")
def get_disasters_list():
    disasters_coll = get_disasters_collection()
    disasters = disasters_coll.find({
        "status": {"$nin": ["REJECTED", "Rejected", "INACTIVE", "Inactive", "RESOLVED", "Resolved"]}
    }, limit=100)
    
    output = []
    for d in disasters:
        st = str(d.get("status", "ACTIVE")).upper()
        if st in ["REJECTED", "INACTIVE", "RESOLVED"] or d.get("verified") is False:
            continue
        item = dict(d)
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
        if not item.get("location") and lat is not None and lng is not None:
            item["location"] = {
                "lat": lat,
                "lng": lng,
                "address": item.get("address", "GPS coordinates"),
            }
        item["latitude"] = lat
        item["longitude"] = lng
        item["lat"] = lat
        item["lng"] = lng
        output.append(item)

    return output

@router.get("/spatial-nodes")
def get_live_spatial_nodes(lat: float = Query(..., ge=-90, le=90), lng: float = Query(..., ge=-180, le=180), radius_m: int = Query(12000, ge=500, le=30000)):
    """
    Query OpenStreetMap Overpass API live for real nearby hospitals,
    police stations, and emergency relief nodes around the driver's GPS location.
    """
    import requests
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:20];
    (
      nwr["amenity"="hospital"](around:{radius_m},{lat},{lng});
      nwr["amenity"="clinic"](around:{radius_m},{lat},{lng});
      nwr["amenity"="police"](around:{radius_m},{lat},{lng});
      nwr["amenity"="fire_station"](around:{radius_m},{lat},{lng});
      nwr["amenity"="shelter"](around:{radius_m},{lat},{lng});
      nwr["social_facility"="shelter"](around:{radius_m},{lat},{lng});
    );
    out center tags 100;
    """
    
    nodes = []
    try:
        resp = requests.post(overpass_url, data={'data': overpass_query}, timeout=25)
        if resp.status_code == 200:
            elements = resp.json().get("elements", [])
            for elem in elements:
                tags = elem.get("tags", {})
                name = tags.get("name") or tags.get("name:en")
                amenity = tags.get("amenity")
                node_type = amenity or tags.get("social_facility") or "shelter"
                point = elem.get("center", elem)
                node_lat, node_lng = point.get("lat"), point.get("lon")
                if node_lat is None or node_lng is None:
                    continue
                distance_km = 2 * 6371 * asin(sqrt(
                    sin(radians(node_lat - lat) / 2) ** 2
                    + cos(radians(lat)) * cos(radians(node_lat)) * sin(radians(node_lng - lng) / 2) ** 2
                ))
                nodes.append({
                    "id": f"{elem.get('type', 'node')}-{elem.get('id')}",
                    "name": name or tags.get("operator") or "Unnamed emergency facility",
                    "type": node_type,
                    "lat": node_lat,
                    "lng": node_lng,
                    "distance_km": round(distance_km, 2),
                    "contact": tags.get("contact:phone") or tags.get("phone") or "Not published",
                })
    except Exception as e:
        print(f"Overpass API live query error: {e}")

    return sorted(nodes, key=lambda node: node["distance_km"])
