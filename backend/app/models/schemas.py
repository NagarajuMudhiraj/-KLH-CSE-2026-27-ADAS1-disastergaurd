from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    role: Optional[str] = "driver"  # "driver" or "admin"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserProfile(BaseModel):
    username: str
    email: str
    role: str
    phone: Optional[str] = "+91 98765 43210"
    vehicle_model: Optional[str] = "Mahindra Thar 4x4 ADAS"
    vehicle_plate: Optional[str] = "KA-05-EV-2024"
    license_number: Optional[str] = "DL-1420110098765"
    blood_group: Optional[str] = "O+ Positive"
    medical_conditions: Optional[str] = "None · No major allergies"
    emergency_contact_name: Optional[str] = "Ramesh Kumar"
    emergency_contact_phone: Optional[str] = "+91 98765 12345"
    adas_auto_sos: Optional[bool] = True
    preferred_navigation: Optional[str] = "Safest Route"

class UserProfileUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_plate: Optional[str] = None
    license_number: Optional[str] = None
    blood_group: Optional[str] = None
    medical_conditions: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    adas_auto_sos: Optional[bool] = None
    preferred_navigation: Optional[str] = None

# --- Road Safety Prediction Schemas ---
class RoadPredictionInput(BaseModel):
    rainfall: float = Field(..., ge=0, description="Rainfall intensity in mm/hour")
    traffic: float = Field(..., ge=1, le=10, description="Traffic level 1 to 10")
    waterLevel: float = Field(..., ge=0, description="Water depth on road in cm")

class RoadPredictionOutput(BaseModel):
    prediction: str  # "Safe", "Risky", "Blocked"
    confidence: float
    riskScore: float
    recommendation: str
    createdAt: str

# ============================================================
# --- Future Road-Risk ML Architecture Schemas (Phase 1) ---
# ============================================================
class RoadRiskFeatures(BaseModel):
    """
    Canonical Feature Contract for future real-time Road-Risk ML model (road-risk-v2).
    Enforces physical units, validated realistic bounds, and type consistency.
    """
    # Environment Group
    rainfall_mm_h: float = Field(..., ge=0.0, le=300.0, description="Precipitation rate in mm/hour [0, 300]")
    rainfall_10min_mm: Optional[float] = Field(None, ge=0.0, le=100.0, description="10-minute rain accumulation in mm [0, 100]")
    rainfall_1h_mm: Optional[float] = Field(None, ge=0.0, le=250.0, description="1-hour rain accumulation in mm [0, 250]")
    visibility_m: Optional[float] = Field(None, ge=0.0, le=10000.0, description="Horizontal visibility in meters [0, 10000]")
    temperature_c: Optional[float] = Field(None, ge=-40.0, le=60.0, description="Ambient air temperature in Celsius [-40, 60]")
    wind_speed_kmh: Optional[float] = Field(None, ge=0.0, le=250.0, description="Wind speed in km/h [0, 250]")

    # Traffic Group
    traffic_level: float = Field(..., ge=1.0, le=10.0, description="Traffic congestion index [1.0, 10.0]")
    vehicle_density: Optional[float] = Field(None, ge=0.0, le=200.0, description="Vehicles per kilometer per lane [0, 200]")
    congestion_change: Optional[float] = Field(None, ge=-10.0, le=10.0, description="Rate of congestion change index/hour [-10, 10]")

    # Vehicle Telemetry Group
    vehicle_speed_kmh: Optional[float] = Field(None, ge=0.0, le=200.0, description="Host vehicle ground speed in km/h [0, 200]")
    acceleration_mps2: Optional[float] = Field(None, ge=-12.0, le=8.0, description="Longitudinal acceleration in m/s² [-12, 8]")
    braking_intensity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized braking pedal ratio [0.0, 1.0]")

    # Road / Geography Group
    road_slope_pct: Optional[float] = Field(None, ge=-35.0, le=35.0, description="Road slope percent grade [-35, 35]")
    elevation_m: Optional[float] = Field(None, ge=-100.0, le=6000.0, description="Elevation above sea level in meters [-100, 6000]")
    road_type: Optional[int] = Field(None, ge=0, le=4, description="Road category: 0:Urban, 1:Highway, 2:Rural, 3:Bridge, 4:Tunnel")

    # Visual Hazards Group (from YOLOv11)
    vehicle_count: Optional[int] = Field(None, ge=0, le=100, description="YOLO vehicle detection count [0, 100]")
    person_count: Optional[int] = Field(None, ge=0, le=100, description="YOLO pedestrian/victim count [0, 100]")
    fire_detected: Optional[int] = Field(None, ge=0, le=1, description="Binary visual fire indicator (0 or 1)")
    smoke_detected: Optional[int] = Field(None, ge=0, le=1, description="Binary visual smoke indicator (0 or 1)")
    flood_detected: Optional[int] = Field(None, ge=0, le=1, description="Binary visual surface water indicator (0 or 1)")
    obstacle_count: Optional[int] = Field(None, ge=0, le=50, description="Count of detected road obstacles/damage [0, 50]")
    hazard_count: Optional[int] = Field(None, ge=0, le=100, description="Total count of visual hazards [0, 100]")
    hazard_distance_m: Optional[float] = Field(None, ge=0.0, le=500.0, description="Estimated distance to nearest hazard in meters [0, 500]")

    # Disaster / Road Status Group
    flood_report: Optional[int] = Field(None, ge=0, le=1, description="Active confirmed flood report flag (0 or 1)")
    road_closure_report: Optional[int] = Field(None, ge=0, le=1, description="Official road closure notice flag (0 or 1)")


