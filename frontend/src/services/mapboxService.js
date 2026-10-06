/**
 * Mapbox GL JS, Geocoding v6, and Directions v5 Service Abstraction
 * Production-ready ADAS mapping provider with mapbox/driving-traffic profile.
 */
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '';

if (MAPBOX_TOKEN && MAPBOX_TOKEN !== 'your_mapbox_access_token_here') {
  mapboxgl.accessToken = MAPBOX_TOKEN;
}

export const mapboxService = {
  isConfigured: () => Boolean(MAPBOX_TOKEN && MAPBOX_TOKEN.trim() !== '' && MAPBOX_TOKEN !== 'your_mapbox_access_token_here'),

  getToken: () => MAPBOX_TOKEN,

  /**
   * Initializes Mapbox GL map instance centered on current GPS coordinates
   */
  initializeMap: (container, { center = [80.245, 13.035], zoom = 14, style = 'mapbox://styles/mapbox/navigation-day-v1' } = {}) => {
    if (!mapboxService.isConfigured()) {
      throw new Error('VITE_MAPBOX_ACCESS_TOKEN is not configured in .env file.');
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container,
      style: 'mapbox://styles/mapbox/streets-v12',
      center, // [lng, lat] in Mapbox
      zoom,
      attributionControl: false
    });

    map.addControl(new mapboxgl.NavigationControl({ showCompass: true }), 'bottom-right');

    return map;
  },

  /**
   * Mapbox Geocoding API v6 for destination search / autocomplete
   * Endpoint: https://api.mapbox.com/search/geocode/v6/forward
   */
  searchDestinationV6: async (query, proximity = null) => {
    if (!query || query.trim().length === 0) return [];
    if (!mapboxService.isConfigured()) {
      console.warn('Mapbox access token missing for Geocoding v6 search.');
      return [];
    }

    try {
      let url = `https://api.mapbox.com/search/geocode/v6/forward?q=${encodeURIComponent(query)}&autocomplete=true&limit=6&access_token=${MAPBOX_TOKEN}`;
      if (proximity && proximity.length === 2) {
        url += `&proximity=${proximity[0]},${proximity[1]}`;
      }

      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Mapbox Geocoding error: ${res.status}`);
      }

      const data = await res.json();
      const features = data.features || [];

      return features.map((f) => {
        const coords = f.geometry?.coordinates || [0, 0];
        const name = f.properties?.name || f.properties?.name_preferred || f.properties?.full_address || 'Destination';
        const fullAddress = f.properties?.full_address || f.properties?.place_formatted || name;
        return {
          id: f.id,
          name,
          full_address: fullAddress,
          lng: coords[0],
          lat: coords[1]
        };
      });
    } catch (err) {
      console.warn('Geocoding v6 search failed:', err.message);
      return [];
    }
  },

  /**
   * Mapbox Reverse Geocoding v6 to retrieve human address from [lng, lat]
   * Endpoint: https://api.mapbox.com/search/geocode/v6/reverse
   */
  reverseGeocodeV6: async (lng, lat) => {
    if (!mapboxService.isConfigured() || lng === undefined || lat === undefined) return null;
    try {
      const url = `https://api.mapbox.com/search/geocode/v6/reverse?longitude=${lng}&latitude=${lat}&access_token=${MAPBOX_TOKEN}`;
      const res = await fetch(url);
      if (!res.ok) return null;
      const data = await res.json();
      const feature = data.features?.[0];
      if (!feature) return null;
      return feature.properties?.full_address || feature.properties?.name || null;
    } catch (err) {
      console.warn('Reverse geocoding failed:', err.message);
      return null;
    }
  },

  /**
   * Mapbox Directions API v5 Routing with traffic awareness & alternatives
   * Profile: mapbox/driving-traffic
   * Params: alternatives=true, overview=full, geometries=geojson
   */
  getDrivingTrafficRoutes: async (originCoords, destCoords, waypoints = []) => {
    if (!mapboxService.isConfigured()) {
      return null;
    }

    try {
      // Coordinates format: lng,lat;lng,lat or with waypoints: lng,lat;w_lng,w_lat;lng,lat
      const allCoords = [originCoords, ...waypoints, destCoords];
      const coordString = allCoords.map(c => `${c[0]},${c[1]}`).join(';');
      const url = `https://api.mapbox.com/directions/v5/mapbox/driving-traffic/${coordString}?alternatives=true&overview=full&geometries=geojson&steps=true&annotations=congestion,distance&access_token=${MAPBOX_TOKEN}`;

      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Mapbox Directions API v5 error: ${res.status}`);
      }

      const data = await res.json();
      if (!data.routes || data.routes.length === 0) {
        return null;
      }

      return {
        routes: data.routes.map((r, idx) => ({
          id: `route_${idx}`,
          geometry: r.geometry,
          distance_meters: r.distance,
          distance_km: +(r.distance / 1000).toFixed(1),
          duration_seconds: r.duration,
          duration_minutes: Math.round(r.duration / 60),
          legs: r.legs,
          weight: r.weight,
          congestion: r.legs?.[0]?.annotation?.congestion || []
        })),
        waypoints: data.waypoints
      };
    } catch (err) {
      console.warn('Mapbox Directions API v5 error:', err.message);
      return null;
    }
  }
};

export default mapboxService;
