import os
from dotenv import load_dotenv

# Keep Ultralytics runtime settings inside the project.  The default Windows
# user-level location can be unavailable in restricted desktop environments.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(project_root, ".ultralytics-config"))

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.mongodb import db_manager
from app.services.ai_service import ai_engine
from app.api import auth, prediction, road_prediction, emergency, dashboard, weather
from app.api import routes_safety, hazards, admin_control, navigation

from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Starting Disaster-Aware Driver Safety & Emergency Response Server ---")
    db_manager.connect()
    from app.database.mongodb import seed_default_users, seed_initial_hazards
    seed_default_users()
    seed_initial_hazards()
    # Pre-warm AI engines
    _ = ai_engine.yolo_model
    _ = ai_engine.xgboost_model
    print("--- Server Initialization Complete ---")
    yield
    print("--- Shutting Down Server ---")

app = FastAPI(
    title="Disaster-Aware Driver Safety & Emergency Response API",
    description=(
        "Production-grade AI-powered real-time disaster and road hazard management platform. "
        "Features: YOLOv11 hazard detection, route safety analysis, emergency SOS dispatch, "
        "admin disaster control center, WebSocket real-time feeds, and spatial radar."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for output assets
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ---- Register Core API Routers ----
app.include_router(auth.router)
app.include_router(prediction.router)
app.include_router(road_prediction.router)
app.include_router(emergency.router)
app.include_router(dashboard.router)
app.include_router(weather.router)

# ---- Register New Feature Routers ----
app.include_router(routes_safety.router)
app.include_router(hazards.router)
app.include_router(admin_control.router)
app.include_router(navigation.router)

@app.get("/")
@app.get("/api/")
@app.get("/api/health")
def read_root():
    return {
        "status": "Online",
        "service": "Disaster-Aware Driver Safety & Emergency Response System",
        "version": "2.0.0",
        "database_connected": db_manager.is_connected,
        "yolo_loaded": ai_engine.yolo_model is not None,
        "xgboost_loaded": ai_engine.xgboost_model is not None,
        "features": [
            "YOLOv11 Hazard Detection",
            "Route Safety Analysis & Detours",
            "Emergency SOS Dispatch",
            "Admin Disaster Control Center",
            "Real-Time WebSocket Emergency Feed",
            "Hazard Lifecycle Management",
            "Area-Wide Broadcast Alerts",
            "Spatial Disaster Radar",
        ]
    }
