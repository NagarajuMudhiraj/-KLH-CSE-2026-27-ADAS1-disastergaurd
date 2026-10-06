import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import L from 'leaflet';
import mapboxService from '../../services/mapboxService';

export const LiveMap = ({
  currentLocation,
  destination,
  routeData,
  hazards = [],
  onHazardClick,
  vehiclePosition,
  isNavigating
}) => {
  const mapContainerRef = useRef(null);
  const mapboxInstanceRef = useRef(null);
  const leafletInstanceRef = useRef(null);

  // Markers & Layers refs
  const currentLocMarkerRef = useRef(null);
  const currentLocLeafletMarkerRef = useRef(null);
  const destMarkerRef = useRef(null);
  const destLeafletMarkerRef = useRef(null);
  const hazardMarkersRef = useRef([]);

  const isMapbox = mapboxService.isConfigured();

  // Helper to create or update the user location mark
  const updateUserLocationMarker = (lat, lng) => {
    if (!lat || !lng) return;

    // --- 1. Mapbox GL JS Marker ---
    if (mapboxInstanceRef.current) {
      if (!currentLocMarkerRef.current) {
        const el = document.createElement('div');
        el.className = 'user-location-marker';
        el.style.display = 'flex';
        el.style.flexDirection = 'column';
        el.style.alignItems = 'center';
        el.style.cursor = 'pointer';
        el.style.zIndex = '50';

        el.innerHTML = `
          <div style="
            background: #0284c7;
            color: #ffffff;
            font-size: 10px;
            font-weight: 900;
            padding: 3px 8px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.45);
            border: 2px solid #ffffff;
            white-space: nowrap;
            margin-bottom: 2px;
            letter-spacing: 0.04em;
            display: flex;
            align-items: center;
            gap: 5px;
          ">
            <span style="display:inline-block; width:7px; height:7px; border-radius:50%; background:#22c55e; box-shadow:0 0 6px #22c55e;"></span>
            YOU ARE HERE
          </div>
          <div style="position:relative; width:48px; height:48px; display:flex; align-items:center; justify-content:center;">
            <div style="
              position: absolute;
              width: 48px;
              height: 48px;
              border-radius: 50%;
              background: rgba(2, 132, 199, 0.3);
              animation: pulse-ring 2s infinite ease-out;
            "></div>
            <div style="
              position: absolute;
              width: 32px;
              height: 32px;
              border-radius: 50%;
              background: rgba(2, 132, 199, 0.45);
            "></div>
            <div style="
              position: relative;
              background: #0284c7;
              width: 22px;
              height: 22px;
              border-radius: 50%;
              border: 3px solid #ffffff;
              box-shadow: 0 0 16px rgba(2, 132, 199, 1);
              display: flex;
              align-items: center;
              justify-content: center;
              color: #ffffff;
              font-size: 11px;
              font-weight: 900;
            ">
              ▲
            </div>
          </div>
        `;

        const popup = new mapboxgl.Popup({ offset: 35, closeButton: false }).setHTML(`
          <div style="font-family:Inter, sans-serif; font-size:0.82rem; padding:4px; line-height:1.4;">
            <strong style="color:#0284c7; font-size:0.9rem; display:flex; align-items:center; gap:4px; margin-bottom:2px;">
              📍 Your Current Location
            </strong>
            <div style="color:#475569; font-size:0.75rem;">
              Latitude: ${lat.toFixed(5)}<br/>
              Longitude: ${lng.toFixed(5)}
            </div>
            <div style="color:#059669; font-weight:800; font-size:0.72rem; margin-top:4px;">
              ✓ Real GPS Satellite Anchor
            </div>
          </div>
        `);

        currentLocMarkerRef.current = new mapboxgl.Marker({ element: el })
          .setLngLat([lng, lat])
          .setPopup(popup)
          .addTo(mapboxInstanceRef.current);
      } else {
        currentLocMarkerRef.current.setLngLat([lng, lat]);
      }
    }

    // --- 2. Leaflet Fallback Marker ---
    if (leafletInstanceRef.current) {
      if (!currentLocLeafletMarkerRef.current) {
        const leafletIcon = L.divIcon({
          className: 'user-location-leaflet-marker',
          html: `
            <div style="display:flex; flex-direction:column; align-items:center;">
              <div style="background:#0284c7; color:#fff; font-size:9px; font-weight:900; padding:2px 8px; border-radius:10px; border:1.5px solid #fff; white-space:nowrap; margin-bottom:2px; box-shadow:0 2px 8px rgba(0,0,0,0.3);">
                YOU ARE HERE
              </div>
              <div style="background:#0284c7; width:22px; height:22px; border-radius:50%; border:3px solid #ffffff; box-shadow:0 0 14px #0284c7; display:flex; align-items:center; justify-content:center; color:#fff; font-size:10px; font-weight:900;">
                ▲
              </div>
            </div>
          `,
          iconSize: [90, 48],
          iconAnchor: [45, 40]
        });

        currentLocLeafletMarkerRef.current = L.marker([lat, lng], { icon: leafletIcon })
          .addTo(leafletInstanceRef.current)
          .bindPopup('<strong>📍 Your Current Location</strong><br/>Starting Point for Navigation');
      } else {
        currentLocLeafletMarkerRef.current.setLatLng([lat, lng]);
      }
    }
  };

  // 1. Initialize Map (Mapbox GL JS primary, Leaflet fallback)
  useEffect(() => {
    if (!mapContainerRef.current || !currentLocation) return;

    if (isMapbox) {
      if (mapboxInstanceRef.current) {
        mapboxInstanceRef.current.setCenter([currentLocation.lng, currentLocation.lat]);
        updateUserLocationMarker(currentLocation.lat, currentLocation.lng);
        return;
      }

      try {
        const map = mapboxService.initializeMap(mapContainerRef.current, {
          center: [currentLocation.lng, currentLocation.lat],
          zoom: 14
        });

        map.on('load', () => {
          // Immediately place user location marker on map load
          updateUserLocationMarker(currentLocation.lat, currentLocation.lng);

          // Initialize GeoJSON sources for primary and alternative routes
          map.addSource('primary-route-source', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] }
          });

          map.addSource('alternative-route-source', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] }
          });

          // Alternative route layer (rendered underneath primary)
          map.addLayer({
            id: 'alternative-route-layer',
            type: 'line',
            source: 'alternative-route-source',
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: {
              'line-color': '#10b981',
              'line-width': 5,
              'line-opacity': 0.8
            }
          });

          // Primary route layer
          map.addLayer({
            id: 'primary-route-layer',
            type: 'line',
            source: 'primary-route-source',
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: {
              'line-color': '#0284c7',
              'line-width': 6,
              'line-opacity': 0.95
            }
          });
        });

        mapboxInstanceRef.current = map;
      } catch (err) {
        console.warn('Mapbox initialization warning, using Leaflet engine:', err.message);
        initLeafletFallback();
      }
    } else {
      initLeafletFallback();
    }

    function initLeafletFallback() {
      if (leafletInstanceRef.current) {
        leafletInstanceRef.current.setView([currentLocation.lat, currentLocation.lng], 14);
        updateUserLocationMarker(currentLocation.lat, currentLocation.lng);
        return;
      }

      const map = L.map(mapContainerRef.current, {
        center: [currentLocation.lat, currentLocation.lng],
        zoom: 14,
        zoomControl: true
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(map);

      leafletInstanceRef.current = map;
      updateUserLocationMarker(currentLocation.lat, currentLocation.lng);
    }

    return () => {
      if (mapboxInstanceRef.current) {
        mapboxInstanceRef.current.remove();
        mapboxInstanceRef.current = null;
      }
      if (leafletInstanceRef.current) {
        leafletInstanceRef.current.remove();
        leafletInstanceRef.current = null;
      }
      currentLocMarkerRef.current = null;
      currentLocLeafletMarkerRef.current = null;
    };
  }, [isMapbox, Boolean(currentLocation)]);

  // Resize Listener: Dynamically re-adjust Mapbox GL or Leaflet canvas when camera side panel is docked or resized
  useEffect(() => {
    const handleResize = () => {
      if (mapboxInstanceRef.current) {
        try {
          mapboxInstanceRef.current.resize();
        } catch {
          // ignore transient resize error
        }
      }
      if (leafletInstanceRef.current) {
        try {
          leafletInstanceRef.current.invalidateSize();
        } catch {
          // ignore transient resize error
        }
      }
    };

    window.addEventListener('resize', handleResize);

    let ro = null;
    if (mapContainerRef.current && typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(() => {
        handleResize();
      });
      ro.observe(mapContainerRef.current);
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      if (ro) ro.disconnect();
    };
  }, []);

  // 2. Current Location Marker & Real-Time Tracking
  useEffect(() => {
    if (!currentLocation) return;

    const lat = vehiclePosition ? vehiclePosition.lat : currentLocation.lat;
    const lng = vehiclePosition ? vehiclePosition.lng : currentLocation.lng;

    updateUserLocationMarker(lat, lng);

    if (isNavigating) {
      if (mapboxInstanceRef.current) {
        mapboxInstanceRef.current.panTo([lng, lat], { duration: 1000 });
      }
      if (leafletInstanceRef.current) {
        leafletInstanceRef.current.panTo([lat, lng]);
      }
    }
  }, [currentLocation, vehiclePosition, isNavigating]);

  // 3. Destination Marker
  useEffect(() => {
    if (!destination) {
      if (destMarkerRef.current) {
        destMarkerRef.current.remove();
        destMarkerRef.current = null;
      }
      if (destLeafletMarkerRef.current) {
        destLeafletMarkerRef.current.remove();
        destLeafletMarkerRef.current = null;
      }
      return;
    }

    // Mapbox
    if (mapboxInstanceRef.current) {
      if (!destMarkerRef.current) {
        const el = document.createElement('div');
        el.style.display = 'flex';
        el.style.flexDirection = 'column';
        el.style.alignItems = 'center';
        el.style.cursor = 'pointer';

        el.innerHTML = `
          <div style="
            background: #ea580c;
            color: #ffffff;
            font-size: 10px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
            border: 1.5px solid #ffffff;
            white-space: nowrap;
            margin-bottom: 2px;
          ">
            DESTINATION
          </div>
          <div style="
            background: #ea580c;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 3px solid #ffffff;
            box-shadow: 0 0 14px rgba(234, 88, 12, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 13px;
            font-weight: 900;
          ">
            🏁
          </div>
        `;

        destMarkerRef.current = new mapboxgl.Marker({ element: el })
          .setLngLat([destination.lng, destination.lat])
          .addTo(mapboxInstanceRef.current);
      } else {
        destMarkerRef.current.setLngLat([destination.lng, destination.lat]);
      }
    }

    // Leaflet
    if (leafletInstanceRef.current) {
      if (!destLeafletMarkerRef.current) {
        destLeafletMarkerRef.current = L.marker([destination.lat, destination.lng])
          .addTo(leafletInstanceRef.current)
          .bindPopup(`<strong>🏁 Destination: ${destination.name || 'Target'}</strong>`);
      } else {
        destLeafletMarkerRef.current.setLatLng([destination.lat, destination.lng]);
      }
    }
  }, [destination]);

  // 4. Update Mapbox Route Layers (Primary & Alternative Routes)
  useEffect(() => {
    if (!mapboxInstanceRef.current) return;

    const map = mapboxInstanceRef.current;
    if (!map.isStyleLoaded()) return;

    const primarySource = map.getSource('primary-route-source');
    const altSource = map.getSource('alternative-route-source');

    if (!primarySource || !altSource) return;

    const primaryRoute = routeData?.primaryRoute;
    const alternativeRoute = routeData?.alternativeRoute;

    if (primaryRoute?.geometry) {
      // Primary Route GeoJSON
      primarySource.setData({
        type: 'Feature',
        properties: {},
        geometry: primaryRoute.geometry
      });

      // Style line color:
      // - Red dashed if user explicitly chose to continue on compromised route
      // - Emerald green solid if automatically shifted to safe bypass
      // - Standard blue solid if clean shortest route
      if (routeData?.userChoseOriginal) {
        map.setPaintProperty('primary-route-layer', 'line-color', '#ef4444');
        map.setPaintProperty('primary-route-layer', 'line-dasharray', [2, 2]);
      } else if (routeData?.isShifted) {
        map.setPaintProperty('primary-route-layer', 'line-color', '#10b981');
        map.setPaintProperty('primary-route-layer', 'line-dasharray', [1, 0]);
      } else {
        map.setPaintProperty('primary-route-layer', 'line-color', '#0284c7');
        map.setPaintProperty('primary-route-layer', 'line-dasharray', [1, 0]);
      }

      // Fit bounds around primary route coordinates
      const coords = primaryRoute.geometry.coordinates || [];
      if (coords.length > 0) {
        const bounds = coords.reduce((b, coord) => b.extend(coord), new mapboxgl.LngLatBounds(coords[0], coords[0]));
        map.fitBounds(bounds, { padding: 80 });
      }
    } else if (currentLocation && destination) {
      // Generate direct GeoJSON line if Directions API pending
      const directLine = {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: [
            [currentLocation.lng, currentLocation.lat],
            [destination.lng, destination.lat]
          ]
        }
      };
      primarySource.setData(directLine);
    } else {
      primarySource.setData({ type: 'FeatureCollection', features: [] });
    }

    // Always clear alternative route source to guarantee ONLY a single shortest path is displayed
    altSource.setData({ type: 'FeatureCollection', features: [] });
  }, [routeData, currentLocation, destination]);

  // 5. Update Real Backend Hazards on Mapbox
  useEffect(() => {
    if (!mapboxInstanceRef.current) return;

    // Clear previous hazard markers
    hazardMarkersRef.current.forEach((m) => m.remove());
    hazardMarkersRef.current = [];

    hazards.forEach((h) => {
      const lat = h.latitude !== undefined ? h.latitude : h.lat;
      const lng = h.longitude !== undefined ? h.longitude : h.lng;
      if (!lat || !lng) return;

      const isPothole = h.type?.includes('pothole') || h.name?.toLowerCase().includes('pothole');
      const isFlood = h.type?.includes('flood') || h.name?.toLowerCase().includes('flood');
      const isFire = h.type?.includes('fire') || h.name?.toLowerCase().includes('fire');
      const isDamage = h.type?.includes('damage') || h.name?.toLowerCase().includes('damage');
      const isAccident = h.type?.includes('accident') || h.name?.toLowerCase().includes('accident');
      const isBlock = h.type?.includes('block') || h.name?.toLowerCase().includes('block');

      let iconEmoji = '⚠️';
      if (isPothole) iconEmoji = '🕳️';
      else if (isFlood) iconEmoji = '🌊';
      else if (isFire) iconEmoji = '🔥';
      else if (isDamage) iconEmoji = '🚧';
      else if (isAccident) iconEmoji = '💥';
      else if (isBlock) iconEmoji = '⛔';

      const source = (h.source || 'AI').toUpperCase();
      const isAdminSource = source === 'ADMIN';

      // Distance calculation from current user GPS
      let distanceText = 'Nearby';
      if (currentLocation?.lat && currentLocation?.lng) {
        const dLat = (lat - currentLocation.lat) * (Math.PI / 180);
        const dLon = (lng - currentLocation.lng) * (Math.PI / 180);
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
          Math.cos(currentLocation.lat * (Math.PI / 180)) * Math.cos(lat * (Math.PI / 180)) *
          Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const dKm = 6371 * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
        distanceText = `${dKm.toFixed(1)} km`;
      }

      const el = document.createElement('div');
      el.innerHTML = `
        <div style="display:flex; flex-direction:column; align-items:center; cursor:pointer;">
          <div style="
            background: ${isAdminSource ? '#7c3aed' : '#ef4444'}; width: 36px; height: 36px; border-radius: 50%;
            border: 2px solid #ffffff; box-shadow: 0 0 14px ${isAdminSource ? 'rgba(124, 58, 237, 0.7)' : 'rgba(239, 68, 68, 0.7)'};
            display: flex; align-items: center; justify-content: center; font-size: 16px;
            animation: pulse-ring 2s infinite;
          ">
            ${iconEmoji}
          </div>
          <div style="
            background: rgba(15, 23, 42, 0.9); color: #ffffff; padding: 2px 6px; border-radius: 4px;
            font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 2px;
            border: 1px solid rgba(255, 255, 255, 0.2); white-space: nowrap;
          ">
            ${h.name || 'Hazard'} • ${h.severity || 'HIGH'}
          </div>
        </div>
      `;

      el.addEventListener('click', () => {
        if (onHazardClick) {
          onHazardClick({
            ...h,
            distanceText,
            source: isAdminSource ? 'Admin' : (source === 'USER' ? 'Driver Report' : 'AI Detector')
          });
        }
      });

      const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div style="font-family:Inter, sans-serif; font-size:0.82rem; min-width:210px; line-height:1.4;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">
            <strong style="color:${isAdminSource ? '#6d28d9' : '#dc2626'}; font-size:0.95rem;">
              ${iconEmoji} ${h.name || h.type}
            </strong>
            <span style="
              font-size:0.68rem; font-weight:800; padding:2px 6px; border-radius:4px;
              background:${isAdminSource ? '#f5f3ff' : '#fef2f2'};
              color:${isAdminSource ? '#6d28d9' : '#dc2626'};
              border:1px solid ${isAdminSource ? '#ddd6fe' : '#fecaca'};
            ">
              ${isAdminSource ? 'ADMIN SOURCE' : source}
            </span>
          </div>
          <div><strong>Severity:</strong> <span style="color:#b91c1c; font-weight:700;">${h.severity || 'High'}</span></div>
          <div><strong>Source:</strong> <span>${isAdminSource ? 'Admin Reported Hazard' : (source === 'USER' ? 'User Report' : 'AI Detected')}</span></div>
          <div><strong>Location:</strong> <span style="color:#475569;">${h.address || `${lat.toFixed(4)}, ${lng.toFixed(4)}`}</span></div>
          ${h.description ? `<div><strong>Description:</strong> <span style="color:#334155;">${h.description}</span></div>` : ''}
          <div><strong>Distance:</strong> <span>${distanceText}</span></div>
          <div><strong>Status:</strong> <span style="color:#059669; font-weight:700;">${h.status || 'Active'}</span></div>
        </div>
      `);

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(mapboxInstanceRef.current);

      hazardMarkersRef.current.push(marker);
    });
  }, [hazards, onHazardClick]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%', borderRadius: '16px' }} />

      {/* Recenter on User Location Marker Button */}
      {currentLocation && (
        <button
          onClick={() => {
            const lat = vehiclePosition ? vehiclePosition.lat : currentLocation.lat;
            const lng = vehiclePosition ? vehiclePosition.lng : currentLocation.lng;
            if (mapboxInstanceRef.current) {
              mapboxInstanceRef.current.flyTo({ center: [lng, lat], zoom: 15, duration: 1000 });
            }
            if (leafletInstanceRef.current) {
              leafletInstanceRef.current.setView([lat, lng], 15);
            }
          }}
          style={{
            position: 'absolute',
            top: '80px',
            right: '20px',
            zIndex: 400,
            background: '#ffffff',
            border: '1.5px solid #cbd5e1',
            borderRadius: '12px',
            padding: '8px 14px',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.12)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            fontSize: '0.82rem',
            fontWeight: 800,
            color: '#0284c7'
          }}
          title="Center Map on Your Current Location"
        >
          <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: '#0284c7', boxShadow: '0 0 6px #0284c7' }}></span>
          <span>Center on Me</span>
        </button>
      )}

      {!isMapbox && (
        <div 
          style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            background: 'rgba(255, 255, 255, 0.9)',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '0.72rem',
            color: '#64748b',
            border: '1px solid #cbd5e1'
          }}
        >
          Mapbox token pending in .env • Operating on OpenStreetMap
        </div>
      )}
    </div>
  );
};

export default LiveMap;