class RoadRiskPrediction(BaseModel):
    """
    Standardized Response Schema for Road-Risk prediction models.
    Enforces calibrated multi-class probability distributions and audit traceability.
    """
    predicted_class: str = Field(..., description="Target risk category: 'Safe', 'Risky', or 'Blocked'")
    safe_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated probability of Safe condition")
    risky_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated probability of Risky condition")
    blocked_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated probability of Blocked condition")
    model_version: str = Field("road-risk-v2", description="Identifies model iteration, e.g., 'synthetic-baseline-v1', 'road-risk-v2'")
    data_quality: str = Field("HIGH", description="Assessment of feature completeness: 'HIGH', 'MODERATE', 'DEGRADED'")

    @model_validator(mode='after')
    def validate_probabilities_sum(self):
        total = self.safe_probability + self.risky_probability + self.blocked_probability
        if not (0.98 <= total <= 1.02):
            raise ValueError(
                f"Probabilities must approximately sum to 1.0 (got {total:.4f}: "
                f"safe={self.safe_probability}, risky={self.risky_probability}, blocked={self.blocked_probability})"
            )
        return self

# --- Emergency SOS Schemas ---
class EmergencySOSInput(BaseModel):
    disasterType: str
    lat: float
    lng: float
    address: Optional[str] = "Current GPS Location"

class EmergencyAdminCreateInput(BaseModel):
    caller_name: Optional[str] = "Command Center Manual Dispatch"
    disasterType: str = Field(..., description="Flood, Fire, Landslide, Road Damage, Medical Emergency, Vehicle Accident, etc.")
    lat: float
    lng: float
    address: Optional[str] = "Manual Dispatch Coordinates"
    severity: Optional[str] = "Critical"
    notes: Optional[str] = ""
    status: Optional[str] = "Pending"

class EmergencySOSOutput(BaseModel):
    id: str
    username: str
    disasterType: str
    location: Dict[str, Any]
    status: str
    timestamp: str


# --- Disaster Schema ---
class DisasterSchema(BaseModel):
    disasterType: str
    location: Dict[str, Any]
    severity: str
    image: Optional[str] = None
    detectedBy: str
    createdAt: str

# --- Dashboard Schemas ---
class DashboardSummary(BaseModel):
    totalPredictions: int
    totalDisasters: int
    activeEmergencies: int
    registeredUsers: int
    roadStatusCounts: Dict[str, int]
    disasterTypeCounts: Dict[str, int]
    recentEmergencies: List[Dict[str, Any]]

