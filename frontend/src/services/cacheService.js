/**
 * DisasterShield ADAS Cache & Memory Engine
 * Provides persistent memory and ultra-fast in-memory caching for:
 * 1. User & Driver: Recent Destinations, Route History, Telemetry Logs, Voice Preferences
 * 2. Admin: Incident History, Pinned Hazards Audit, SOS Rescue Dispatch Memory
 * 3. High-Performance In-Memory Cache with TTL for Hazards & Telemetry
 */

const MEMORY_KEYS = {
  RECENT_DESTINATIONS: 'adas_memory_recent_destinations',
  TRIP_HISTORY: 'adas_memory_trip_history',
  HAZARDS_CACHE: 'adas_cache_hazards',
  ADMIN_INCIDENT_LOG: 'adas_memory_admin_incidents',
  DRIVER_PREFERENCES: 'adas_memory_driver_prefs'
};

// In-Memory volatile cache store for sub-millisecond lookups
const inMemoryStore = new Map();

export const cacheService = {
  // ==========================================
  // 1. GENERIC IN-MEMORY CACHE WITH TTL
  // ==========================================
  setCache: (key, data, ttlSeconds = 60) => {
    const expiresAt = Date.now() + (ttlSeconds * 1000);
    const entry = { data, expiresAt };
    inMemoryStore.set(key, entry);
    try {
      localStorage.setItem(`adas_cache_${key}`, JSON.stringify(entry));
    } catch {
      // localStorage fallback if full
    }
  },

  getCache: (key) => {
    // Check in-memory store first
    if (inMemoryStore.has(key)) {
      const entry = inMemoryStore.get(key);
      if (entry.expiresAt > Date.now()) {
        return entry.data;
      }
      inMemoryStore.delete(key);
    }

    // Check localStorage fallback
    try {
      const saved = localStorage.getItem(`adas_cache_${key}`);
      if (saved) {
        const entry = JSON.parse(saved);
        if (entry.expiresAt > Date.now()) {
          inMemoryStore.set(key, entry);
          return entry.data;
        }
        localStorage.removeItem(`adas_cache_${key}`);
      }
    } catch {
      // Ignore parse errors
    }
    return null;
  },

  invalidateCache: (key) => {
    inMemoryStore.delete(key);
    try {
      localStorage.removeItem(`adas_cache_${key}`);
    } catch {
      // Ignore
    }
  },

  // ==========================================
  // 2. USER / DRIVER DESTINATION MEMORY
  // ==========================================
  getRecentDestinations: () => {
    try {
      const saved = localStorage.getItem(MEMORY_KEYS.RECENT_DESTINATIONS);
      return saved ? JSON.parse(saved) : [
        { name: 'KIMS Emergency Hospital', full_address: 'KIMS Hospital, Hubballi', lat: 15.3647, lng: 75.1240, timestamp: Date.now() - 3600000 },
        { name: 'Central Bus Station Junction', full_address: 'CBT Hubballi Karnataka', lat: 15.3524, lng: 75.1388, timestamp: Date.now() - 7200000 },
        { name: 'Airport Road Bypass', full_address: 'Gokul Road, Hubballi Airport', lat: 15.3617, lng: 75.0849, timestamp: Date.now() - 14400000 }
      ];
    } catch {
      return [];
    }
  },

  saveDestinationToMemory: (destination) => {
    if (!destination || !destination.name) return;
    try {
      const existing = cacheService.getRecentDestinations();
      // Remove duplicate if it already exists
      const filtered = existing.filter(d => d.name.toLowerCase() !== destination.name.toLowerCase());
      const updated = [
        {
          name: destination.name,
          full_address: destination.full_address || destination.name,
          lat: destination.lat,
          lng: destination.lng,
          timestamp: Date.now()
        },
        ...filtered
      ].slice(0, 8); // Keep last 8 destinations in memory

      localStorage.setItem(MEMORY_KEYS.RECENT_DESTINATIONS, JSON.stringify(updated));
      return updated;
    } catch (e) {
      console.warn("Could not save destination to memory:", e);
      return [];
    }
  },

  clearDestinationMemory: () => {
    localStorage.removeItem(MEMORY_KEYS.RECENT_DESTINATIONS);
  },

  // ==========================================
  // 3. TRIP & DRIVE TELEMETRY MEMORY
  // ==========================================
  getTripHistory: () => {
    try {
      const saved = localStorage.getItem(MEMORY_KEYS.TRIP_HISTORY);
      return saved ? JSON.parse(saved) : [
        {
          id: 'TRIP-101',
          destination: 'KIMS Emergency Hospital',
          distanceKm: 5.4,
          durationMin: 14,
          hazardsAvoided: 2,
          date: new Date(Date.now() - 86400000).toLocaleDateString(),
          safetyRating: 'A+ (Safe Detour)'
        },
        {
          id: 'TRIP-102',
          destination: 'Airport Road Bypass',
          distanceKm: 8.2,
          durationMin: 19,
          hazardsAvoided: 1,
          date: new Date(Date.now() - 172800000).toLocaleDateString(),
          safetyRating: 'A (Optimal Path)'
        }
      ];
    } catch {
      return [];
    }
  },

  saveTripToMemory: (tripRecord) => {
    try {
      const existing = cacheService.getTripHistory();
      const newRecord = {
        id: `TRIP-${Date.now().toString().slice(-4)}`,
        date: new Date().toLocaleDateString(),
        timestamp: Date.now(),
        ...tripRecord
      };
      const updated = [newRecord, ...existing].slice(0, 15);
      localStorage.setItem(MEMORY_KEYS.TRIP_HISTORY, JSON.stringify(updated));
      return updated;
    } catch (e) {
      console.warn("Could not record trip memory:", e);
      return [];
    }
  },

  // ==========================================
  // 4. ADMIN INCIDENT & DISASTER MEMORY LOG
  // ==========================================
  getAdminIncidentLog: () => {
    try {
      const saved = localStorage.getItem(MEMORY_KEYS.ADMIN_INCIDENT_LOG);
      return saved ? JSON.parse(saved) : [
        {
          id: 'INC-8801',
          type: 'Flood Water Inundation',
          location: 'Old Hubli Bypass Underpass',
          severity: 'CRITICAL',
          timestamp: new Date(Date.now() - 7200000).toLocaleTimeString(),
          status: 'ACTIVE_WARNING',
          unitsDispatched: 2
        },
        {
          id: 'INC-8802',
          type: 'Road Surface Damage / Deep Pothole',
          location: 'Airport Cross Road Sector 4',
          severity: 'MODERATE',
          timestamp: new Date(Date.now() - 18000000).toLocaleTimeString(),
          status: 'REROUTED',
          unitsDispatched: 1
        },
        {
          id: 'INC-8803',
          type: 'Severe Waterlogging',
          location: 'Unkal Lake Overpass',
          severity: 'HIGH',
          timestamp: new Date(Date.now() - 86400000).toLocaleTimeString(),
          status: 'RESOLVED',
          unitsDispatched: 3
        }
      ];
    } catch {
      return [];
    }
  },

  logAdminIncident: (incident) => {
    try {
      const existing = cacheService.getAdminIncidentLog();
      const entry = {
        id: `INC-${Math.floor(1000 + Math.random() * 9000)}`,
        timestamp: new Date().toLocaleTimeString(),
        status: 'LOGGED_IN_MEMORY',
        ...incident
      };
      const updated = [entry, ...existing].slice(0, 25);
      localStorage.setItem(MEMORY_KEYS.ADMIN_INCIDENT_LOG, JSON.stringify(updated));
      return updated;
    } catch (e) {
      console.warn("Could not log admin incident memory:", e);
      return [];
    }
  }
};

export default cacheService;
