from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from app.models.schemas import (
    EmergencySOSInput, EmergencySOSOutput, EmergencyAdminCreateInput,
    SOSStatusUpdateInput, RescueTeamAssignmentInput, DispatchServiceInput,
    NotifyContactsInput, DriverLocationUpdate
)
from app.database.mongodb import get_emergency_requests_collection, get_driver_telemetry_collection
from app.utils.security import get_current_user
from datetime import datetime
from typing import List
import asyncio

router = APIRouter(prefix="/api", tags=["Emergency SOS"])

class ConnectionManager:
    """Manages active WebSocket connections for emergency dispatchers."""
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

ws_manager = ConnectionManager()

@router.websocket("/ws/emergency")
async def websocket_emergency_feed(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# ---- Send SOS (original + voice trigger support) ----
@router.post("/emergency")
async def send_emergency_sos(
    sos_data: EmergencySOSInput,
    current_user: dict = Depends(get_current_user)
):
    sos_coll = get_emergency_requests_collection()
    
    timestamp = datetime.utcnow().isoformat()
    sos_doc = {
        "username": current_user["username"],
        "disasterType": sos_data.disasterType,
        "location": {
            "lat": sos_data.lat,
            "lng": sos_data.lng,
            "address": sos_data.address or "Current GPS Position"
        },
        "status": "Pending",
        "assignedTeam": None,
        "dispatchedServices": [],
        "timestamp": timestamp,
        "updatedAt": timestamp,
    }
    
    result = sos_coll.insert_one(sos_doc)
    doc_id = str(getattr(result, "inserted_id", "sos_id_101"))
    
    response_payload = {
        "message": "Emergency SOS triggered successfully! Help teams notified.",
        "id": doc_id,
        "username": current_user["username"],
        "disasterType": sos_data.disasterType,
        "location": sos_doc["location"],
        "status": "Pending",
        "timestamp": timestamp
    }

    asyncio.create_task(ws_manager.broadcast({
        "event": "NEW_SOS",
        "data": response_payload
    }))

    return response_payload

# ---- Get Emergency List ----
@router.get("/emergency/list")
def get_emergency_list(current_user: dict = Depends(get_current_user)):
    sos_coll = get_emergency_requests_collection()
    requests = sos_coll.find({}, limit=50)
    
    output = []
    for r in requests:
        item = dict(r)
        if "_id" in item:
            item["_id"] = str(item["_id"])
        output.append(item)
    return output

# ---- Assign Rescue Team ----
@router.post("/emergency/assign")
async def assign_rescue_team(
    data: RescueTeamAssignmentInput,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    
    sos_coll = get_emergency_requests_collection()
    team_info = {
        "team_type": data.team_type,
        "eta_minutes": data.eta_minutes or 15,
        "team_contact": data.team_contact or "Control Room: 112",
        "assigned_at": datetime.utcnow().isoformat(),
        "assigned_by": current_user["username"],
    }
    sos_coll.update_one(
        {"_id": data.sos_id},
        {"$set": {
            "assignedTeam": team_info,
            "status": "Dispatched",
            "updatedAt": datetime.utcnow().isoformat(),
        }}
    )
    asyncio.create_task(ws_manager.broadcast({
        "event": "SOS_STATUS_UPDATED",
        "data": {"sos_id": data.sos_id, "status": "Dispatched", "team": team_info}
    }))
    return {"message": f"{data.team_type} assigned. ETA: {data.eta_minutes} minutes.", "sos_id": data.sos_id}

# ---- Update SOS Status ----
@router.patch("/emergency/status")
async def update_sos_status(
    data: SOSStatusUpdateInput,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    
    valid_statuses = ["Pending", "Dispatched", "In Progress", "Rescued", "Closed"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")

    sos_coll = get_emergency_requests_collection()
    sos_coll.update_one(
        {"_id": data.sos_id},
        {"$set": {"status": data.status, "updatedAt": datetime.utcnow().isoformat()}}
    )
    asyncio.create_task(ws_manager.broadcast({
        "event": "SOS_STATUS_UPDATED",
        "data": {"sos_id": data.sos_id, "status": data.status}
    }))
    return {"message": f"SOS status updated to '{data.status}'.", "sos_id": data.sos_id}

# ---- One-Click Dispatch Service ----
@router.post("/emergency/dispatch")
async def dispatch_service(
    data: DispatchServiceInput,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")

    sos_coll = get_emergency_requests_collection()
    sos = sos_coll.find_one({"_id": data.sos_id})
    if not sos:
        raise HTTPException(status_code=404, detail="SOS record not found.")
    
    dispatched = list(sos.get("dispatchedServices", []))
    dispatched.append({
        "service": data.service_type,
        "dispatched_at": datetime.utcnow().isoformat(),
        "dispatched_by": current_user["username"],
    })
    sos_coll.update_one(
        {"_id": data.sos_id},
        {"$set": {
            "dispatchedServices": dispatched,
            "status": "In Progress",
            "updatedAt": datetime.utcnow().isoformat(),
        }}
    )
    asyncio.create_task(ws_manager.broadcast({
        "event": "RESCUE_DISPATCHED",
        "data": {"sos_id": data.sos_id, "service": data.service_type}
    }))
    return {"message": f"{data.service_type} dispatched successfully.", "sos_id": data.sos_id}

# ---- Notify Emergency Contacts (simulated) ----
@router.post("/emergency/notify-contacts")
async def notify_emergency_contacts(
    data: NotifyContactsInput,
    current_user: dict = Depends(get_current_user)
):
    sos_coll = get_emergency_requests_collection()
    sos = sos_coll.find_one({"_id": data.sos_id})
    
    notifications = []
    for contact in data.contacts:
        notifications.append({
            "contact_name": contact.name,
            "phone": contact.phone,
            "relationship": contact.relationship,
            "message_sent": f"URGENT: {current_user['username']} has triggered an emergency SOS. Incident ID: {data.sos_id}. Track at: https://disasterassist.app/track/{data.sos_id}",
            "channels": ["SMS", "WhatsApp"],
            "status": "Delivered (Simulated)",
        })

    return {
        "message": f"Emergency notifications sent to {len(notifications)} contact(s).",
        "notifications": notifications,
    }

# ---- Driver Live Location Update ----
@router.post("/emergency/location-update")
async def update_driver_location(
    data: DriverLocationUpdate,
    current_user: dict = Depends(get_current_user)
):
    telemetry_coll = get_driver_telemetry_collection()
    now = datetime.utcnow().isoformat()
    telemetry_coll.update_one(
        {"username": current_user["username"]},
        {"$set": {
            "username": current_user["username"],
            "lat": data.lat,
            "lng": data.lng,
            "speed_kmh": data.speed_kmh or 0.0,
            "heading": data.heading or 0.0,
            "altitude": data.altitude or 0.0,
            "status": "Active",
            "last_updated": now,
        }},
        upsert=True,
    )
    return {"message": "Location telemetry updated.", "timestamp": now}

# ---- Admin: Create Emergency Incident Manually ----
@router.post("/emergency/manual-create")
async def create_emergency_incident(
    data: EmergencyAdminCreateInput,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required to manually create emergencies.")
    
    sos_coll = get_emergency_requests_collection()
    timestamp = datetime.utcnow().isoformat()
    sos_doc = {
        "username": data.caller_name or current_user.get("username", "admin"),
        "disasterType": data.disasterType,
        "location": {
            "lat": data.lat,
            "lng": data.lng,
            "address": data.address or "Manual Dispatch Coordinates"
        },
        "severity": data.severity or "Critical",
        "notes": data.notes or "",
        "status": data.status or "Pending",
        "createdBy": current_user.get("username", "admin"),
        "assignedTeam": None,
        "dispatchedServices": [],
        "timestamp": timestamp,
        "updatedAt": timestamp,
    }
    result = sos_coll.insert_one(sos_doc)
    doc_id = str(getattr(result, "inserted_id", "sos_manual_101"))
    sos_doc["_id"] = doc_id
    
    asyncio.create_task(ws_manager.broadcast({
        "event": "NEW_SOS",
        "data": sos_doc
    }))
    
    return {
        "message": f"Emergency incident '{data.disasterType}' created successfully.",
        "id": doc_id,
        "data": sos_doc
    }

# ---- Admin: Delete / Remove Emergency SOS Record ----
@router.delete("/emergency/{sos_id}")
async def delete_emergency_sos(
    sos_id: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required to delete emergencies.")
    
    sos_coll = get_emergency_requests_collection()
    res = sos_coll.find_one({"_id": sos_id})
    if not res:
        try:
            from bson import ObjectId
            res = sos_coll.find_one({"_id": ObjectId(sos_id)})
            if res:
                sos_coll.delete_one({"_id": ObjectId(sos_id)})
        except Exception:
            pass
    else:
        sos_coll.delete_one({"_id": sos_id})

    asyncio.create_task(ws_manager.broadcast({
        "event": "SOS_DELETED",
        "data": {"sos_id": sos_id}
    }))

    return {"message": f"Emergency incident #{sos_id} removed successfully.", "sos_id": sos_id}

