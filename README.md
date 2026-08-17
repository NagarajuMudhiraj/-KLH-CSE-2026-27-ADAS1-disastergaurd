# Intelligent Vehicle Assistance During Disasters

An AI-powered web application designed to assist drivers and emergency teams during natural disasters by detecting road hazards from images using **YOLOv11**, predicting road safety status based on weather and traffic metrics using **XGBoost**, providing interactive disaster maps using **Leaflet**, and managing real-time emergency SOS alerts.

---

## 📌 Features

- 🔐 **User Authentication**: Secure JWT-based auth with password hashing (bcrypt) supporting Driver and Admin roles.
- 🖼️ **AI Disaster Detection**: Upload road/disaster images to detect **Flood**, **Fire**, **Landslide**, and **Road Damage** with visual bounding boxes and confidence scores using **YOLOv11**.
- 🛣️ **Road Safety Prediction**: Real-time road safety classification (**Safe**, **Risky**, **Blocked**) based on rainfall, traffic level, and water depth using **XGBoost**.
- 🗺️ **Interactive Disaster Map**: Leaflet map displaying real-time disaster locations, driver GPS coordinates, safe emergency routes, and nearest relief nodes (Hospitals, Police, Shelters).
- 🚨 **Emergency SOS System**: One-click SOS alert sending GPS coordinates and hazard details to MongoDB and the Admin Emergency Dashboard.
- 📊 **Dashboard & Analytics**: Chart.js data visualizations for disaster statistics, safety distributions, and live incident feeds.
- 🕒 **Prediction History**: Complete queryable audit trail of past predictions with filtering capability.
- ⚙️ **Admin Control Panel**: Centralized management view for registered drivers, pending SOS requests, and disaster logs.

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: React (Vite)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Mapping**: Leaflet & React-Leaflet
- **Charts**: Chart.js & React-ChartJS-2
- **State & HTTP**: React Context API & Axios

### Backend
- **Language**: Python 3.12
- **Web Framework**: FastAPI & Uvicorn
- **Data Validation**: Pydantic v2
- **Database**: MongoDB Atlas / PyMongo
- **Auth**: JWT (PyJWT / Passlib bcrypt)

### AI & Machine Learning
- **Computer Vision**: Ultralytics YOLOv11 & OpenCV
- **Safety Classifier**: XGBoost Classifier
- **Data Analysis**: Pandas, NumPy, Scikit-Learn

---

## 📁 Project Structure

```
.
├── frontend/             # Vite + React + Tailwind CSS Web Application
│   ├── src/
│   │   ├── components/   # Navbar, Footer, Reusable UI widgets
│   │   ├── pages/        # Dashboard, Detection, Map, SOS, Admin, Auth
│   │   ├── context/      # AuthContext
│   │   ├── services/     # Axios API service
│   │   └── App.jsx
│   └── package.json
├── backend/              # Python FastAPI Server
│   ├── app/
│   │   ├── api/          # Auth, Detections, Road Safety, SOS, Dashboard
│   │   ├── database/     # MongoDB Connection & Mock Storage Fallback
│   │   ├── services/     # YOLOv11 & XGBoost Model Inference Engines
│   │   ├── utils/        # JWT & Password Hashing Utilities
│   │   └── main.py       # FastAPI Entry Point
│   └── requirements.txt
├── datasets/             # Directory for RDD2022, FloodNet, FLAME datasets
├── models/               # Model weights (best.pt, road_model.pkl)
├── training/             # YOLOv11 & XGBoost training scripts
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

# Create virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create initial AI model files (runs automatically if models are missing)
python ../models/generate_initial_models.py

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend server will start at: `http://localhost:8000`
Swagger API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup & Run

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend application will start at: `http://localhost:5173`

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

