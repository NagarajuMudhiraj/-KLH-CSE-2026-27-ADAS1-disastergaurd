import { useState, useEffect, useCallback } from 'react';
import hazardService from '../services/hazardService';
import cacheService from '../services/cacheService';

export const useHazards = () => {
  const [hazards, setHazards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeAlert, setActiveAlert] = useState(null);

  const fetchHazards = useCallback(async () => {
    try {
      const list = await hazardService.getActiveHazards(true);
      setHazards(list);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHazards();

    // Setup WebSocket live hazard stream
    const unsubscribe = hazardService.connectHazardWebSocket((event) => {
      if (!event) return;

      // When admin rejects a hazard: IMMEDIATELY remove from user view & clear active alert
      if (event.event === 'HAZARD_REJECTED') {
        cacheService.invalidateCache('active_hazards');
        const targetId = String(event.data?.id || event.data?._id || '');
        setHazards((prev) => prev.filter((h) => String(h.id || h._id) !== targetId));
        setActiveAlert((prev) => (prev && String(prev.id) === targetId ? null : prev));
        fetchHazards();
        return;
      }

      // When admin deletes a hazard: IMMEDIATELY remove from user view
      if (event.event === 'HAZARD_DELETED') {
        cacheService.invalidateCache('active_hazards');
        const targetId = String(event.data?.id || event.data?._id || '');
        setHazards((prev) => prev.filter((h) => String(h.id || h._id) !== targetId));
        setActiveAlert((prev) => (prev && String(prev.id) === targetId ? null : prev));
        fetchHazards();
        return;
      }

      // When status is changed to INACTIVE / REJECTED / RESOLVED: remove immediately
      if (event.event === 'HAZARD_STATUS_UPDATED') {
        cacheService.invalidateCache('active_hazards');
        const st = String(event.data?.status || '').toUpperCase();
        if (st === 'REJECTED' || st === 'INACTIVE' || st === 'RESOLVED') {
          const targetId = String(event.data?.id || event.data?._id || '');
          setHazards((prev) => prev.filter((h) => String(h.id || h._id) !== targetId));
          setActiveAlert((prev) => (prev && String(prev.id) === targetId ? null : prev));
        }
        fetchHazards();
        return;
      }

      // When admin approves/verifies a hazard: refresh so it appears for navigation
      if (event.event === 'HAZARD_VERIFIED') {
        cacheService.invalidateCache('active_hazards');
        fetchHazards();
        return;
      }

      // When a new approved disaster/hazard is reported or detected:
      if (event.event === 'NEW_DISASTER_DETECTED' || event.event === 'HAZARD_REPORTED') {
        cacheService.invalidateCache('active_hazards');
        fetchHazards();
        if (event.data && event.data.status !== 'REJECTED' && event.data.status !== 'INACTIVE') {
          setActiveAlert({
            id: event.data.id || 'alert_live',
            type: event.data.disasterType || event.data.name || 'Hazard Detected',
            latitude: event.data.lat || event.data.latitude,
            longitude: event.data.lng || event.data.longitude,
            severity: event.data.severity || 'Critical',
            recommendation: event.data.recommendation || 'Proceed via automated detour bypass',
            timestamp: new Date().toISOString()
          });
        }
      }
    });

    return () => {
      unsubscribe();
    };
  }, [fetchHazards]);

  return {
    hazards,
    loading,
    activeAlert,
    setActiveAlert,
    refreshHazards: fetchHazards
  };
};

export default useHazards;
