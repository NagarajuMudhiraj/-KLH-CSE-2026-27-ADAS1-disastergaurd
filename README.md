# Intelligent Vehicle Assistance During Disasters

An AI-powered backend service and API designed to assist drivers and emergency teams during natural disasters by detecting road hazards from images using **YOLOv11**, predicting road safety status based on weather and traffic metrics using **XGBoost**, and managing real-time emergency SOS alerts and route safety.

---

## 📌 Features

- 🔐 **User Authentication**: Secure JWT-based auth with password hashing (bcrypt) supporting Driver and Admin roles.
- 🖼️ **AI Disaster Detection**: Upload road/disaster images to detect **Flood**, **Fire**, **Landslide**, and **Road Damage** with visual bounding boxes and confidence scores using **YOLOv11**.
- 🛣️ **Road Safety Prediction**: Real-time road safety classification (**Safe**, **Risky**, **Blocked**) based on rainfall, traffic level, and water depth using **XGBoost**.
- 🚨 **Emergency SOS System**: Real-time SOS alert dispatch sending GPS coordinates and hazard details to MongoDB.
- 📊 **Dashboard & Analytics API**: Aggregated disaster statistics, safety distributions, and live incident queries.
- 🕒 **Prediction History**: Complete queryable audit trail of past predictions with filtering capability.
- ⚙️ **Admin Management APIs**: Centralized endpoints for registered drivers, pending SOS requests, and disaster logs.

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: React 19 + Vite 8
- **Styling**: Vanilla CSS Design System with Dark Glassmorphism HUD Theme
- **Mapping**: Leaflet (CartoDB Dark Matter Tiles, Custom Risk Circles, Overpass API Relief Nodes)
- **Visualizations**: Chart.js & React-ChartJS-2 (Doughnut & Bar Analytics)
- **Icons**: Lucide React
- **HTTP & State**: Axios & React Context API (with automatic JWT injection)

### Backend
- **Language**: Python 3.12
- **Web Framework**: FastAPI & Uvicorn
- **Data Validation**: Pydantic v2
- **Database**: MongoDB Atlas / PyMongo (with resilient mock fallback)
- **Auth**: JWT (PyJWT / Passlib bcrypt)

### AI & Machine Learning
- **Computer Vision**: Ultralytics YOLOv11 & OpenCV
- **Safety Classifier**: XGBoost Classifier
- **Pathfinding**: Modified Dijkstra Risk-Weighted Engine & Disaster-Aware A*

---

## 📁 Project Structure

```
.
├── frontend/             # React 19 + Vite Dark HUD Web Application
│   ├── src/
│   │   ├── components/   # Navbar, HUD widgets
│   │   ├── pages/        # Dashboard, Detection, RoadSafety, DisasterRadar, EmergencySOS, AdminControl, Profile
│   │   ├── context/      # AuthContext (Role switcher & JWT state)
│   │   ├── services/     # Axios API service proxying to backend
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css     # Automotive HUD Dark Glassmorphism Theme
│   ├── vite.config.js    # Proxy configuration for /api and WebSockets
│   └── package.json
├── backend/              # Python FastAPI Server
│   ├── app/
│   │   ├── api/          # Auth, Detections, Road Safety, SOS, Radar, Admin, Weather
│   │   ├── database/     # MongoDB Connection & Mock Storage Fallback
│   │   ├── services/     # YOLOv11, XGBoost & Dijkstra Routing Engines
│   │   ├── utils/        # JWT & Password Hashing Utilities
│   │   └── main.py       # FastAPI Entry Point
│   └── requirements.txt
├── datasets/             # Directory for RDD2022, FloodNet, FLAME datasets
├── models/               # Model weights (best.pt, road_model.pkl)
├── docs/                 # Documentation (Architecture, Schema, API, Training)
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup

Clone the repository and ensure Python 3.12+ and Node.js 18+ are installed.

### 2. Backend Setup & Run

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

```
- Backend server: `http://localhost:8000`
- Swagger API Docs: `http://localhost:8000/docs`

### 3. Frontend Setup & Run

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
- Frontend application: `http://localhost:5173`

### 4. 🔑 Demo Login Credentials

The platform includes pre-seeded operational accounts for testing both Driver and Admin workflows:

| Operational Role | Username | Password | Dedicated Access & Capabilities |
| :--- | :--- | :--- | :--- |
| **Driver & Citizen** | `driver` | `driver123` | Live GPS Map Navigation, YOLOv11s Hazard Vision, Pothole Depth & Road Risk Telemetry, Emergency SOS |
| **HQ Incident Admin** | `admin` | `admin123` | City-Wide Incident Command Center, Custom Hazard Geo-Pinning, SOS Rescue Dispatch Center |

---

## 🧠 AI Models & Datasets

1. **YOLOv11 Object Detection**:
   - **Classes**: `Flood`, `Fire`, `Landslide`, `Road Damage`
   - **Target Datasets**: RDD2022 (Road Damage), FloodNet (Flooding), FLAME (Fire)
   - **Training Script**: `training/train_yolo.py`

2. **XGBoost Road Classifier**:
   - **Input Features**: `Rainfall (mm/h)`, `Traffic Level (1-10)`, `Water Level (cm)`
   - **Outputs**: `Safe`, `Risky`, `Blocked`
   - **Training Script**: `training/train_xgboost.py`

---

## 📚 Research Papers & Downloadable Dataset Links

### 1. 🌊 FloodNet Dataset & Paper
- 📥 **Dataset Source**: [FloodNet Challenge (BinaLab GitHub)](https://github.com/BinaLab/FloodNet-Challenge-EARTHVISION2021)
- 📄 **Research Paper**: [FloodNet: A High-Resolution Aerial Imagery Dataset for Post-Disaster Damage Assessment](https://arxiv.org/abs/2012.02951)
- ⬇️ **Download Paper PDF**: [arXiv 2012.02951 PDF](https://arxiv.org/pdf/2012.02951.pdf)

### 2. 🛣️ RDD2022 (Road Damage Detection) Dataset & Paper
- ⬇️ **Download Paper PDF**: [arXiv 2209.08538 PDF](https://arxiv.org/pdf/2209.08538.pdf)

### 3. 🔥 FLAME (Wildfire Aerial Imagery) Dataset & Paper

- 📄 **Research Paper**: [FLAME: Aerial Imagery Dataset for Wildfire Detection and Approaching Fire Front Monitoring](https://arxiv.org/abs/2012.03062)
- ⬇️ **Download Paper PDF**: [arXiv 2012.03062 PDF](https://arxiv.org/pdf/2012.03062.pdf)

### 4. 🤖 AI Core Framework Papers
- 📄 **YOLOv11 Documentation & Architecture**: [Ultralytics YOLOv11 Docs](https://docs.ultralytics.com/models/yolo11/)
- 📄 **XGBoost Paper**: [XGBoost: A Scalable Tree Boosting System (arXiv:1603.02754)](https://arxiv.org/abs/1603.02754)
- ⬇️ **Download XGBoost Paper PDF**: [arXiv 1603.02754 PDF](https://arxiv.org/pdf/1603.02754.pdf)

---

## 📄 Documentation

Check the `docs/` folder for detailed guides:
- [Architecture Guide](file:///d:/datasets_IDM(ADAS)/docs/architecture.md)
- [Database Schema](file:///d:/datasets_IDM(ADAS)/docs/database.md)
- [API Documentation](file:///d:/datasets_IDM(ADAS)/docs/api_docs.md)
- [Model Training Guide](file:///d:/datasets_IDM(ADAS)/docs/training_guide.md)

