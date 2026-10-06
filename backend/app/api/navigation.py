from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from app.database.mongodb import get_disaster_zones_collection, get_hazards_collection, get_disasters_collection
from app.services.dijkstra_routing import dijkstra_engine

router = APIRouter(prefix="/api/navigation", tags=["Google Maps Disaster Navigation & Dijkstra"])

class RoutePlanRequest(BaseModel):
    origin_lat: float = Field(..., description="Latitude of start position")
    origin_lng: float = Field(..., description="Longitude of start position")
    destination_lat: float = Field(..., description="Latitude of destination position")
    destination_lng: float = Field(..., description="Longitude of destination position")
    avoid_critical: bool = True
    temp_hazard: Optional[Dict[str, Any]] = None

class DisasterZoneInput(BaseModel):
    name: str = Field(..., example="Flooded Main Bridge")
    lat: float
    lng: float
    radius_meters: float = Field(1000.0, example=1000.0)
    risk_level: str = Field("Red", example="Red")  # Green, Yellow, Red, Purple
    reason: str = Field("Severe Inundation", example="Severe Inundation")

class ConnectionManager:
    """Manages active WebSocket connections for disaster updates."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

disaster_ws_manager = ConnectionManager()

# Default disaster zones if database is unpopulated
DEFAULT_DISASTER_ZONES = [
    {
        "_id": "dz_green_1",
        "name": "Low Risk Flood Monitoring Zone",
        "lat": 13.0827,
        "lng": 80.2707,
        "radius_meters": 1200,
        "risk_level": "Green",
        "reason": "Minor water accumulation on curb"
    },
    {
        "_id": "dz_yellow_1",
        "name": "Moderate Waterlogging Zone",
        "lat": 13.0674,
        "lng": 80.2376,
        "radius_meters": 1500,
        "risk_level": "Yellow",
        "reason": "Slower traffic due to 0.3m standing water"
    },
    {
        "_id": "dz_red_1",
        "name": "High Risk Submerged Expressway",
        "lat": 13.0405,
        "lng": 80.2337,
        "radius_meters": 2000,
        "risk_level": "Red",
        "reason": "Severe flood waters (0.8m) - High vehicle hazard"
    },
    {
        "_id": "dz_purple_1",
        "name": "Critical Collapse & Flash Flood Danger",
        "lat": 13.0102,
        "lng": 80.2156,
        "radius_meters": 2500,
        "risk_level": "Purple",
        "reason": "Bridge damage & extreme surge - Strictly IMPASSABLE"
    }
]

@router.get("/disaster-zones")
def get_disaster_zones(lat: Optional[float] = None, lng: Optional[float] = None):
    """Retrieve all colored disaster risk zones (Green, Yellow, Red, Purple)."""
    coll = get_disaster_zones_collection()
    items = list(coll.find({}))
    if not items:
        if lat is not None and lng is not None:
            return [
                {
                    "_id": "dz_green_local",
                    "name": "Low Risk Curb Inundation Zone",
                    "lat": round(lat + 0.009, 5),
                    "lng": round(lng + 0.008, 5),
                    "radius_meters": 800,
                    "risk_level": "Green",
                    "reason": "Minor water accumulation on curb"
                },
                {
                    "_id": "dz_yellow_local",
                    "name": "Moderate Waterlogging Zone",
                    "lat": round(lat - 0.008, 5),
                    "lng": round(lng + 0.010, 5),
                    "radius_meters": 1200,
                    "risk_level": "Yellow",
                    "reason": "Slower traffic due to 0.3m standing water"
                },
                {
                    "_id": "dz_red_local",
                    "name": "High Risk Flooded Underpass",
                    "lat": round(lat + 0.014, 5),
                    "lng": round(lng - 0.009, 5),
                    "radius_meters": 1600,
                    "risk_level": "Red",
                    "reason": "Severe flood waters (0.8m) - High vehicle hazard"
                },
                {
                    "_id": "dz_purple_local",
                    "name": "Critical Collapse & Flash Surge Danger",
                    "lat": round(lat - 0.015, 5),
                    "lng": round(lng - 0.012, 5),
                    "radius_meters": 2000,
                    "risk_level": "Purple",
                    "reason": "Culvert collapse & active surge - Strictly IMPASSABLE"
                }
            ]
        return DEFAULT_DISASTER_ZONES

    output = []
    for z in items:
        item = dict(z)
        if "_id" in item:
            item["_id"] = str(item["_id"])
        output.append(item)
    return output

@router.post("/disaster-zones")
async def create_disaster_zone(data: DisasterZoneInput):
    """Add a new disaster risk zone and broadcast live WebSocket update."""
    valid_risks = ["Green", "Yellow", "Red", "Purple"]
    if data.risk_level not in valid_risks:
        raise HTTPException(status_code=400, detail=f"risk_level must be one of: {valid_risks}")

    coll = get_disaster_zones_collection()
    now = datetime.utcnow().isoformat()
    doc = {
        "name": data.name,
        "lat": data.lat,
        "lng": data.lng,
        "radius_meters": data.radius_meters,
        "risk_level": data.risk_level,
        "reason": data.reason,
        "createdAt": now
    }
    result = coll.insert_one(doc)
    doc_id = str(getattr(result, "inserted_id", "zone_new"))
    doc["_id"] = doc_id

    # Broadcast via WebSocket
    asyncio.create_task(disaster_ws_manager.broadcast({
        "event": "DISASTER_ZONE_ADDED",
        "data": doc
    }))

    return {"message": "Disaster risk zone created successfully.", "zone": doc}

@router.post("/route")
def plan_dijkstra_route(req: RoutePlanRequest):
    """
    Plan safe navigation route using Modified Dijkstra Risk-Weighted Algorithm.
    Evaluates origin, destination, disaster risk zones (Green/Yellow/Red/Purple) and active hazards.
    """
    origin = (req.origin_lat, req.origin_lng)
    dest = (req.destination_lat, req.destination_lng)

    # Fetch zones & hazards
    coll_zones = get_disaster_zones_collection()
    zones = list(coll_zones.find({})) or DEFAULT_DISASTER_ZONES

    coll_hazards = get_hazards_collection()
    coll_disasters = get_disasters_collection()
    raw_hazards = list(coll_hazards.find({})) + list(coll_disasters.find({}))

    # Only include active, verified hazards (strictly exclude rejected hazards)
    hazards = []
    for h in raw_hazards:
        st = str(h.get("status", "ACTIVE")).upper()
        if st in ["REJECTED", "INACTIVE", "RESOLVED"] or h.get("verified") is False:
            continue
        hazards.append(h)

    if req.temp_hazard and str(req.temp_hazard.get("status", "ACTIVE")).upper() != "REJECTED":
        hazards.append(req.temp_hazard)

    # Execute Dijkstra pathfinding
    result = dijkstra_engine.run_modified_dijkstra(
        origin=origin,
        dest=dest,
        disaster_zones=zones,
        hazards=hazards,
        detour_bias=0.02
    )

    return result

@router.websocket("/ws/disasters")
async def websocket_disaster_feed(websocket: WebSocket):
    """WebSocket stream for real-time disaster alerts & dynamic route re-evaluations."""
    await disaster_ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back keepalive ping if needed
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        disaster_ws_manager.disconnect(websocket)
    except Exception:
        disaster_ws_manager.disconnect(websocket)
