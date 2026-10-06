import React from 'react';
import { ShieldCheck, AlertTriangle, CornerUpRight, X } from 'lucide-react';

export const RouteChangedNotification = ({
  reason = 'Hazard detected on current route.',
  oldETA = 25,
  newETA = 27,
  oldDistanceKm,
  newDistanceKm,
  onShift,
  onContinue,
  onAcceptDetour,
  onContinueOriginal,
  onClose
}) => {
  const handleShift = onShift || onAcceptDetour;
  const handleContinue = onContinue || onContinueOriginal;

  return (
    <div 
      style={{
        position: 'fixed',
        top: '18px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 9999,
        maxWidth: '420px',
        width: '90%',
        background: '#ffffff',
        border: '1.5px solid #10b981',
        borderRadius: '14px',
        boxShadow: '0 12px 30px rgba(16, 185, 129, 0.22), 0 4px 12px rgba(0, 0, 0, 0.08)',
        padding: '12px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        animation: 'slideDown 0.25s cubic-bezier(0.16, 1, 0.3, 1)'
      }}
    >
      {/* Compact Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div 
            style={{ 
              background: '#10b981', 
              color: '#fff', 
              width: '28px', 
              height: '28px', 
              borderRadius: '8px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            <ShieldCheck size={17} />
          </div>
          <div>
            <div style={{ fontSize: '0.62rem', fontWeight: 800, color: '#059669', letterSpacing: '0.04em', lineHeight: 1 }}>
              ROUTE SHIFTED
            </div>
            <h4 style={{ fontSize: '0.88rem', color: '#0f172a', fontWeight: 800, margin: '2px 0 0', lineHeight: 1.2 }}>
              Hazard Ahead • Shortest Bypass
            </h4>
          </div>
        </div>

        {onClose && (
          <button 
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '2px' }}
            title="Dismiss"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Reason line */}
      <div style={{ 
        fontSize: '0.78rem', 
        color: '#dc2626', 
        background: '#fef2f2', 
        border: '1px solid #fee2e2', 
        borderRadius: '8px', 
        padding: '5px 10px',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontWeight: 600
      }}>
        <AlertTriangle size={13} style={{ flexShrink: 0 }} />
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{reason}</span>
      </div>

      {/* Inline ETA Comparison */}
      <div 
        style={{ 
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#f8fafc', 
          padding: '6px 12px', 
          borderRadius: '8px',
          border: '1px solid #e2e8f0',
          fontSize: '0.76rem'
        }}
      >
        <div>
          <span style={{ color: '#64748b', fontSize: '0.65rem', fontWeight: 700, display: 'block', textTransform: 'uppercase' }}>Original</span>
          <span style={{ fontWeight: 800, color: '#dc2626' }}>{oldETA} min</span>
          {oldDistanceKm !== undefined && <span style={{ color: '#64748b', fontSize: '0.7rem' }}> ({oldDistanceKm} km)</span>}
        </div>

        <div style={{ color: '#94a3b8', fontWeight: 800 }}>➔</div>

        <div style={{ textAlign: 'right' }}>
          <span style={{ color: '#059669', fontSize: '0.65rem', fontWeight: 800, display: 'block', textTransform: 'uppercase' }}>Bypass (Safe)</span>
          <span style={{ fontWeight: 800, color: '#059669' }}>{newETA} min</span>
          {newDistanceKm !== undefined && <span style={{ color: '#059669', fontSize: '0.7rem' }}> ({newDistanceKm} km)</span>}
        </div>
      </div>

      {/* Compact Action Buttons: Shift vs Continue */}
      <div style={{ display: 'flex', gap: '8px', marginTop: '2px' }}>
        <button
          onClick={handleShift}
          style={{
            flex: 1,
            background: '#10b981',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            padding: '8px 12px',
            fontWeight: 800,
            fontSize: '0.82rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '5px',
            boxShadow: '0 2px 8px rgba(16, 185, 129, 0.35)',
            transition: 'all 0.15s ease'
          }}
          title="Shift to shortest bypass route"
        >
          <CornerUpRight size={14} />
          <span>Shift</span>
        </button>

        <button
          onClick={handleContinue}
          style={{
            flex: 1,
            background: '#ffffff',
            color: '#475569',
            border: '1px solid #cbd5e1',
            borderRadius: '8px',
            padding: '8px 12px',
            fontWeight: 700,
            fontSize: '0.82rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.15s ease'
          }}
          title="Continue on original route"
        >
          <span>Continue</span>
        </button>
      </div>
    </div>
  );
};

export default RouteChangedNotification;