# ============================================================
# --- Route Safety Schemas ---
# ============================================================
class RouteAnalysisInput(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    avoid_hazard_types: Optional[List[str]] = []

class DestinationNode(BaseModel):
    id: str
    lat: float
    lng: float
    name: str

class BatchRouteAnalysisInput(BaseModel):
    origin_lat: float
    origin_lng: float
    destinations: List[DestinationNode]
    avoid_hazard_types: Optional[List[str]] = []

class RouteSegment(BaseModel):
    from_point: List[float]  # [lat, lng]
    to_point: List[float]
    risk_level: str  # "Safe", "Caution", "Danger"
    risk_score: float
    hazard_type: Optional[str] = None
    advisory: str

class AlternateRoute(BaseModel):
    route_id: str
    route_name: str
    waypoints: List[List[float]]  # list of [lat, lng]
    risk_score: float  # 0-100
    distance_km: float
    estimated_time_min: float
    hazard_intersections: int
    is_recommended: bool
    route_color: str
    segments: List[RouteSegment]
    summary: str

class SafeRouteResult(BaseModel):
    origin: List[float]
    destination: List[float]
    routes: List[AlternateRoute]
    active_hazards_nearby: int
    analysis_timestamp: str
    overall_area_risk: str

# ============================================================
# --- Hazard Management Schemas ---
# ============================================================
class HazardReportInput(BaseModel):
    disasterType: str = Field(..., description="Flood, Fire, Landslide, Road Damage, etc.")
    lat: float
    lng: float
    severity: Optional[str] = "Medium"  # Low, Medium, High, Critical
    address: Optional[str] = "GPS Location"
    description: Optional[str] = ""
    image_base64: Optional[str] = None
    depth_cm: Optional[float] = None

class HazardVerificationInput(BaseModel):
    hazard_id: Optional[str] = None
    action: str = "approve"  # "approve" or "reject"
    admin_note: Optional[str] = ""

class HazardSeverityUpdate(BaseModel):
    hazard_id: str
    severity: str  # Low, Medium, High, Critical

class RestrictedZoneSchema(BaseModel):
    name: str
    lat: float
    lng: float
    radius_meters: float = Field(..., ge=100, le=50000)
    reason: str
    severity: Optional[str] = "High"

class AdminHazardCreateInput(BaseModel):
    type: str = Field(..., description="Flood, Fire, Smoke, Pothole, Road Damage, Accident, Road Block, Heavy Traffic, Other")
    latitude: float
    longitude: float
    address: Optional[str] = "Selected Location"
    severity: str = Field("High", description="Low, Medium, High, Critical")
    description: Optional[str] = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = "ACTIVE"  # ACTIVE, INACTIVE

class AdminHazardUpdateInput(BaseModel):
    type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None

class AIDetectedHazardInput(BaseModel):
    source: str = "AI"
    type: str = Field(..., description="flood, fire, smoke, pothole, road damage, etc.")
    confidence: float = Field(..., ge=0.0, le=1.0)
    latitude: float
    longitude: float
    timestamp: Optional[str] = None
    severity: Optional[str] = "HIGH"
    depth_cm: Optional[float] = None
    distance_m: Optional[float] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    status: Optional[str] = "PENDING_REVIEW"

# ============================================================
# --- Rescue Operations Schemas ---
# ============================================================
class SOSStatusUpdateInput(BaseModel):
    sos_id: str
    status: str  # Pending, Dispatched, In Progress, Rescued, Closed

class RescueTeamAssignmentInput(BaseModel):
    sos_id: str
    team_type: str  # NDRF, Police QRT, Medical Unit, Fire Brigade
    eta_minutes: Optional[int] = 15
    team_contact: Optional[str] = ""

class DispatchServiceInput(BaseModel):
    sos_id: str
    service_type: str  # Ambulance, Police, Fire, Relief

class EmergencyContactSchema(BaseModel):
    name: str
    phone: str
    relationship: str

class NotifyContactsInput(BaseModel):
    sos_id: str
    contacts: List[EmergencyContactSchema]

class DriverLocationUpdate(BaseModel):
    lat: float
    lng: float
    speed_kmh: Optional[float] = 0.0
    heading: Optional[float] = 0.0
    altitude: Optional[float] = 0.0

# ============================================================
# --- Broadcast System Schemas ---
# ============================================================
class BroadcastAlertInput(BaseModel):
    alert_type: str  # Evacuation, Severe Weather, Road Closure, General
    title: str
    message: str
    target_lat: Optional[float] = None
    target_lng: Optional[float] = None
    radius_km: Optional[float] = 50.0
    severity: Optional[str] = "High"

class BroadcastAlertOutput(BaseModel):
    id: str
    alert_type: str
    title: str
    message: str
    sent_by: str
    timestamp: str
    active: bool

# ============================================================
# --- AI & System Monitoring Schemas ---
# ============================================================
class DetectionLogSchema(BaseModel):
    image_id: str
    detected_class: str
    confidence: float
    inference_time_ms: float
    is_false_positive: Optional[bool] = False
    timestamp: str

class SystemHealthStatus(BaseModel):
    cpu_percent: float
    memory_percent: float
    avg_inference_ms: float
    db_latency_ms: float
    yolo_model_status: str
    xgboost_model_status: str
    active_websocket_connections: int
    uptime_seconds: float

class FalsePositiveFeedbackInput(BaseModel):
    log_id: str
    reason: Optional[str] = "Incorrect detection"

# ============================================================
# --- Driver Telemetry Schemas ---
# ============================================================
class DriverTelemetrySchema(BaseModel):
    username: str
    lat: float
    lng: float
    speed_kmh: float
    heading: float
    status: str  # Active, Idle, Emergency, Offline
    last_updated: str

class DriverSafetyScore(BaseModel):
    username: str
    overall_score: float  # 0-100
    hazard_avoidance_score: float
    sos_compliance_score: float
    travel_safety_score: float
    total_trips: int
    total_hazards_reported: int
    total_sos_triggered: int
