import { useState, useEffect, useCallback, useRef } from 'react';

export const useLocation = () => {
  const [currentLocation, setCurrentLocation] = useState(null);
  const [error, setError] = useState(null);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [isLocating, setIsLocating] = useState(true);
  const watchIdRef = useRef(null);

  const requestLocation = useCallback(() => {
    setIsLocating(true);
    setError(null);
    setPermissionDenied(false);

    if (!('geolocation' in navigator)) {
      setError('Location access is required for navigation.\nPlease enable location permission.');
      setPermissionDenied(true);
      setIsLocating(false);
      return;
    }

    const handleSuccess = (pos) => {
      const coords = {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        accuracy: pos.coords.accuracy,
        heading: pos.coords.heading,
        speed: pos.coords.speed ? Math.round(pos.coords.speed * 3.6) : 0, // convert m/s to km/h
        timestamp: pos.timestamp || Date.now(),
        name: 'Current Location'
      };

      setCurrentLocation(coords);
      setError(null);
      setPermissionDenied(false);
      setIsLocating(false);
    };

    const handleError = (err) => {
      // Error code 1 is PERMISSION_DENIED
      console.warn('GPS Geolocation error code:', err.code, err.message);
      setError('Location access is required for navigation.\nPlease enable location permission.');
      setPermissionDenied(true);
      setCurrentLocation(null); // Never fall back to fake or hardcoded location
      setIsLocating(false);
    };

    // 1. Initial position query
    navigator.geolocation.getCurrentPosition(handleSuccess, handleError, {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0
    });

    // 2. Real-time GPS stream
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
    }

    watchIdRef.current = navigator.geolocation.watchPosition(
      handleSuccess,
      handleError,
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 2000
      }
    );
  }, []);

  useEffect(() => {
    requestLocation();

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
    };
  }, [requestLocation]);

  return {
    currentLocation,
    error,
    permissionDenied,
    isLocating,
    requestLocation
  };
};

export default useLocation;
