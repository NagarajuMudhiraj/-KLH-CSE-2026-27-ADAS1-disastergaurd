import React, { useState, useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import api from '../../services/api';
import mapboxService from '../../services/mapboxService';
import { 
  MapPin, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Navigation, 
  X, 
  Loader2, 
  Eye, 
  Send, 
  Flame, 
  Radio
} from 'lucide-react';

const HAZARD_TYPES = [
  'Flood',
  'Fire',
  'Smoke',
  'Pothole',
  'Road Damage',
  'Accident',
  'Road Block',
  'Heavy Traffic',
  'Other'
];

const SEVERITY_LEVELS = ['Low', 'Medium', 'High', 'Critical'];

export const CreateHazardView = ({ onHazardCreated, onCancel, onViewOnMap }) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const searchDebounceRef = useRef(null);

  // Form State
  const [formData, setFormData] = useState({
    type: 'Flood',
    severity: 'High',
    latitude: 17.4321,
    longitude: 78.4567,
    address: 'Hitech City Corridor, Hyderabad',
    description: 'Severe waterlogging under rail underpass. Road impassable for low-clearance vehicles.',
    start_time: new Date().toISOString().slice(0, 16),
    end_time: '',
    status: 'ACTIVE'
  });

  const [hasLocation, setHasLocation] = useState(true);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Initialize interactive map for location selection
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    try {
      const map = mapboxService.initializeMap(mapContainerRef.current, {
        center: [formData.longitude, formData.latitude],
        zoom: 13
      });

      map.on('load', () => {
        // Initial marker
        const el = document.createElement('div');
        el.className = 'admin-picker-pin';
        el.innerHTML = `
          <div style="background:#7c3aed; width:34px; height:34px; border-radius:50%; border:3px solid #ffffff; box-shadow:0 0 16px rgba(124, 58, 237, 0.8); display:flex; align-items:center; justify-content:center; color:#fff; font-size:16px; cursor:grab;">
            📍
          </div>
        `;

        const marker = new mapboxgl.Marker({ element: el, draggable: true })
          .setLngLat([formData.longitude, formData.latitude])
          .addTo(map);

        marker.on('dragend', async () => {
          const lngLat = marker.getLngLat();
          updateLocation(lngLat.lat, lngLat.lng);
        });

        markerRef.current = marker;
      });

      // Click on Map to select location
      map.on('click', async (e) => {
        const { lng, lat } = e.lngLat;
        if (markerRef.current) {
          markerRef.current.setLngLat([lng, lat]);
        }
        await updateLocation(lat, lng);
      });

      mapInstanceRef.current = map;
    } catch (err) {
      console.warn('Mapbox creation error:', err.message);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update coordinates and reverse geocode human address
  const updateLocation = async (lat, lng, manualAddress = null) => {
    const roundedLat = +lat.toFixed(6);
    const roundedLng = +lng.toFixed(6);

    let address = manualAddress;
    if (!address) {
      address = await mapboxService.reverseGeocodeV6(roundedLng, roundedLat);
      if (!address) {
        address = `Location (${roundedLat}, ${roundedLng})`;
      }
    }

    setFormData((prev) => ({
      ...prev,
      latitude: roundedLat,
      longitude: roundedLng,
      address
    }));
    setHasLocation(true);

    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo({ center: [roundedLng, roundedLat], zoom: 14 });
    }
    if (markerRef.current) {
      markerRef.current.setLngLat([roundedLng, roundedLat]);
    }
  };

  // Search input change handler with Mapbox v6 autocomplete
  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);

    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);

    if (val.trim().length > 1) {
      setIsSearching(true);
      searchDebounceRef.current = setTimeout(async () => {
        const proximity = [formData.longitude, formData.latitude];
        const results = await mapboxService.searchDestinationV6(val, proximity);
        setSearchSuggestions(results);
        setIsSearching(false);
      }, 250);
    } else {
      setSearchSuggestions([]);
      setIsSearching(false);
    }
  };

  const handleSelectSearchResult = (result) => {
    setSearchQuery(result.name);
    setSearchSuggestions([]);
    updateLocation(result.lat, result.lng, result.full_address || result.name);
  };

  const handleGoToPreview = (e) => {
    e.preventDefault();
    if (!formData.latitude || !formData.longitude) {
      setErrorMessage('Please select a valid location on the map or search.');
      return;
    }
    setErrorMessage(null);
    setIsPreviewMode(true);
  };

  // Final Submit to Backend Database
  const handleCreateHazard = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const payload = {
        type: formData.type,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        address: formData.address,
        severity: formData.severity,
        description: formData.description,
        start_time: formData.start_time ? new Date(formData.start_time).toISOString() : new Date().toISOString(),
        end_time: formData.end_time ? new Date(formData.end_time).toISOString() : null,
        status: formData.status
      };

      const res = await api.createAdminHazard(payload);
      setSuccessMessage('Admin hazard created and published to live fleet successfully!');
      
      if (onHazardCreated) {
        onHazardCreated(res.hazard || res);
      }
    } catch (err) {
      console.error('Hazard creation error:', err);
      setErrorMessage(err.response?.data?.detail || err.message || 'Failed to create hazard.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ padding: '4px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Title & Instructions Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ 
              background: '#f5f3ff', color: '#6d28d9', padding: '4px 10px', 
              borderRadius: '6px', fontSize: '0.72rem', fontWeight: 800, border: '1px solid #ddd6fe' 
            }}>
              HQ DISASTER AUTHORIZATION
            </span>
            <span style={{ fontSize: '0.8rem', color: '#64748b' }}>• Source Tag: <strong>ADMIN</strong></span>
          </div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 900, color: '#0f172a', margin: '4px 0 0' }}>
            Publish Admin Hazard at Any Map Location
          </h1>
          <p style={{ fontSize: '0.86rem', color: '#64748b', margin: '2px 0 0' }}>
            Select any point on the map or search an address. Published hazards will be stored in the database, broadcasted to active drivers, and integrated into ADAS route-risk avoidance.
          </p>
        </div>

        {onCancel && (
          <button onClick={onCancel} className="btn btn-secondary" style={{ padding: '8px 16px' }}>
            <X size={16} /> Cancel
          </button>
        )}
      </div>

      {/* Success Notification */}
      {successMessage && (
        <div 
          style={{ 
            background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '12px', 
            padding: '16px 20px', marginBottom: '20px', display: 'flex', alignItems: 'center', 
            justifyContent: 'space-between', gap: '16px' 
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <CheckCircle2 size={24} color="#16a34a" />
            <div>
              <strong style={{ color: '#15803d', fontSize: '0.95rem' }}>Hazard Published Successfully!</strong>
              <div style={{ fontSize: '0.82rem', color: '#166534' }}>{successMessage}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {onViewOnMap && (
              <button 
                onClick={onViewOnMap} 
                className="btn btn-primary"
                style={{ padding: '8px 16px', fontSize: '0.82rem' }}
              >
                View on Hazard Map ➔
              </button>
            )}
            <button 
              onClick={() => {
                setSuccessMessage(null);
                setIsPreviewMode(false);
              }} 
              className="btn btn-secondary"
              style={{ padding: '8px 16px', fontSize: '0.82rem' }}
            >
              + Create Another
            </button>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <div style={{ 
          background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '12px', 
          padding: '12px 18px', marginBottom: '20px', color: '#b91c1c', fontSize: '0.86rem',
          display: 'flex', alignItems: 'center', gap: '8px' 
        }}>
          <AlertTriangle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE 1: FORM & MAP LOCATION SELECTION */}
      {/* ========================================================================= */}
      {!isPreviewMode && !successMessage && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
          
          {/* Left Column: Interactive Location Picker Map & Search */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '0.85rem', fontWeight: 800, color: '#0f172a', display: 'block', marginBottom: '6px' }}>
                1. Select Location (Click Map or Search)
              </label>

              {/* Location Search Bar */}
              <div style={{ position: 'relative' }}>
                <div style={{
                  display: 'flex', alignItems: 'center', background: '#f8fafc',
                  border: '1px solid #cbd5e1', borderRadius: '10px', padding: '8px 12px'
                }}>
                  <Search size={16} color="#64748b" style={{ marginRight: '8px', flexShrink: 0 }} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={handleSearchChange}
                    placeholder="Search city, address, or landmark (e.g. Karimnagar, Hyderabad)..."
                    style={{ border: 'none', background: 'transparent', width: '100%', outline: 'none', fontSize: '0.88rem' }}
                  />
                  {isSearching && <Loader2 size={16} className="animate-spin" color="#64748b" />}
                  {searchQuery && !isSearching && (
                    <button 
                      onClick={() => { setSearchQuery(''); setSearchSuggestions([]); }}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                {/* Autocomplete Suggestions */}
                {searchSuggestions.length > 0 && (
                  <div style={{
                    position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0,
                    background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '8px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.15)', zIndex: 1000, maxHeight: '200px', overflowY: 'auto'
                  }}>
                    {searchSuggestions.map((item, idx) => (
                      <div
                        key={item.id || idx}
                        onClick={() => handleSelectSearchResult(item)}
                        style={{
                          padding: '10px 12px', fontSize: '0.82rem', cursor: 'pointer',
                          borderBottom: idx < searchSuggestions.length - 1 ? '1px solid #f1f5f9' : 'none'
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = '#ffffff')}
                      >
                        <strong style={{ display: 'block', color: '#0f172a' }}>{item.name}</strong>
                        <span style={{ fontSize: '0.74rem', color: '#64748b' }}>{item.full_address}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Interactive Mapbox Canvas */}
            <div style={{ position: 'relative', width: '100%', height: '380px', borderRadius: '12px', overflow: 'hidden', border: '1px solid #cbd5e1' }}>
              <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
              <div style={{
                position: 'absolute', bottom: '12px', left: '12px',
                background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(8px)',
                color: '#fff', padding: '6px 12px', borderRadius: '8px', fontSize: '0.75rem',
                display: 'flex', alignItems: 'center', gap: '6px', pointerEvents: 'none'
              }}>
                <MapPin size={14} color="#a855f7" />
                <span>Click any point on the map to place the hazard pin</span>
              </div>
            </div>

            {/* Selected Location Pill */}
            <div style={{
              background: '#f8fafc', padding: '12px 14px', borderRadius: '10px',
              border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
                  Selected Location Anchor
                </span>
                <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#0f172a' }}>
                  {formData.address}
                </div>
                <div style={{ fontSize: '0.76rem', color: '#64748b', fontFamily: 'monospace' }}>
                  Latitude: {formData.latitude} • Longitude: {formData.longitude}
                </div>
              </div>
              <span className="badge badge-safe" style={{ fontSize: '0.72rem' }}>Pin Anchored</span>
            </div>
          </div>

          {/* Right Column: Hazard Details Form */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <form onSubmit={handleGoToPreview} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              
              {/* Hazard Type */}
              <div className="form-group">
                <label className="form-label" style={{ fontWeight: 800, color: '#0f172a' }}>
                  Hazard Type *
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="form-select"
                  style={{ fontWeight: 700 }}
                  required
                >
                  {HAZARD_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {/* Severity Level */}
              <div className="form-group">
                <label className="form-label" style={{ fontWeight: 800, color: '#0f172a' }}>
                  Severity Level *
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                  {SEVERITY_LEVELS.map((s) => {
                    const isSelected = formData.severity === s;
                    let activeBg = '#0284c7';
                    if (s === 'Low') activeBg = '#10b981';
                    if (s === 'Medium') activeBg = '#f59e0b';
                    if (s === 'High') activeBg = '#ea580c';
                    if (s === 'Critical') activeBg = '#dc2626';

                    return (
                      <button
                        type="button"
                        key={s}
                        onClick={() => setFormData({ ...formData, severity: s })}
                        style={{
                          padding: '8px',
                          border: isSelected ? `2px solid ${activeBg}` : '1px solid #cbd5e1',
                          background: isSelected ? activeBg : '#ffffff',
                          color: isSelected ? '#ffffff' : '#334155',
                          borderRadius: '8px',
                          fontWeight: 800,
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        {s}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Description */}
              <div className="form-group">
                <label className="form-label" style={{ fontWeight: 800, color: '#0f172a' }}>
                  Description / Incident Notes *
                </label>
                <textarea
                  rows="3"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="e.g. Flooded road near bridge, water depth 35cm, vehicles must divert..."
                  className="form-textarea"
                  required
                />
              </div>

              {/* Start & End Times */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: 800, color: '#0f172a' }}>
                    Start Time *
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="form-input"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: 800, color: '#0f172a' }}>
                    End Time (Optional)
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="form-input"
                  />
                </div>
              </div>

              {/* Status */}
              <div className="form-group">
                <label className="form-label" style={{ fontWeight: 800, color: '#0f172a' }}>
                  Status *
                </label>
                <div style={{ display: 'flex', gap: '12px' }}>
                  {['ACTIVE', 'INACTIVE'].map((st) => (
                    <label 
                      key={st} 
                      style={{ 
                        display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', 
                        fontSize: '0.86rem', fontWeight: 700 
                      }}
                    >
                      <input
                        type="radio"
                        name="hazard_status"
                        value={st}
                        checked={formData.status === st}
                        onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      />
                      <span>{st === 'ACTIVE' ? 'Active (Live Alert)' : 'Inactive (Draft)'}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Submit to Preview Button */}
              <div style={{ marginTop: '12px' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '0.95rem',
                    fontWeight: 800,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  <Eye size={18} /> Preview Hazard Details ➔
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE 2: ADMIN HAZARD PREVIEW STEP */}
      {/* ========================================================================= */}
      {isPreviewMode && !successMessage && (
        <div className="glass-panel" style={{ padding: '32px', maxWidth: '720px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <div style={{ background: '#7c3aed', color: '#fff', width: '36px', height: '36px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Eye size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 900, color: '#0f172a', margin: 0 }}>
                Admin Hazard Preview
              </h2>
              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                Review before saving to database and broadcasting to active drivers
              </span>
            </div>
          </div>

          {/* Details Card */}
          <div style={{ 
            background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '14px', 
            padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' 
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
              <div>
                <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>
                  HAZARD CLASSIFICATION
                </span>
                <div style={{ fontSize: '1.2rem', fontWeight: 900, color: '#0f172a' }}>
                  {formData.type}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <span className="badge badge-info" style={{ background: '#f5f3ff', color: '#6d28d9', border: '1px solid #ddd6fe' }}>
                  Source: ADMIN
                </span>
                <span className={`badge ${
                  formData.severity === 'Critical' ? 'badge-danger' : 
                  formData.severity === 'High' ? 'badge-warning' : 'badge-safe'
                }`}>
                  {formData.severity} Severity
                </span>
                <span className="badge badge-safe">
                  {formData.status}
                </span>
              </div>
            </div>

            {/* Location */}
            <div>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>
                Location & Coordinates
              </span>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a' }}>
                📍 {formData.address}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', fontFamily: 'monospace' }}>
                Lat: {formData.latitude} • Lng: {formData.longitude}
              </div>
            </div>

            {/* Description */}
            <div>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>
                Description
              </span>
              <p style={{ margin: '4px 0 0', fontSize: '0.88rem', color: '#334155', lineHeight: 1.5 }}>
                {formData.description}
              </p>
            </div>

            {/* Timeline */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', borderTop: '1px solid #e2e8f0', paddingTop: '12px' }}>
              <div>
                <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>
                  Active From
                </span>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a' }}>
                  {new Date(formData.start_time).toLocaleString()}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>
                  Active Until
                </span>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0f172a' }}>
                  {formData.end_time ? new Date(formData.end_time).toLocaleString() : 'Indefinite / Until Cleared'}
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setIsPreviewMode(false)}
              className="btn btn-secondary"
              style={{ padding: '12px 24px', fontWeight: 700 }}
              disabled={isSubmitting}
            >
              ← Back to Edit
            </button>

            <button
              onClick={handleCreateHazard}
              style={{
                background: '#7c3aed',
                color: '#ffffff',
                border: 'none',
                borderRadius: '10px',
                padding: '12px 28px',
                fontSize: '0.95rem',
                fontWeight: 800,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 14px rgba(124, 58, 237, 0.4)'
              }}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={18} className="animate-spin" /> Saving & Broadcasting...
                </>
              ) : (
                <>
                  <Send size={18} /> Create & Publish Hazard
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CreateHazardView;
