import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import pymongo
from pymongo import MongoClient

class InMemoryCollection:
    """Fallback in-memory collection when MongoDB is offline."""
    def __init__(self, name: str):
        self.name = name
        self._data: List[Dict[str, Any]] = []
        self._counter = 1

    def _match_doc(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        if not query:
            return True
        for k, v in query.items():
            if k == "$or" and isinstance(v, list):
                if not any(self._match_doc(doc, sub_q) for sub_q in v):
                    return False
            elif k == "$and" and isinstance(v, list):
                if not all(self._match_doc(doc, sub_q) for sub_q in v):
                    return False
            elif isinstance(v, dict):
                doc_val = doc.get(k)
                for op, op_val in v.items():
                    if op == "$in" and doc_val not in op_val:
                        return False
                    elif op == "$nin" and doc_val in op_val:
                        return False
                    elif op == "$ne" and doc_val == op_val:
                        return False
                    elif op == "$eq" and doc_val != op_val:
                        return False
                    elif op == "$gt" and not (doc_val is not None and doc_val > op_val):
                        return False
                    elif op == "$gte" and not (doc_val is not None and doc_val >= op_val):
                        return False
                    elif op == "$lt" and not (doc_val is not None and doc_val < op_val):
                        return False
                    elif op == "$lte" and not (doc_val is not None and doc_val <= op_val):
                        return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    def insert_one(self, document: Dict[str, Any]):
        doc_copy = dict(document)
        if "_id" not in doc_copy:
            doc_copy["_id"] = str(self._counter)
            self._counter += 1
        self._data.append(doc_copy)
        class InsertResult:
            inserted_id = doc_copy["_id"]
        return InsertResult()

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for item in self._data:
            if self._match_doc(item, query):
                return item
        return None

    def find(self, query: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        query = query or {}
        results = []
        for item in self._data:
            if self._match_doc(item, query):
                results.append(item)
            if len(results) >= limit:
                break
        class FindCursor(list):
            def count(self):
                return len(self)
            def limit(self, n: int):
                return FindCursor(self[:n])
            def sort(self, key, direction=1):
                try:
                    rev = (direction == -1 or direction == pymongo.DESCENDING)
                    sorted_list = sorted(self, key=lambda x: str(x.get(key, "")), reverse=rev)
                    return FindCursor(sorted_list)
                except Exception:
                    return self
        return FindCursor(results)

    def find_one_and_update(self, query: Dict[str, Any], update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for item in self._data:
            if self._match_doc(item, query):
                item.update(update.get("$set", {}))
                return item
        return None

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        for item in self._data:
            if self._match_doc(item, query):
                item.update(update.get("$set", {}))
                return
        if upsert:
            document = dict(query)
            document.update(update.get("$set", {}))
            self.insert_one(document)

    def update_many(self, query: Dict[str, Any], update: Dict[str, Any]):
        for item in self._data:
            if self._match_doc(item, query):
                item.update(update.get("$set", {}))

    def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        query = query or {}
        return sum(1 for item in self._data if self._match_doc(item, query))

    def delete_one(self, query: Dict[str, Any]):
        for i, item in enumerate(self._data):
            if self._match_doc(item, query):
                self._data.pop(i)
                return

    def delete_many(self, query: Dict[str, Any]):
        initial_len = len(self._data)
        self._data = [item for item in self._data if not self._match_doc(item, query)]
        deleted_count = initial_len - len(self._data)
        class DeleteResult:
            def __init__(self, count):
                self.deleted_count = count
        return DeleteResult(deleted_count)


class MongoDBManager:
    """MongoDB Atlas & Local connection manager with automatic in-memory fallback."""
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self.collections: Dict[str, Any] = {}

    def connect(self):
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("DB_NAME", "disaster_assistance_db")

        try:
            print(f"Connecting to MongoDB at {mongo_url}...")
            self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            self.is_connected = True
            print(f"Successfully connected to MongoDB Database: {db_name}")
        except Exception as e:
            print(f"MongoDB connection note ({e}). Initializing In-Memory Fallback Storage.")
            self.is_connected = False
            self.db = None


    def get_collection(self, collection_name: str):
        if self.is_connected and self.db is not None:
            return self.db[collection_name]
        if collection_name not in self.collections:
            self.collections[collection_name] = InMemoryCollection(collection_name)
        return self.collections[collection_name]

# Global database manager instance
db_manager = MongoDBManager()

def get_users_collection():
    return db_manager.get_collection("users")

def get_vehicles_collection():
    return db_manager.get_collection("vehicles")

def get_predictions_collection():
    return db_manager.get_collection("predictions")

def get_disasters_collection():
    return db_manager.get_collection("disasters")

def get_hazards_collection():
    return db_manager.get_collection("disasters")

def get_emergency_requests_collection():
    return db_manager.get_collection("emergency_requests")

def get_restricted_zones_collection():
    return db_manager.get_collection("restricted_zones")

def get_broadcast_alerts_collection():
    return db_manager.get_collection("broadcast_alerts")

def get_driver_telemetry_collection():
    return db_manager.get_collection("driver_telemetry")

def get_detection_logs_collection():
    return db_manager.get_collection("detection_logs")

def get_travel_history_collection():
    return db_manager.get_collection("travel_history")

def get_disaster_zones_collection():
    return db_manager.get_collection("disaster_zones")

def seed_default_users():
    """Seeds default demo admin and driver credentials if not already present."""
    from app.utils.security import hash_password
    users_coll = get_users_collection()
    
    demo_users = [
        {
            "username": "admin",
            "email": "admin@emergency.org",
            "password": hash_password("admin123"),
            "role": "admin",
            "full_name": "HQ Incident Commander",
            "createdAt": datetime.utcnow().isoformat()
        },
        {
            "username": "driver",
            "email": "driver@emergency.org",
            "password": hash_password("driver123"),
            "role": "driver",
            "full_name": "Emergency Responder",
            "createdAt": datetime.utcnow().isoformat()
        }
    ]

    for u in demo_users:
        existing = users_coll.find_one({"username": u["username"]})
        if not existing:
            users_coll.insert_one(u)
            print(f"[AUTH SEED] Created demo user: {u['username']} (role: {u['role']})")


def seed_initial_hazards():
    """Seeds real corridor hazard records if collection is empty so admin actions can manage them."""
    hazards_coll = get_hazards_collection()
    if hazards_coll.count_documents() > 0:
        return

    now = datetime.utcnow().isoformat()
    initial_hazards = [
        {
            "_id": "1",
            "id": "1",
            "source": "AI",
            "type": "flood",
            "disasterType": "Flood",
            "name": "Flood Inundation",
            "latitude": 15.3647,
            "longitude": 75.1240,
            "lat": 15.3647,
            "lng": 75.1240,
            "location": {"lat": 15.3647, "lng": 75.1240, "address": "Hubballi Bypass Corridor"},
            "address": "Hubballi Bypass Corridor",
            "severity": "HIGH",
            "description": "Flash water accumulation across 2 driving lanes.",
            "status": "ACTIVE",
            "verified": True,
            "created_by": "YOLOv11 Dashcam",
            "created_at": now,
            "updated_at": now
        },
        {
            "_id": "2",
            "id": "2",
            "source": "USER",
            "type": "road damage",
            "disasterType": "Road Damage",
            "name": "Road Damage",
            "latitude": 15.3524,
            "longitude": 75.1388,
            "lat": 15.3524,
            "lng": 75.1388,
            "location": {"lat": 15.3524, "lng": 75.1388, "address": "Station Road Junction"},
            "address": "Station Road Junction",
            "severity": "MEDIUM",
            "description": "Deep asphalt rupture and potholes reported by citizen.",
            "status": "ACTIVE",
            "verified": True,
            "created_by": "driver",
            "created_at": now,
            "updated_at": now
        },
        {
            "_id": "3",
            "id": "3",
            "source": "ADMIN",
            "type": "fire hazard",
            "disasterType": "Fire Hazard",
            "name": "Fire Hazard",
            "latitude": 15.3617,
            "longitude": 75.0849,
            "lat": 15.3617,
            "lng": 75.0849,
            "location": {"lat": 15.3617, "lng": 75.0849, "address": "Airport Road Sector 4"},
            "address": "Airport Road Sector 4",
            "severity": "CRITICAL",
            "description": "Fuel spill and active grass fire near roadside.",
            "status": "ACTIVE",
            "verified": True,
            "created_by": "admin",
            "created_at": now,
            "updated_at": now
        }
    ]
    for h in initial_hazards:
        hazards_coll.insert_one(h)
    print(f"[HAZARD SEED] Initialized {len(initial_hazards)} real corridor hazards.")


