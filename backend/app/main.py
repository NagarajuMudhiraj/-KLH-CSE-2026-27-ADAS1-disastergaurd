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
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.utils.rate_limit import limiter

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

# Rate Limiting configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration: restrict to explicit origins
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# HTTP Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: blob: https://*.mapbox.com; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "connect-src 'self' ws: wss: http: https: https://*.mapbox.com; "
        "font-src 'self' data:;"
    )
    return response

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
