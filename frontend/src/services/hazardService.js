/**
 * Hazard Management & Real-Time Alert Service
 * Consumes real backend hazards and WebSocket broadcasts.
 */
import api from './api';
import cacheService from './cacheService';

export const hazardService = {
  /**
   * Fetch all active disasters & hazards from database with in-memory caching
   */
  getActiveHazards: async (forceRefresh = false) => {
    // 1. Check in-memory cache first if not forced
    if (!forceRefresh) {
      const cached = cacheService.getCache('active_hazards');
      if (cached && Array.isArray(cached) && cached.length > 0) {
        return cached;
      }
    }

    try {
      const [disasters, hazards] = await Promise.all([
        api.getDisasters().catch(() => []),
        api.listHazards().catch(() => [])
      ]);

      const combined = [...disasters, ...hazards];
      const seen = new Set();
      const unique = [];

      for (const h of combined) {
        const id = String(h.id || h._id || `${h.lat}_${h.lng}`);
        if (!seen.has(id)) {
          seen.add(id);
          unique.push(h);
        }
      }

      // Normalize format & strictly filter for User / Driver active view
      const active = unique.map((h, idx) => {
        const lat = h.latitude !== undefined ? h.latitude : (h.location?.lat !== undefined ? h.location.lat : h.lat);
        const lng = h.longitude !== undefined ? h.longitude : (h.location?.lng !== undefined ? h.location.lng : h.lng);
        const source = (h.source || (h.created_by || h.createdBy === 'admin' ? 'ADMIN' : (h.reported_by || h.detectedBy === 'Driver Report' ? 'USER' : 'AI'))).toUpperCase();
        const status = (h.status || 'ACTIVE').toUpperCase();
        const isVerified = h.verified !== undefined ? Boolean(h.verified) : (status === 'ACTIVE' || status === 'VERIFIED');

        return {
          id: h._id || h.id || `hazard_${idx}`,
          source, // ADMIN, AI, or USER
          type: (h.disasterType || h.type || h.name || 'Hazard').toLowerCase(),
          name: h.disasterType || h.name || h.type || 'Hazard',
          latitude: lat,
          longitude: lng,
          lat,
          lng,
          severity: (h.severity || 'HIGH').toUpperCase(),
          confidence: h.confidence || (source === 'ADMIN' ? 1.0 : 0.92),
          address: h.address || h.location?.address || 'Corridor Sector',
          description: h.description || '',
          depth: h.depth || (String(h.disasterType || h.type).toLowerCase().includes('pothole') ? 0.08 : null),
          unit: 'm',
          distance: h.distance || null,
          status,
          verified: isVerified,
          start_time: h.start_time || h.createdAt || new Date().toISOString(),
          end_time: h.end_time || null,
          created_by: h.created_by || h.reported_by || (source === 'ADMIN' ? 'Admin' : 'System'),
          timestamp: h.createdAt || h.created_at || new Date().toISOString()
        };
      }).filter((h) => {
        if (!h.latitude || !h.longitude) return false;
        const st = (h.status || 'ACTIVE').toUpperCase();
        // NEVER show rejected hazards in user / driver panel
        if (st === 'REJECTED' || st === 'INACTIVE' || st === 'RESOLVED') return false;
        // NEVER show unverified or rejected hazards
        if (h.verified === false) return false;
        // Only show accepted, verified, active hazards
        return st === 'ACTIVE' || st === 'VERIFIED' || st === 'APPROVED';
      });

      // Save into in-memory cache with 25-second TTL
      cacheService.setCache('active_hazards', active, 25);
      return active;
    } catch (err) {
      console.warn('Failed to fetch hazards:', err);
      // Fallback to expired cache if network is down
      const stale = cacheService.getCache('active_hazards');
      return stale || [];
    }
  },

  /**
   * Submit driver-reported hazard
   */
  reportHazard: async ({ type, latitude, longitude, severity = 'High', description = '', image_base64 = null, address = '' }) => {
    cacheService.invalidateCache('active_hazards');
    return api.reportHazard({
      disasterType: type,
      lat: latitude,
      lng: longitude,
      severity,
      description,
      address,
      image_base64
    });
  },

  /**
   * Listen to Real-time WebSocket disaster updates
   */
  connectHazardWebSocket: (onMessageCallback) => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/disasters';
    let ws = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessageCallback(data);
        } catch {
          // ignore parse errors
        }
      };
      ws.onerror = () => {
        console.warn('Disaster WebSocket not available, relying on REST polling.');
      };
    } catch {
      // ignore
    }
    return () => {
      if (ws) ws.close();
    };
  }
};

export default hazardService;
