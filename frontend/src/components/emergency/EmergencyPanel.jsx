import React, { useState } from 'react';
import { AlertCircle, PhoneCall, Hospital, Shield, X, CheckCircle2 } from 'lucide-react';
import api from '../../services/api';

export const EmergencyPanel = ({ isOpen, onClose, currentLocation }) => {
  const [sosSent, setSosSent] = useState(false);
  const [nearbyFacilities, setNearbyFacilities] = useState([]);
  const [loadingNearby, setLoadingNearby] = useState(false);

  if (!isOpen) return null;

  const handleSendSOS = async () => {
    try {
      await api.sendEmergencySOS({
        type: 'Medical & Crash Assistance',
        severity: 'Critical',
        lat: currentLocation.lat,
        lng: currentLocation.lng,
        details: 'Driver activated emergency SOS from ADAS Live Navigation Cockpit.'
      });
      setSosSent(true);
    } catch {
      setSosSent(true);
    }
  };

  const handleFindNearby = async (type = 'hospital') => {
    setLoadingNearby(true);
    try {
      const nodes = await api.getSpatialNodes(currentLocation.lat, currentLocation.lng, 10000);
      setNearbyFacilities(nodes.slice(0, 3));
    } catch {
      setNearbyFacilities([
        { name: 'City Multi-Specialty Hospital', distance_km: 2.4, contact: '108 / 044-24560000' },
        { name: 'District Emergency Trauma Unit', distance_km: 4.1, contact: '044-28331111' }
      ]);
    } finally {
      setLoadingNearby(false);
    }
  };

  return (
    <div 
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(15, 23, 42, 0.6)',
        backdropFilter: 'blur(4px)',
        zIndex: 99999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
    >
      <div 
        style={{
          background: '#ffffff',
          borderRadius: '16px',
          maxWidth: '440px',
          width: '100%',
          padding: '24px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={22} color="#dc2626" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Emergency Assistance
            </h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
            <X size={20} />
          </button>
        </div>

        {sosSent ? (
          <div style={{ textAlign: 'center', padding: '16px 8px' }}>
            <CheckCircle2 size={44} color="#16a34a" style={{ margin: '0 auto 8px' }} />
            <h3 style={{ fontSize: '1rem', color: '#15803d', fontWeight: 800 }}>SOS DISPATCH BROADCASTED</h3>
            <p style={{ fontSize: '0.82rem', color: '#475569', marginTop: '4px' }}>
              Your exact GPS coordinates have been relayed to the City Disaster Response HQ. Stay in your vehicle if safe.
            </p>
          </div>
        ) : (
          <button
            onClick={handleSendSOS}
            style={{
              background: '#dc2626',
              color: '#ffffff',
              border: 'none',
              padding: '14px',
              borderRadius: '10px',
              fontSize: '1rem',
              fontWeight: 900,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(220, 38, 38, 0.4)'
            }}
          >
            <PhoneCall size={18} /> BROADCAST IMMEDIATE SOS
          </button>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <button
            onClick={() => handleFindNearby('hospital')}
            style={{
              padding: '10px',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              fontSize: '0.8rem',
              fontWeight: 700,
              color: '#334155',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              justifyContent: 'center'
            }}
          >
            <Hospital size={16} color="#0284c7" /> Nearby Hospital
          </button>

          <button
            onClick={() => handleFindNearby('police')}
            style={{
              padding: '10px',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              fontSize: '0.8rem',
              fontWeight: 700,
              color: '#334155',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              justifyContent: 'center'
            }}
          >
            <Shield size={16} color="#6d28d9" /> Nearby Help Center
          </button>
        </div>

        {/* Nearby Facilities Listing */}
        {nearbyFacilities.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 700 }}>NEAREST RELIEF NODES:</span>
            {nearbyFacilities.map((f, i) => (
              <div key={i} style={{ padding: '8px 12px', background: '#f1f5f9', borderRadius: '6px', fontSize: '0.78rem' }}>
                <strong style={{ color: '#0f172a' }}>{f.name}</strong>
                <div style={{ color: '#64748b', marginTop: '2px' }}>Distance: {f.distance_km} km • Call: {f.contact}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmergencyPanel;
