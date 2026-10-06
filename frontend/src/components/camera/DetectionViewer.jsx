import React, { useState } from 'react';
import { Camera, Eye, ChevronDown, ChevronUp } from 'lucide-react';

export const DetectionViewer = ({ detection = null }) => {
  const [collapsed, setCollapsed] = useState(true);

  const defaultDetection = detection || {
    hazardType: 'Pothole',
    confidence: 0.94,
    depth: 0.08,
    distance: 6.2
  };

  return (
    <div 
      style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        zIndex: 500,
        width: collapsed ? '170px' : '260px',
        background: 'rgba(15, 23, 42, 0.94)',
        backdropFilter: 'blur(8px)',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
        color: '#ffffff',
        overflow: 'hidden',
        transition: 'width 0.25s ease'
      }}
    >
      <div 
        onClick={() => setCollapsed(!collapsed)}
        style={{
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          background: 'rgba(255, 255, 255, 0.05)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Camera size={14} color="#06b6d4" />
          <span style={{ fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.04em' }}>
            YOLOv11 VISION
          </span>
        </div>
        {collapsed ? <ChevronDown size={14} color="#94a3b8" /> : <ChevronUp size={14} color="#94a3b8" />}
      </div>

      {!collapsed && (
        <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Simulated Compact Dashcam Frame */}
          <div 
            style={{ 
              position: 'relative', 
              width: '100%', 
              height: '110px', 
              borderRadius: '8px', 
              overflow: 'hidden',
              background: '#020617' 
            }}
          >
            <img 
              src="https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=400&q=80" 
              alt="Front ADAS Camera" 
              style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.85 }} 
            />

            {/* YOLO Bounding Box */}
            <div 
              style={{
                position: 'absolute',
                top: '42%',
                left: '32%',
                width: '36%',
                height: '38%',
                border: '2px solid #f59e0b',
                background: 'rgba(245, 158, 11, 0.15)',
                borderRadius: '4px'
              }}
            >
              <span 
                style={{ 
                  position: 'absolute', 
                  top: '-16px', 
                  left: 0, 
                  background: '#f59e0b', 
                  color: '#000', 
                  fontSize: '0.62rem', 
                  fontWeight: 900, 
                  padding: '1px 4px', 
                  borderRadius: '2px' 
                }}
              >
                POTHOLE 94%
              </span>
            </div>
          </div>

          <div style={{ fontSize: '0.74rem', color: '#cbd5e1', lineHeight: 1.4 }}>
            <div>Hazard: <strong style={{ color: '#f59e0b' }}>{defaultDetection.hazardType}</strong></div>
            <div>Confidence: <strong>{(defaultDetection.confidence * 100).toFixed(0)}%</strong></div>
            <div>Estimated Depth: <strong style={{ color: '#f87171' }}>{Math.round(defaultDetection.depth * 100)} cm</strong></div>
            <div>Distance: <strong>{defaultDetection.distance} m</strong></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DetectionViewer;
