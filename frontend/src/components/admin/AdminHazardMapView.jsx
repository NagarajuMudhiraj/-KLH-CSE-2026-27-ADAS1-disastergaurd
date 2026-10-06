import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import mapboxService from '../../services/mapboxService';
import { 
  MapPin, 
  Plus, 
  Layers, 
  ShieldCheck, 
  Cpu, 
  User, 
  RefreshCw,
  Sliders
} from 'lucide-react';

export const AdminHazardMapView = ({ hazards = [], onNavigateToCreate, onRefresh }) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);

  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [selectedHazard, setSelectedHazard] = useState(null);

  // Initialize Mapbox map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    try {
      const center = hazards.length > 0 && hazards[0].latitude && hazards[0].longitude
        ? [hazards[0].longitude, hazards[0].latitude]
        : [78.4567, 17.4321];

      const map = mapboxService.initializeMap(mapContainerRef.current, {
        center,
        zoom: 12
      });

      mapInstanceRef.current = map;
    } catch (err) {
      console.warn('Mapbox init error in AdminHazardMapView:', err);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Hazard Markers on the Map
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    const visibleHazards = hazards.filter((h) => {
      const src = (h.source || (h.created_by ? 'ADMIN' : (h.reported_by ? 'USER' : 'AI'))).toUpperCase();
      if (sourceFilter !== 'ALL' && src !== sourceFilter) return false;
      return true;
    });

    visibleHazards.forEach((h) => {
      const lat = h.latitude !== undefined ? h.latitude : h.lat;
      const lng = h.longitude !== undefined ? h.longitude : h.lng;
      if (!lat || !lng) return;

      const src = (h.source || (h.created_by ? 'ADMIN' : (h.reported_by ? 'USER' : 'AI'))).toUpperCase();
      const isAdmin = src === 'ADMIN';
      const isUser = src === 'USER';

      let iconEmoji = '⚠️';
      const typeLower = (h.type || h.name || '').toLowerCase();
      if (typeLower.includes('flood')) iconEmoji = '🌊';
      else if (typeLower.includes('pothole')) iconEmoji = '🕳️';
      else if (typeLower.includes('fire')) iconEmoji = '🔥';
      else if (typeLower.includes('damage')) iconEmoji = '🚧';
      else if (typeLower.includes('accident')) iconEmoji = '💥';
      else if (typeLower.includes('block')) iconEmoji = '⛔';

      const el = document.createElement('div');
      el.style.cursor = 'pointer';
      el.innerHTML = `
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="
            background: ${isAdmin ? '#7c3aed' : (isUser ? '#f59e0b' : '#0284c7')};
            width: 38px; height: 38px; border-radius: 50%;
            border: 2px solid #ffffff; box-shadow: 0 0 16px ${isAdmin ? 'rgba(124, 58, 237, 0.8)' : 'rgba(2, 132, 199, 0.7)'};
            display: flex; align-items: center; justify-content: center; font-size: 18px;
            animation: pulse-ring 2.5s infinite;
          ">
            ${iconEmoji}
          </div>
          <div style="
            background: rgba(15, 23, 42, 0.9); color: #ffffff; padding: 2px 6px; border-radius: 4px;
            font-size: 9px; font-weight: 800; text-transform: uppercase; margin-top: 2px;
            border: 1px solid rgba(255, 255, 255, 0.2); white-space: nowrap;
          ">
            ${src} • ${h.severity || 'HIGH'}
          </div>
        </div>
      `;

      el.addEventListener('click', () => {
        setSelectedHazard({ ...h, lat, lng, src });
      });

      const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div style="font-family:Inter, sans-serif; font-size:0.82rem; min-width:210px; line-height:1.4;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
            <strong style="color:${isAdmin ? '#6d28d9' : '#0284c7'}; font-size:0.95rem;">
              ${iconEmoji} ${h.name || h.type}
            </strong>
            <span style="
              font-size:0.68rem; font-weight:800; padding:2px 6px; border-radius:4px;
              background:${isAdmin ? '#f5f3ff' : '#f0f9ff'};
              color:${isAdmin ? '#6d28d9' : '#0284c7'};
              border:1px solid ${isAdmin ? '#ddd6fe' : '#bae6fd'};
            ">
              ${src}
            </span>
          </div>
          <div><strong>Severity:</strong> <span style="color:#b91c1c; font-weight:700;">${h.severity || 'High'}</span></div>
          <div><strong>Address:</strong> <span style="color:#475569;">${h.address || `${lat.toFixed(4)}, ${lng.toFixed(4)}`}</span></div>
          ${h.description ? `<div><strong>Notes:</strong> <span style="color:#334155;">${h.description}</span></div>` : ''}
          <div><strong>Status:</strong> <span style="color:#059669; font-weight:700;">${h.status || 'Active'}</span></div>
        </div>
      `);

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(mapInstanceRef.current);

      markersRef.current.push(marker);
    });

    // Fit bounds if hazards exist
    if (visibleHazards.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      visibleHazards.forEach((h) => {
        const lat = h.latitude !== undefined ? h.latitude : h.lat;
        const lng = h.longitude !== undefined ? h.longitude : h.lng;
        if (lat && lng) bounds.extend([lng, lat]);
      });
      if (!bounds.isEmpty()) {
        mapInstanceRef.current.fitBounds(bounds, { padding: 80, maxZoom: 14 });
      }
    }
  }, [hazards, sourceFilter]);

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Top Controls & Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 900, color: '#0f172a', margin: 0 }}>
            City-Wide Hazard & Corridor Risk Map
          </h1>
          <p style={{ fontSize: '0.86rem', color: '#64748b', margin: '2px 0 0' }}>
            Live geospatial overview of all road conditions, flood zones, and admin bypass triggers.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Source Filter */}
          <div style={{ display: 'flex', gap: '6px' }}>
            {[
              { id: 'ALL', label: 'All Hazards' },
              { id: 'ADMIN', label: 'Admin (HQ)', color: '#6d28d9' },
              { id: 'AI', label: 'AI Detected', color: '#0284c7' },
              { id: 'USER', label: 'User Reports', color: '#b45309' }
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setSourceFilter(f.id)}
                className={`btn ${sourceFilter === f.id ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '6px 12px', fontSize: '0.78rem', fontWeight: 800 }}
              >
                {f.label}
              </button>
            ))}
          </div>

          <button
            onClick={onRefresh}
            className="btn btn-secondary"
            style={{ padding: '8px 12px', fontSize: '0.82rem' }}
            title="Refresh Map Markers"
          >
            <RefreshCw size={15} />
          </button>

          <button
            onClick={onNavigateToCreate}
            style={{
              background: '#7c3aed',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 16px',
              fontWeight: 800,
              fontSize: '0.82rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 4px 12px rgba(124, 58, 237, 0.35)'
            }}
          >
            <Plus size={16} /> Create Hazard
          </button>
        </div>
      </div>

      {/* Mapbox Canvas */}
      <div style={{ position: 'relative', width: '100%', height: '620px', borderRadius: '16px', overflow: 'hidden', border: '1px solid #cbd5e1' }}>
        <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

        {/* Legend Overlay */}
        <div style={{
          position: 'absolute', bottom: '20px', left: '20px',
          background: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(8px)',
          borderRadius: '12px', padding: '12px 16px', border: '1px solid #cbd5e1',
          boxShadow: '0 10px 25px rgba(0,0,0,0.1)', fontSize: '0.78rem', zIndex: 10
        }}>
          <div style={{ fontWeight: 800, color: '#0f172a', marginBottom: '8px', textTransform: 'uppercase', fontSize: '0.7rem' }}>
            Hazard Source Legend
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: '#7c3aed' }} />
              <strong style={{ color: '#6d28d9' }}>ADMIN</strong>: HQ Incident Commander Manual Hazard
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: '#0284c7' }} />
              <strong style={{ color: '#0284c7' }}>AI</strong>: YOLOv11 & Pothole Vision Detector
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: '#f59e0b' }} />
              <strong style={{ color: '#b45309' }}>USER</strong>: Driver & Citizen Field Report
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminHazardMapView;
