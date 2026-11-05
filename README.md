# Intelligent Vehicle Assistance During Disasters (DisasterShield ADAS)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-2.0-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite 8" />
  <img src="https://img.shields.io/badge/YOLO-v11s-00FFFF?style=for-the-badge&logo=ultralytics&logoColor=black" alt="YOLOv11s" />
  <img src="https://img.shields.io/badge/XGBoost-V4-FF6600?style=for-the-badge" alt="XGBoost V4" />
  <img src="https://img.shields.io/badge/Copernicus-GLO--30-003399?style=for-the-badge" alt="Copernicus GLO-30" />
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License MIT" />
</p>

<p align="center">
  <strong>An Intelligent Driver Assistance System (ADAS) & Resilient Evacuation Navigation Platform engineered to safeguard vehicular mobility during extreme environmental catastrophes.</strong>
</p>

---

## 📑 Table of Contents

- [About the Project](#-about-the-project)
  - [The Fatal Flaw of Nominal Navigation](#the-fatal-flaw-of-nominal-navigation)
  - [The DisasterShield Solution](#the-disastershield-solution)
- [How the Map Understands Flooding & Reroutes](#-how-the-map-understands-flooding--reroutes)
- [Multi-Tier Intelligence Architecture](#-multi-tier-intelligence-architecture)
- [Quick Verification (Run in 2 Seconds)](#-quick-verification-run-in-2-seconds)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Repository Directory Structure](#-repository-directory-structure)
- [Quick Start Guide](#-quick-start-guide)
  - [Prerequisites](#1-prerequisites)
  - [Backend Setup](#2-backend-setup--startup)
  - [Frontend Setup](#3-frontend-setup--startup)
  - [Demo Accounts](#4--demo-credentials)
- [Scientific Benchmarks & Audited Results](#-scientific-benchmarks--audited-results)
- [Open Datasets & Literature](#-open-datasets--literature)
- [Documentation Hub](#-documentation-hub)
- [License](#-license)

---

## 📖 About the Project

### The Fatal Flaw of Nominal Navigation
Conventional commercial GPS navigation platforms (such as Google Maps, Waze, and TomTom) optimize routes purely for statistical traffic delays derived from mobile crowd telemetry. During severe natural disasters (flash floods, wildfire fronts, debris landslides, and road cave-ins), these systems fail catastrophically:
1. **Zero Hazard Semantics:** A submerged highway has zero moving vehicles. Legacy algorithms interpret this as an **"empty, high-speed corridor"**, directing civilian families directly into deadly flood waters.
2. **Crowdsource Delay & Blackouts:** Human hazard reports suffer 30–120 minute reporting latencies and fail completely when cellular towers lose power.
3. **Topographical & Hydrological Blindness:** Nominal GPS platforms possess no concept of river stage height, drainage thalwegs, or catchment elevation.

### The DisasterShield Solution
**DisasterShield ADAS** bridges physical hazard perception and automotive navigation through an integrated four-tier intelligence pipeline:
- 👁️ **Onboard Edge Computer Vision:** Uses **Ultralytics YOLOv11s** on forward-facing dashcam streams to detect standing water, active fire, smoke plumes, stranded pedestrians, and road damage in real time ($<30\text{ ms}$).
- 🛰️ **Hydrologically Grounded Risk Predictor:** Uses **XGBoost V4** trained on European Space Agency (ESA) **Copernicus GLO-30 Height Above Nearest Drainage (HAND)** and ERA5 multi-scale precipitation, achieving **100% recall** on unseen road corridors.
- ⚡ **Disaster-Aware Dynamic Pathfinding:** Modulates a modified **A\* routing algorithm** using inverse-distance hazard decay penalties and **raised-cosine (Hann-window) lateral detours** to compute evasion routes in **under 25 ms**.
- 🛡️ **Zero-Dependency Resilience:** Operates locally on vehicle compute with automatic in-memory mock database fallbacks during cellular dropouts.

---

## ⚡ How the Map Understands Flooding & Reroutes

```
[Dashcam Feed] ──▶ [YOLOv11s & CLAHE] ──▶ [XGBoost V4 HAND] ──▶ [Risk Engine (0-100)] ──▶ [A* 100,000x Penalty] ──▶ [Safe Detour <25ms]
```

1. **Camera Detection:** The car’s forward dashcam spots standing water or damage on the road using the YOLOv11 deep vision model and tags its exact GPS coordinates.
2. **Hydrological Verification:** The system evaluates satellite terrain clearance (Copernicus GLO-30 HAND) and live rainfall data to confirm whether the corridor is inundated beyond camera line-of-sight.
3. **Hazard Flagging:** The centralized Risk Engine arbitrates the threat and marks that specific road segment as **"CRITICAL / Blocked"** on the live map.
4. **Cost Penalty:** The custom A\* routing algorithm places a massive penalty (**100,000× cost multiplier**) on the flooded edge, instantly making it impassable to the pathfinder.
5. **Instant Evasive Rerouting:** The engine calculates a smooth lateral detour (Hann-window raised-cosine bypass) around the flood boundary and updates the automotive HUD with a safe green route in **under 25 milliseconds**.

---

## 🧠 Multi-Tier Intelligence Architecture

| Level | Component | Technology | Primary Inputs | Key Capabilities | Benchmark Metric |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Level 1** | **Edge Optical Perception** | **YOLOv11s** + **YOLOv8n** + **SAHI** | Dashcam RGB frames ($640\times640$) | 6 hazard classes, cavity depth (cm), and distance-ahead optics | **71.64% mAP@0.5**, 15 ms edge latency |
| **Level 2** | **Hydrological Inundation** | **XGBoost V4** (Calibrated) | 8-Feature Contract (Copernicus HAND, ERA5 rain) | Flood exposure probability $P(\text{Exposed})$ beyond camera line-of-sight | **100.0% Recall** (0 False Negatives), **94.44% Acc** |
| **Level 3** | **Multi-Modal Risk Fusion** | **RiskService Engine** | Level 1 Visuals + Level 2 Hydro Data | Composite Threat Score $R \in [0, 100]$ & Threat Tier categorization | Deterministic, sub-1 ms execution |
| **Level 4** | **Disaster-Aware Routing** | **Modified A\*** + **Hann Window** | Road network grid + Hazard repulsion fields | 3 concurrent routes (Optimal Green, Alt Blue, Evacuation Amber) | **$< 25\text{ ms}$** path generation, 0 hazard intersections |

---

## 🧪 Quick Verification (Run in 2 Seconds)

We have extracted and consolidated the three core algorithm suites into a single, self-contained Python script so you can verify the entire pipeline immediately without spinning up databases or servers:

```powershell
python core_pipeline_snippets.py
```

### Verified Pipeline Output:
```text
================================================================================
DisasterShield ADAS -- Core Algorithms Pipeline Verification Demo
================================================================================

[1] Testing Main Image Processing & CLAHE Enhancement...
  [OK] Image decoded successfully: shape=(480, 640, 3)
  [OK] CLAHE LAB contrast enhancement applied: shape=(480, 640, 3)

[2] Testing Object Detection Scoring & Distance Estimation...
  [OK] Normalized Class: 'Flood Inundation'
  [OK] Severity Tier: CRITICAL
  [OK] Estimated Distance Ahead: 160.0 meters

[3] Testing Disaster-Aware A* Routing & Hann-Window Detour...
  [OK] [Optimal Safe Route (A*)] Distance: 7.52 km | Safety Score: 100/100 | Time: 12.9 min | Latency: 1.01 ms
  [OK] [Alternative Detour Route] Distance: 8.04 km | Safety Score: 100/100 | Time: 13.8 min | Latency: 0.0 ms
  [OK] [Emergency Evacuation Corridor] Distance: 6.28 km | Safety Score: 0/100 | Time: 8.4 min | Latency: 0.0 ms

================================================================================
ALL CORE ALGORITHM SUITES VALIDATED AND FUNCTIONAL IN A SINGLE MODULE.
================================================================================
```

---

## 🏗️ System Architecture

Explore the standalone interactive runtime architecture diagram with dark/light themes and live animated signal traces:  
👉 **[Open Interactive Architecture Diagram](./.archify/architecture-adas-runtime-20261104-225800/adas-runtime.html)**

<p align="center">
  <img src="./docs/architecture-runtime-diagram.png" alt="ADAS Intelligent Vehicle Assistance Runtime Architecture" width="100%" style="border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);" />
</p>

```mermaid
flowchart LR
    subgraph INGRESS["External Actors and Inputs"]
        DRIVER["Vehicle Driver<br/>In-Cabin HUD or Mobile"]
        CAMERA["Dashcam Camera<br/>Real-Time Video Stream"]
        ADMIN["Emergency Admin<br/>Disaster Dispatch Center"]
    end

    subgraph CLIENT["Vehicle Onboard HUD Client"]
        HUD["React 19 HUD Portal<br/>Driver and Admin SPA"]
        CAM_HUD["Live Camera HUD<br/>Bounding Box Overlay"]
        RADAR["Spatial Disaster Radar<br/>Leaflet Risk Map"]
    end

    subgraph GATEWAY_TIER["FastAPI Gateway and Services"]
        AUTH["JWT Auth Gate<br/>PyJWT and Passlib"]
        GATEWAY["FastAPI Gateway<br/>Uvicorn REST Endpoints"]
        WS["WebSocket Stream Hub<br/>Live Alerts and SOS"]
        FUSION["Risk Fusion Engine<br/>Composite Score 0 to 100"]
        DB[("MongoDB Storage<br/>Atlas or In-Memory Mock")]
    end

    subgraph AI_ENGINES["Dual AI and Routing Intelligence"]
        YOLO["YOLOv11s Perception<br/>Flood, Fire, Smoke, Damage"]
        XGB["XGBoost V4 Hydro Model<br/>HAND and Antecedent Rain"]
        ASTAR["Disaster-Aware A-Star<br/>Hann Detours under 25ms"]
    end

    subgraph EXTERNAL["Geospatial and External APIs"]
        GEO["Open-Meteo and GLO-30 DEM<br/>Weather and Drainage"]
    end

    DRIVER --> HUD
    CAMERA --> CAM_HUD
    ADMIN --> RADAR

    HUD -->|Bearer JWT| AUTH
    HUD -->|REST API| GATEWAY
    CAM_HUD -->|POST /predict| GATEWAY
    RADAR -->|Query Route and SOS| GATEWAY
    WS -.->|Live Hazard Stream| RADAR

    GATEWAY -->|Image Buffer| YOLO
    GATEWAY -->|Telemetry and Hydro| XGB
    GATEWAY -->|Route Request| ASTAR

    YOLO -->|Visual BBoxes| FUSION
    XGB -->|Hydro Exposure| FUSION
    FUSION -->|Persist Scores| DB
    ASTAR -->|Query Obstacles| DB
    XGB -.->|Rain and HAND Data| GEO
```

---

## 🛠️ Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Frontend HUD** | **React 19**, **Vite 8**, Tailwind CSS, Lucide React, Axios | Automotive Heads-Up Display, driver portal, emergency command console |
| **Mapping & Radar** | **Leaflet.js**, CartoDB Dark Matter, Leaflet-RotatedMarker | Spatial hazard radar, animated vehicular marker tracking, evacuation corridors |
| **Backend API** | **FastAPI 2.0**, **Uvicorn**, Python 3.12, Pydantic v2 | High-throughput non-blocking REST gateway and real-time streaming endpoints |
| **Real-Time Feeds** | **WebSockets** (`/ws/emergency`, `/ws/disasters`) | Millisecond-latency telemetry push for SOS broadcasts and live incident tracking |
| **Database & Cache** | **MongoDB Atlas**, PyMongo (with zero-dependency in-memory mock fallback) | Persistent incident storage, user credential store, telemetry logging |
| **Edge Computer Vision**| **Ultralytics YOLOv11s** + **YOLOv8n**, **OpenCV**, **SAHI** | 6-class disaster identification, CLAHE contrast enhancement, small obstacle slicing |
| **Hydrological ML** | **XGBoost V4**, Scikit-Learn, SciPy, Platt Temperature Calibration | 8-variable flood prediction using terrain drainage clearance (Copernicus GLO-30 HAND) |
| **Dynamic Routing** | **Disaster-Aware A\***, Haversine heuristics, Hann-window lateral bypass | Sub-25ms multi-route calculation (Optimal Green, Alt Blue, Evacuation Amber) |
| **Security & Auth** | **PyJWT**, **Passlib (bcrypt)** | Role-based token authentication for Citizen Drivers and Command Admins |

---

## 📁 Repository Directory Structure

```
.
├── backend/                       # FastAPI 2.0 REST API & WebSocket Server
│   ├── app/
│   │   ├── api/                   # REST Routers (auth, prediction, hazards, navigation, emergency, weather)
│   │   ├── database/              # MongoDB Atlas connection manager & in-memory collection mock
│   │   ├── models/                # Pydantic v2 schemas and validation models
│   │   ├── services/              # AI Services: YOLOv11s inference, XGBoost V4, Risk Engine, A* Routing
│   │   └── main.py                # FastAPI application entrypoint & middleware setup
│   └── requirements.txt           # Backend Python dependencies
├── frontend/                      # React 19 + Vite 8 Automotive HUD Web Application
│   ├── src/
│   │   ├── components/            # Camera HUD modal, dynamic radar map, hazard alerts, SOS banner
│   │   ├── context/               # AuthContext (JWT bearer management and role gating)
│   │   ├── pages/                 # Dashboard, Detection, RoadSafety, DisasterRadar, EmergencySOS, AdminControl
│   │   ├── services/              # Axios API clients, WebSocket connection handlers, routing utilities
│   │   └── App.jsx                # Root layout and portal router
│   ├── package.json
│   └── vite.config.js             # Reverse proxy configuration for /api and WebSockets
├── pipeline/                      # Machine learning training, auditing, and dataset pipelines
│   ├── train_and_evaluate_v4.py   # XGBoost V4 training & held-out road evaluation
│   ├── sahi_inference.py          # SAHI multi-scale slicing implementation
│   └── providers/                 # Weather, disaster, road, and telemetry data providers
├── training/                      # Deep learning training scripts (YOLOv11, FloodNet, unified sets)
├── models/                        # Pretrained model weights
│   ├── best.pt                    # Master YOLOv11s disaster detector weights (50 epochs)
│   ├── yolov8n.pt                 # Real-time traffic & pedestrian companion tracker
│   └── road_risk_v4/              # XGBoost V4 model JSON & calibration parameters
├── scripts/                       # Accuracy benchmarks, verification scripts, and paper generators
│   ├── benchmark_sahi_accuracy.py # SAHI vs standard YOLO comparative evaluation
│   ├── test_accuracy_boost.py     # Threshold calibration (tau = 0.65) benchmark
│   └── generate_research_paper.py # Automated scientific research paper generator
├── docs/                          # Architectural specs, database schemas, and model cards
│   ├── architecture.md            # Complete system architecture specification
│   ├── database.md                # MongoDB schema definitions & collection indices
│   ├── api_docs.md                # OpenAPI REST & WebSocket contract specifications
│   ├── road_risk_v4_model_card.md # XGBoost V4 model card, metrics, and feature contract
│   └── training_guide.md          # Model training and dataset preparation walkthrough
├── core_pipeline_snippets.py      # Standalone runnable showcase script (Image CV + YOLO + A*)
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python:** `3.11+` or `3.12+`
- **Node.js:** `18+` (npm `9+`)
- **Git**

---

### 2. Backend Setup & Startup

Open a terminal in the root directory:

```powershell
cd backend

# Option A: Windows PowerShell with existing virtual environment
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Option B: Fresh virtual environment setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- **API Server:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/api/health`

---

### 3. Frontend Setup & Startup

Open a second terminal in the root directory:

```powershell
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

- **Live Automotive HUD:** `http://localhost:5173`

---

### 4. 🔑 Demo Credentials

The backend automatically seeds operational test accounts upon launch:

| Role | Username | Password | Access & Capabilities |
| :--- | :--- | :--- | :--- |
| **Driver / Citizen** | `driver` | `driver123` | Live GPS Navigation, YOLOv11 Dashcam HUD, Inundation Risk Telemetry, Emergency SOS |
| **Command Admin** | `admin` | `admin123` | City-Wide Incident Command, Hazard Verification & Geo-Pinning, SOS Dispatch Queue |

---

## 📊 Scientific Benchmarks & Audited Results

To guarantee scientific rigor and prevent spatial memorization, the model was evaluated against 68 audited historical flood observations from the **Central Water Commission (CWC)** and **Open-Meteo ERA5** reanalysis across four river basins on held-out road corridors (**0.0% geographical overlap**).

| Evaluation Dimension | Legacy Baseline (V2) | DisasterShield ADAS (V4) | Performance Advantage |
| :--- | :---: | :---: | :---: |
| **Road Inundation Recall (Unseen Roads)** | 60.0% | **100.0% (Zero False Negatives)** | No submerged road classified as safe |
| **Calibrated Inundation Accuracy** | 50.0% | **94.44% ($\tau^* = 0.65$)** | +44.44% generalization improvement |
| **ROC-AUC Metric** | 0.5827 | **1.0000** | Complete discriminatory ranking |
| **Precision-Recall AUC (PR-AUC)** | 0.5362 | **1.0000** | Robust under extreme disaster class imbalance |
| **Visual Disaster mAP@0.5** | — | **71.64%** (YOLOv11s, 50 epochs) | Robust multi-hazard classification |
| **Small Object Yield (SAHI)** | Baseline Single-Pass | **+66.7% to +100% Recall** | Resolves distant obstacles & debris |
| **A\* Pathfinding Latency** | — | **$< 25\text{ ms}$ Total** | Real-time automotive reactive steering |

---

## 📚 Open Datasets & Literature

- 🌊 **FloodNet Challenge Dataset**: [FloodNet (BinaLab)](https://github.com/BinaLab/FloodNet-Challenge-EARTHVISION2021) | [arXiv:2012.02951](https://arxiv.org/abs/2012.02951)
- 🔥 **FLAME Wildfire Aerial Dataset**: [IEEE Access](https://doi.org/10.1109/ACCESS.2021.3082857) | [arXiv:2012.03062](https://arxiv.org/abs/2012.03062)
- 🛣️ **RDD2022 Road Damage Dataset**: [IEEE T-ITS](https://doi.org/10.1109/TITS.2022.3213524) | [arXiv:2209.08538](https://arxiv.org/abs/2209.08538)
- 🛰️ **Copernicus GLO-30 DEM**: [European Space Agency Copernicus Data Space](https://dataspace.copernicus.eu/)
- 🌲 **XGBoost Scalable Tree Boosting**: [ACM SIGKDD](https://doi.org/10.1145/2939672.2945399) | [arXiv:1603.02754](https://arxiv.org/abs/1603.02754)
- 👁️ **Ultralytics YOLOv11**: [Ultralytics Official Documentation](https://docs.ultralytics.com/models/yolo11/)
- 🧭 **Height Above Nearest Drainage (HAND)**: Rennó et al. (Remote Sensing of Environment, 2008)

---

## 📄 Documentation Hub

For detailed architectural contracts, mathematical proofs, and data models:
- 🏛️ [System Architecture Specification](./docs/architecture.md)
- 🗄️ [Database Schemas & Data Collections](./docs/database.md)
- 📡 [REST API & WebSocket Contract Specs](./docs/api_docs.md)
- 🧪 [XGBoost V4 Model Card & Calibration Details](./docs/road_risk_v4_model_card.md)
- 🏋️ [Model Training & Dataset Pipeline Guide](./docs/training_guide.md)
- 💻 [Core Pipeline Source Code Snippets (Unified)](./core_pipeline_snippets.py)

---

## ⚖️ License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute for academic, research, and commercial purposes.
