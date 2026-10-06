import axios from 'axios';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token if expired or invalid
      // localStorage.removeItem('token');
      // localStorage.removeItem('user');
    }
    return Promise.reject(error);
  }
);

export const api = {
  // --- Auth APIs ---
  login: async (username, password) => {
    const res = await apiClient.post('/auth/login', { username, password });
    return res.data;
  },
  register: async (userData) => {
    const res = await apiClient.post('/auth/register', userData);
    return res.data;
  },
  getProfile: async () => {
    const res = await apiClient.get('/auth/profile');
    return res.data;
  },
  updateProfile: async (profileData) => {
    const res = await apiClient.put('/auth/profile', profileData);
    return res.data;
  },

  // --- Dashboard & Analytics ---
  getDashboardData: async () => {
    const res = await apiClient.get('/dashboard');
    return res.data;
  },
  getHistory: async (params = {}) => {
    const res = await apiClient.get('/history', { params });
    return res.data;
  },
  getDisasters: async () => {
    const res = await apiClient.get('/disasters');
    return res.data;
  },
  getSpatialNodes: async (lat, lng, radius_m = 12000) => {
    const res = await apiClient.get('/spatial-nodes', {
      params: { lat, lng, radius_m }
    });
    return res.data;
  },

  // --- AI Hazard Detection (YOLOv11) ---
  predictImage: async (formData) => {
    const res = await apiClient.post('/predict-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  // --- Road Safety Prediction (XGBoost) ---
  predictRoad: async (rainfall, traffic, waterLevel) => {
    const res = await apiClient.post('/predict-road', {
      rainfall: parseFloat(rainfall),
      traffic: parseFloat(traffic),
      waterLevel: parseFloat(waterLevel)
    });
    return res.data;
  },
  calculateRisk: async (data) => {
    const res = await apiClient.post('/risk/calculate', data);
    return res.data;
  },

  // --- Dijkstra & A* Navigation ---
  getDisasterZones: async (lat, lng) => {
    const res = await apiClient.get('/navigation/disaster-zones', {
      params: lat !== undefined && lng !== undefined ? { lat, lng } : {}
    });
    return res.data;
  },
  createDisasterZone: async (zoneData) => {
    const res = await apiClient.post('/navigation/disaster-zones', zoneData);
    return res.data;
  },
  planDijkstraRoute: async (origin_lat, origin_lng, destination_lat, destination_lng, avoid_critical = true, temp_hazard = null) => {
    const res = await apiClient.post('/navigation/route', {
      origin_lat,
      origin_lng,
      destination_lat,
      destination_lng,
      avoid_critical,
      temp_hazard
    });
    return res.data;
  },
  analyzeAStarRoute: async (routeData) => {
    const res = await apiClient.post('/routes/analyze', routeData);
    return res.data;
  },

  // --- Emergency SOS Operations ---
  sendEmergencySOS: async (sosData) => {
    const res = await apiClient.post('/emergency', sosData);
    return res.data;
  },
  getEmergencyList: async () => {
    const res = await apiClient.get('/emergency/list');
    return res.data;
  },
  updateSOSStatus: async (sos_id, status) => {
    const res = await apiClient.patch('/emergency/status', { sos_id, status });
    return res.data;
  },
  assignRescueTeam: async (data) => {
    const res = await apiClient.post('/emergency/assign', data);
    return res.data;
  },
  dispatchService: async (sos_id, service_type) => {
    const res = await apiClient.post('/emergency/dispatch', { sos_id, service_type });
    return res.data;
  },
  notifyEmergencyContacts: async (sos_id, contacts) => {
    const res = await apiClient.post('/emergency/notify-contacts', { sos_id, contacts });
    return res.data;
  },
  updateLocationTelemetry: async (telemetry) => {
    const res = await apiClient.post('/emergency/location-update', telemetry);
    return res.data;
  },
  createManualIncident: async (incidentData) => {
    const res = await apiClient.post('/emergency/manual-create', incidentData);
    return res.data;
  },
  deleteEmergencySOS: async (sos_id) => {
    const res = await apiClient.delete(`/emergency/${sos_id}`);
    return res.data;
  },

  // --- Hazard Lifecycle & Restricted Zones ---
  reportAIDetectedHazard: async (hazardData) => {
    const res = await apiClient.post('/hazards/detected', hazardData);
    return res.data;
  },
  reportHazard: async (hazardData) => {
    const res = await apiClient.post('/hazards/report', hazardData);
    return res.data;
  },
  getActiveHazards: async () => {
    const res = await apiClient.get('/hazards/active');
    return res.data;
  },
  getNearbyHazards: async (lat, lng, radius_km = 5.0) => {
    const res = await apiClient.get('/hazards/nearby', { params: { lat, lng, radius_km } });
    return res.data;
  },
  getRouteHazardImpact: async (params) => {
    const res = await apiClient.get('/hazards/route-impact', { params });
    return res.data;
  },
  getAdminReports: async () => {
    const res = await apiClient.get('/hazards/admin/reports');
    return res.data;
  },
  listHazards: async () => {
    const res = await apiClient.get('/hazards/list');
    return res.data;
  },
  verifyHazard: async (hazard_id, action, admin_note = '') => {
    const res = await apiClient.post('/hazards/verify', {
      hazard_id,
      action,
      admin_note
    });
    return res.data;
  },
  updateHazardSeverity: async (hazard_id, severity) => {
    const res = await apiClient.patch('/hazards/severity', { hazard_id, severity });
    return res.data;
  },
  resolveHazard: async (hazard_id) => {
    const res = await apiClient.put(`/hazards/resolve/${hazard_id}`);
    return res.data;
  },
  createAdminHazard: async (hazardData) => {
    const res = await apiClient.post('/hazards/admin/create', hazardData);
    return res.data;
  },
  editAdminHazard: async (hazard_id, hazardData) => {
    const res = await apiClient.put(`/hazards/admin/${hazard_id}`, hazardData);
    return res.data;
  },
  updateAdminHazardStatus: async (hazard_id, status) => {
    const res = await apiClient.patch(`/hazards/admin/${hazard_id}/status`, { status }, {
      params: { status }
    });
    return res.data;
  },
  deleteAdminHazard: async (hazard_id) => {
    const res = await apiClient.delete(`/hazards/admin/${hazard_id}`);
    return res.data;
  },
  listRestrictedZones: async () => {
    const res = await apiClient.get('/hazards/restricted-zones');
    return res.data;
  },
  createRestrictedZone: async (zoneData) => {
    const res = await apiClient.post('/hazards/restricted-zones', zoneData);
    return res.data;
  },
  deleteRestrictedZone: async (zone_id) => {
    const res = await apiClient.delete(`/hazards/restricted-zones/${zone_id}`);
    return res.data;
  },

  // --- Weather Telemetry ---
  getLiveWeather: async (lat, lng) => {
    const res = await apiClient.get('/weather', { params: { lat, lng } });
    return res.data;
  },

  // --- Admin Operations & Telemetry ---
  getLiveDrivers: async () => {
    const res = await apiClient.get('/admin/drivers');
    return res.data;
  },
  sendBroadcastAlert: async (alertData) => {
    const res = await apiClient.post('/admin/broadcast', alertData);
    return res.data;
  },
  listBroadcasts: async () => {
    const res = await apiClient.get('/admin/broadcast/list');
    return res.data;
  },
  getAIMonitoring: async () => {
    const res = await apiClient.get('/admin/ai-monitoring');
    return res.data;
  },
  flagFalsePositive: async (log_id, reason) => {
    const res = await apiClient.post('/admin/ai-monitoring/false-positive', { log_id, reason });
    return res.data;
  },
  getSystemHealth: async () => {
    const res = await apiClient.get('/admin/system-health');
    return res.data;
  },
  getAnalytics: async () => {
    const res = await apiClient.get('/admin/analytics');
    return res.data;
  },

  // --- User Panel Services ---
  estimatePotholeDepth: async (data = {}) => {
    const res = await apiClient.post('/pothole/estimate-depth', data);
    return res.data;
  },
  getRouteHistory: async () => {
    const res = await apiClient.get('/routes/history');
    return res.data;
  },
  saveRouteHistory: async (routeData) => {
    const res = await apiClient.post('/routes/history', routeData);
    return res.data;
  },
  getAlertHistory: async () => {
    const res = await apiClient.get('/alerts/history');
    return res.data;
  }
};


export default api;
