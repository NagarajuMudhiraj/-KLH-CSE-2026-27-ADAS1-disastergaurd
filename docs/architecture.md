# System Architecture

## Overview

The **Intelligent Vehicle Assistance During Disasters** system operates as an AI-powered REST API backend powered by FastAPI, MongoDB for persistent storage, and dual machine learning inference engines (YOLOv11 and XGBoost). It is designed to serve vehicular navigation clients, mobile apps, emergency response dashboards, and third-party ADAS services.

```
┌────────────────────────────────────────────────────────┐
│               API Consumers / Clients                  │
│  - Vehicle In-Cabin Units / Mobile Applications        │
│  - Emergency Services & Dashboard Clients              │
│  - REST API (JSON / Multipart Form-Data)               │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON / FormData)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Python Backend               │
│  - CORS & Middleware Security                          │
│  - JWT Bearer Authentication                           │
│  - Pydantic Data Validation Schemas                    │
└───────┬───────────────────┬───────────────────┬────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  MongoDB     │    │  YOLOv11     │    │  XGBoost     │
│  Atlas /     │    │  Image       │    │  Road Safety │
│  PyMongo     │    │  Detector    │    │  Classifier  │
│  (or Mock)   │    │  (best.pt)   │    │  (road_model)│
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Technical Flow

1. **User Authentication**:
   - Client sends credentials (`username`, `password`) to `/api/auth/register` or `/api/auth/login`.
   - FastAPI hashes passwords with Passlib (bcrypt) and generates a signed JWT token.
   - Client includes token in subsequent requests via `Authorization: Bearer <token>` headers.

2. **AI Image Detection**:
   - Client uploads a road or disaster image via `POST /api/predict`.
   - FastAPI receives image file, converts to OpenCV BGR matrix, and passes to `ultralytics.YOLO("models/best.pt")`.
   - YOLOv11 predicts bounding boxes, confidence scores, and class labels (`Flood`, `Fire`, `Landslide`, `Road Damage`).
   - Annotated image is generated with bounding boxes and saved under static assets.
   - Result metadata is stored in MongoDB `predictions` and `disasters` collections and returned in the API response.

3. **Road Safety Classification**:
   - Client sends environmental parameters (`rainfall_mm`, `traffic_level`, `water_depth_cm`) via `POST /api/predict/road-safety`.
   - Backend preprocesses input into NumPy array and feeds to `road_model.pkl` (`xgboost.XGBClassifier`).
   - Returns classification (`Safe`, `Risky`, `Blocked`), probability distribution, and safety advice.
   - Prediction log is stored in MongoDB `predictions`.

4. **Emergency SOS & Alerts**:
   - Vehicle or driver sends GPS latitude/longitude and hazard details to `POST /api/emergency/sos`.
   - Incident stored in `emergency_requests` collection with real-time status.
   - Emergency dispatchers query active disasters, SOS incidents, and nearby relief nodes (hospitals, shelters) via `/api/disasters` and `/api/emergency/requests`.
