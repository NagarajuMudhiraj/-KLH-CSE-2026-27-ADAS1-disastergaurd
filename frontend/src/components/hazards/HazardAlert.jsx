import React from 'react';
import { AlertOctagon, ArrowRight, X } from 'lucide-react';

export const HazardAlert = ({ alert, onClose, onViewRoute }) => {
  if (!alert) return null;

  return (
    <div 
      style={{
        position: 'fixed',
        bottom: '24px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 9999,
        maxWidth: '400px',
        width: '90%',
        background: '#ffffff',
        border: '1.5px solid #ef4444',
        borderRadius: '14px',
        boxShadow: '0 12px 30px rgba(239, 68, 68, 0.22), 0 4px 12px rgba(0, 0, 0, 0.08)',
        padding: '12px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        animation: 'slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div 
            style={{ 
              background: '#ef4444', 
              color: '#fff', 
              width: '28px', 
              height: '28px', 
              borderRadius: '8px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              boxShadow: '0 0 10px rgba(239, 68, 68, 0.4)'
            }}
          >
            <AlertOctagon size={16} />
          </div>
          <div>
            <span style={{ fontSize: '0.62rem', fontWeight: 800, color: '#dc2626', letterSpacing: '0.04em', lineHeight: 1 }}>
              ⚠ HAZARD DETECTED
            </span>
            <h4 style={{ fontSize: '0.88rem', color: '#0f172a', fontWeight: 800, margin: '2px 0 0', lineHeight: 1.2 }}>
              {alert.name || alert.type || 'Hazard Ahead'}
            </h4>
          </div>
        </div>

        <button 
          onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '2px' }}
          title="Dismiss"
        >
          <X size={16} />
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#fef2f2', padding: '6px 12px', borderRadius: '8px', fontSize: '0.76rem', color: '#991b1b', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#b91c1c' }}>DISTANCE: </span>
          <strong>{typeof alert.distance === 'number' ? (alert.distance > 1000 ? `${(alert.distance / 1000).toFixed(1)} km` : `${Math.round(alert.distance)} m`) : (alert.distanceText || alert.distance || '6 m')}</strong>
        </div>
        {alert.depth_cm !== undefined && alert.depth_cm !== null && (
          <div>
            <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#b91c1c' }}>DEPTH: </span>
            <strong>~{Math.round(alert.depth_cm)} cm</strong>
          </div>
        )}
        <div>
          <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#b91c1c' }}>SEVERITY: </span>
          <strong>{alert.severity || 'HIGH'}</strong>
        </div>
      </div>

      {alert.description && (
        <div style={{ fontSize: '0.76rem', color: '#475569', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {alert.description}
        </div>
      )}

      {onViewRoute && (
        <button
          onClick={onViewRoute}
          style={{
            background: '#0284c7',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '7px 12px',
            fontWeight: 700,
            fontSize: '0.78rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '5px'
          }}
        >
          <span>View On Map</span>
          <ArrowRight size={13} />
        </button>
      )}
    </div>
  );
};

export default HazardAlert;
