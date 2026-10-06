/**
 * Google Maps Platform Service Abstraction
 * Supports Google Maps JavaScript API, Places Autocomplete, and Directions/Routes API.
 * Seamlessly provides OpenStreetMap/Leaflet fallback if VITE_GOOGLE_MAPS_API_KEY is not configured.
 */

const GOOGLE_MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';
let googleMapsScriptLoaded = false;
let googleMapsLoadingPromise = null;

export const googleMapsService = {
  isKeyConfigured: () => Boolean(GOOGLE_MAPS_KEY && GOOGLE_MAPS_KEY !== 'your_google_maps_api_key_here'),

  /**
   * Dynamically loads Google Maps JavaScript SDK
   */
  loadGoogleMapsScript: () => {
    if (!googleMapsService.isKeyConfigured()) {
      return Promise.reject(new Error('Google Maps API key not configured in .env. Using high-definition Leaflet fallback.'));
    }

    if (googleMapsScriptLoaded && window.google?.maps) {
      return Promise.resolve(window.google.maps);
    }

    if (googleMapsLoadingPromise) {
      return googleMapsLoadingPromise;
    }

    googleMapsLoadingPromise = new Promise((resolve, reject) => {
      const scriptId = 'google-maps-platform-script';
      if (document.getElementById(scriptId)) {
        if (window.google?.maps) {
          googleMapsScriptLoaded = true;
          return resolve(window.google.maps);
        }
      }

      const script = document.createElement('script');
      script.id = scriptId;
      script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_KEY}&libraries=places,geometry&callback=__initGoogleMapsPlatform`;
      script.async = true;
      script.defer = true;

      window.__initGoogleMapsPlatform = () => {
        googleMapsScriptLoaded = true;
        resolve(window.google.maps);
      };

      script.onerror = (err) => {
        reject(new Error('Failed to load Google Maps script. Check network or API key permissions.'));
      };

      document.head.appendChild(script);
    });

    return googleMapsLoadingPromise;
  },

  /**
   * Initializes a Google Map or returns fallback instructions
   */
  initializeMap: async (container, options = {}) => {
    const maps = await googleMapsService.loadGoogleMapsScript();
    const defaultCenter = options.center || { lat: 13.035, lng: 80.245 };
    const defaultZoom = options.zoom || 13;

    const map = new maps.Map(container, {
      center: defaultCenter,
      zoom: defaultZoom,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      styles: [
        { featureType: 'poi', stylers: [{ visibility: 'off' }] },
        { featureType: 'transit', stylers: [{ visibility: 'simplified' }] }
      ],
      ...options
    });

    // Add traffic layer if supported
    if (options.showTraffic !== false) {
      const trafficLayer = new maps.TrafficLayer();
      trafficLayer.setMap(map);
    }

    return map;
  },

  /**
   * Search for destinations using Google Places Service or local matching
   */
  searchDestination: async (query, center = { lat: 13.035, lng: 80.245 }) => {
    if (!query) return [];

    if (googleMapsService.isKeyConfigured() && window.google?.maps?.places) {
      const service = new window.google.maps.places.AutocompleteService();
      return new Promise((resolve) => {
        service.getPlacePredictions(
          {
            input: query,
            location: new window.google.maps.LatLng(center.lat, center.lng),
            radius: 50000
          },
          (predictions, status) => {
            if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
              resolve(
                predictions.map((p) => ({
                  description: p.description,
                  placeId: p.place_id,
                  mainText: p.structured_formatting?.main_text || p.description
                }))
              );
            } else {
              resolve([]);
            }
          }
        );
      });
    }

    // Local presets for fast search when offline/fallback
    const presets = [
      { description: 'OMR IT Corridor, Chennai', lat: 12.9815, lng: 80.2180 },
      { description: 'Chennai Airport Terminal, Meenambakkam', lat: 12.9941, lng: 80.1709 },
      { description: 'City Center Hub, Anna Salai', lat: 13.0569, lng: 80.2425 },
      { description: 'Marina Bay Expressway Corridor', lat: 13.0475, lng: 80.2824 },
      { description: 'Central Railway Hub, Park Town', lat: 13.0827, lng: 80.2707 }
    ];

    return presets.filter((p) => p.description.toLowerCase().includes(query.toLowerCase()));
  },

  /**
   * Request routes via Google Directions Service
   */
  getRoutes: async (origin, destination) => {
    if (googleMapsService.isKeyConfigured() && window.google?.maps) {
      const directionsService = new window.google.maps.DirectionsService();
      return new Promise((resolve, reject) => {
        directionsService.route(
          {
            origin: new window.google.maps.LatLng(origin.lat, origin.lng),
            destination: new window.google.maps.LatLng(destination.lat, destination.lng),
            travelMode: window.google.maps.TravelMode.DRIVING,
            provideRouteAlternatives: true,
            drivingOptions: {
              departureTime: new Date(),
              trafficModel: window.google.maps.TrafficModel.BEST_GUESS
            }
          },
          (result, status) => {
            if (status === window.google.maps.DirectionsStatus.OK && result) {
              resolve(result);
            } else {
              reject(new Error(`Google Routes error: ${status}`));
            }
          }
        );
      });
    }

    return null;
  }
};

export default googleMapsService;
