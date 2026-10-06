# REST API Documentation

Base URL: `http://localhost:8000/api`

---

## 🔑 Authentication Endpoints

### 1. Register User
- **URL**: `POST /auth/register`
- **Request Body**:
```json
{
  "username": "driver_john",
  "email": "john@example.com",
  "password": "securepassword123",
  "role": "driver"
}
```
- **Response** (200 OK):
```json
{
  "message": "User registered successfully",
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "username": "driver_john",
    "email": "john@example.com",
    "role": "driver"
  }
}
```

### 2. Login User
- **URL**: `POST /auth/login`
- **Request Body**:
```json
{
  "username": "driver_john",
  "password": "securepassword123"
}
```
- **Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "username": "driver_john",
    "email": "john@example.com",
    "role": "driver"
  }
}
```

### 3. Get User Profile
- **URL**: `GET /auth/profile`
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK):
```json
{
  "username": "driver_john",
  "email": "john@example.com",
  "role": "driver"
}
```

---

## 🤖 AI Prediction Endpoints

### 4. Image Disaster Detection (YOLOv11)
- **URL**: `POST /predict-image`
- **Headers**: `Authorization: Bearer <token>`
- **Body**: `multipart/form-data` with key `file` (image file)
- **Response** (200 OK):
```json
{
  "prediction": "Flood Inundation",
  "confidence": 0.94,
  "detections": [
    {
      "class_name": "Flood Inundation",
      "confidence": 0.94,
      "bbox": [100, 150, 400, 350]
    }
  ],
  "annotated_image_url": "data:image/jpeg;base64,..."
}
```

### 5. Road Safety Prediction (XGBoost)
- **URL**: `POST /predict-road`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
```json
{
  "rainfall": 65.5,
  "traffic": 8.0,
  "waterLevel": 40.0
}
```
- **Response** (200 OK):
```json
{
  "prediction": "Blocked",
  "confidence": 0.96,
  "riskScore": 89.65,
  "recommendation": "DANGER: Extreme road inundation or hazard. Route is impassable. Please take designated safe detours immediately!",
  "createdAt": "2026-08-16T15:45:00.000Z"
}
```

---

## 🚨 Emergency, Spatial & Dashboard Endpoints

### 6. Trigger Emergency SOS
- **URL**: `POST /emergency`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
```json
{
  "disasterType": "Flood",
  "lat": 12.9716,
  "lng": 77.5946,
  "address": "MG Road, Bengaluru"
}
```

### 7. Get Emergency Requests List
- **URL**: `GET /emergency/list`
- **Headers**: `Authorization: Bearer <token>`

### 8. Get Dashboard Summary
- **URL**: `GET /dashboard`
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK):
```json
{
  "totalPredictions": 48,
  "totalDisasters": 12,
  "activeEmergencies": 3,
  "registeredUsers": 25,
  "roadStatusCounts": { "Safe": 18, "Risky": 20, "Blocked": 10 },
  "disasterTypeCounts": {
    "Flood": 6,
    "Fire": 3,
    "Smoke": 1,
    "Landslide": 2,
    "Road Damage": 5,
    "Person in Distress": 4,
    "Stranded Vehicle": 7
  },
  "recentEmergencies": []
}
```

### 9. Get Disasters for Map
- **URL**: `GET /disasters`

### 10. Get Prediction History
- **URL**: `GET /history?user_filter=driver_john&disaster_type=Flood`
- **Headers**: `Authorization: Bearer <token>`

### 11. Get Live Weather for Coordinates
- **URL**: `GET /weather?lat=12.9716&lng=77.5946`

### 12. Get Nearby Spatial Emergency Nodes (Hospitals, Police, Shelters)
- **URL**: `GET /spatial-nodes?lat=12.9716&lng=77.5946&radius_m=8000`
