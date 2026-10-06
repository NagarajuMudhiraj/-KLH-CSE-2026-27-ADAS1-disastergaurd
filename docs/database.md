# Database Design & Schemas

The application uses **MongoDB** (Atlas or local instance) via **PyMongo**.

Below are the detailed document structures for each collection.

---

## 1. `users` Collection

Stores account information and authentication credentials.

```json
{
  "_id": "ObjectId('65d8a01b2f3e4a001c890123')",
  "username": "driver_john",
  "email": "john@example.com",
  "password": "$2b$12$e8vE7...hashed_bcrypt_string...",
  "role": "driver", // "driver" or "admin"
  "createdAt": "2026-08-06T12:00:00Z"
}
```

---

## 2. `vehicles` Collection

Tracks vehicle metadata associated with drivers.

```json
{
  "_id": "ObjectId('65d8a01b2f3e4a001c890124')",
  "vehicleNumber": "KA-01-AB-1234",
  "owner": "driver_john",
  "vehicleType": "SUV",
  "location": {
    "lat": 12.9716,
    "lng": 77.5946
  },
  "updatedAt": "2026-08-06T12:00:00Z"
}
```

---

## 3. `predictions` Collection

Log of all AI predictions (both YOLOv11 image detections and XGBoost road safety analyses).

```json
{
  "_id": "ObjectId('65d8a01b2f3e4a001c890125')",
  "username": "driver_john",
  "type": "image", // "image" or "road"
  "prediction": "Flood", // "Flood", "Fire", "Landslide", "Road Damage", or "Safe", "Risky", "Blocked"
  "confidence": 0.94,
  "details": {
    "rainfall": 45.0,
    "traffic": 8.0,
    "waterLevel": 35.0
  },
  "imageUrl": "/static/uploads/annotated_123.jpg",
  "createdAt": "2026-08-06T12:05:00Z"
}
```

---

## 4. `disasters` Collection

Active spatial disaster reports rendered on the interactive Leaflet map.

```json
{
  "_id": "ObjectId('65d8a01b2f3e4a001c890126')",
  "disasterType": "Flood",
  "location": {
    "lat": 12.9720,
    "lng": 77.5950,
    "address": "MG Road Underpass, Bengaluru"
  },
  "severity": "High", // "Low", "Medium", "High", "Critical"
  "image": "/static/uploads/disaster_456.jpg",
  "detectedBy": "driver_john",
  "createdAt": "2026-08-06T12:05:00Z"
}
```

---

## 5. `emergency_requests` Collection

Emergency SOS notifications triggered by drivers in distress.

```json
{
  "_id": "ObjectId('65d8a01b2f3e4a001c890127')",
  "username": "driver_john",
  "location": {
    "lat": 12.9716,
    "lng": 77.5946,
    "address": "Near Trinity Metro Station"
  },
  "disasterType": "Flood",
  "status": "Pending", // "Pending", "Dispatched", "Resolved"
  "timestamp": "2026-08-06T12:10:00Z"
}
```
