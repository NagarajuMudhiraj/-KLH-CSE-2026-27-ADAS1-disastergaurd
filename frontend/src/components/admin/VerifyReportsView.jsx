import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { hazardService } from '../../services/hazardService';
import { 
  Check, 
  X, 
  ShieldCheck, 
  Clock, 
  MapPin, 
  AlertTriangle, 
  User, 
  Camera,
  RefreshCw,
  Loader2,
  ExternalLink,
  Eye,
  SlidersHorizontal,
  LayoutGrid,
  Table as TableIcon,
  ZoomIn,
  Flame,
  Droplets,
  Wind,
  Info,
  Radio,
  FileDown
} from 'lucide-react';
import pdfReportService from '../../services/pdfReportService';

/**
 * Normalizes authentic image properties from real driver detections and dashcam frames.
 * Returns null if no authentic photo was provided by the driver.
 */
export const getHazardImage = (h) => {
  if (!h) return null;
  const raw = h.image_url || h.imageUrl || h.annotated_image_url || h.image || h.photo || h.photo_url || h.snapshot || h.evidence_image || h.thumbnail;
  if (raw && typeof raw === 'string' && raw.trim().length > 0) {
    if (raw.startsWith('http') || raw.startsWith('data:') || raw.startsWith('/')) {
      return raw;
    }
    return `data:image/jpeg;base64,${raw}`;
  }
  if (h.image_base64 && typeof h.image_base64 === 'string' && h.image_base64.trim().length > 0) {
    return h.image_base64.startsWith('data:') ? h.image_base64 : `data:image/jpeg;base64,${h.image_base64}`;
  }
  // Authentic: return null if no photo attached by driver (do not fake images)
  return null;
};

export const VerifyReportsView = ({ onRefresh }) => {
  const [reports, setReports] = useState([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [processingId, setProcessingId] = useState(null);
  const [feedbackNotice, setFeedbackNotice] = useState(null);
  const [activeTab, setActiveTab] = useState('ALL'); // ALL, AI, USER
  const [viewMode, setViewMode] = useState('CARDS'); // 'CARDS' or 'TABLE'
  const [selectedReport, setSelectedReport] = useState(null);
  const [adminNote, setAdminNote] = useState('');

  // Fetch real-time pending reports from backend (strictly authentic driver-detected events)
  const fetchPendingReports = async () => {
    setLoadingReports(true);
    try {
      const data = await api.getAdminReports();
      if (Array.isArray(data)) {
        // Exclude any legacy mock items and pedestrians
        const authentic = data.filter((h) => 
          !String(h.id || h._id || '').startsWith('hz_rep_') &&
          !['person', 'pedestrian'].includes((h.type || h.disasterType || h.name || '').toLowerCase().trim())
        );
        setReports(authentic);
      } else {
        setReports([]);
      }
    } catch (err) {
      console.warn('Could not fetch admin reports queue:', err);
      setReports([]);
    } finally {
      setLoadingReports(false);
    }
  };

  useEffect(() => {
    fetchPendingReports();

    // Listen to real-time WebSocket events broadcasted by drivers
    const cleanupWs = hazardService.connectHazardWebSocket((event) => {
      if (event.event === 'NEW_DISASTER_DETECTED' || event.event === 'HAZARD_REPORTED' || event.event === 'HAZARD_DETECTED') {
        const newHazard = event.data || event.hazard;
        if (newHazard && !String(newHazard.id || newHazard._id || '').startsWith('hz_rep_')) {
          setReports((prev) => {
            const id = newHazard.id || newHazard._id;
            if (prev.some((r) => (r.id || r._id) === id)) return prev;
            return [newHazard, ...prev];
          });
          setFeedbackNotice(`🚨 New live detection received from driver: ${newHazard.name || newHazard.type || 'Hazard'}!`);
        }
      }
    });

    return () => cleanupWs();
  }, []);

  // 1. Filter pending reports (strictly real-time, non-demo, exclude pedestrians)
  const filteredReports = reports.filter((h) => {
    // Exclude mock demo IDs
    if (String(h.id || h._id || '').startsWith('hz_rep_')) return false;

    // EXCLUDE PEDESTRIANS: Pedestrians are normal urban entities, not road hazards
    const rawType = (h.type || h.disasterType || h.name || '').toLowerCase().trim();
    if (rawType === 'person' || rawType === 'pedestrian') return false;

    const isVerified = h.verified === true && (h.status || '').toUpperCase() === 'ACTIVE';
    if (isVerified) return false;
    const statusUpper = (h.status || '').toUpperCase();
    if (statusUpper === 'REJECTED' || statusUpper === 'RESOLVED') return false;

    const src = (h.source || (h.reported_by?.includes('YOLO') || h.detectedBy?.includes('YOLO') || h.detectedBy?.includes('Dashcam') ? 'AI' : 'USER')).toUpperCase();
    if (activeTab === 'AI') return src === 'AI';
    if (activeTab === 'USER') return src === 'USER';
    return true;
  });

  // 2. LOCATION & SAME-LABEL DEDUPLICATION:
  // At the same location (~50m radius), take ONLY ONE for the SAME hazard label!
  // Different hazards at the same location are allowed!
  const pendingReports = [];
  for (const rep of filteredReports) {
    const lat = rep.latitude !== undefined ? rep.latitude : rep.lat;
    const lng = rep.longitude !== undefined ? rep.longitude : rep.lng;
    const repType = (rep.type || rep.disasterType || rep.name || '').toLowerCase().trim();

    const hasDuplicateAtLocation = pendingReports.some((existing) => {
      const eLat = existing.latitude !== undefined ? existing.latitude : existing.lat;
      const eLng = existing.longitude !== undefined ? existing.longitude : existing.lng;
      if (lat == null || lng == null || eLat == null || eLng == null) return false;

      // Check ~50 meter spatial proximity
      const isSameLocation = Math.abs(eLat - lat) <= 0.00045 && Math.abs(eLng - lng) <= 0.00045;
      if (!isSameLocation) return false;

      // Check if SAME hazard label
      const eType = (existing.type || existing.disasterType || existing.name || '').toLowerCase().trim();
      const isSameLabel = repType === eType ||
        repType.includes(eType) || eType.includes(repType) ||
        (repType.includes('flood') && eType.includes('flood')) ||
        (repType.includes('fire') && eType.includes('fire')) ||
        (repType.includes('smoke') && eType.includes('smoke')) ||
        (repType.includes('damage') && eType.includes('damage')) ||
        (repType.includes('pothole') && eType.includes('pothole')) ||
        (repType.includes('landslide') && eType.includes('landslide')) ||
        (repType.includes('accident') && eType.includes('accident'));

      return isSameLabel;
    });

    if (!hasDuplicateAtLocation) {
      pendingReports.push(rep);
    }
  }

  const handleVerify = async (hazardId, action, note = '') => {
    setProcessingId(hazardId);
    try {
      await api.verifyHazard(hazardId, action, note || `Admin verification: ${action}`);
      setFeedbackNotice(
        `Hazard #${String(hazardId).slice(-6)} was successfully ${
          action === 'approve' ? 'VERIFIED and published live to vehicular navigation corridors!' : 'REJECTED as false alarm.'
        }`
      );
      
      // Update local state immediately
      setReports((prev) => prev.filter((r) => (r.id || r._id) !== hazardId));
      if (selectedReport && (selectedReport.id || selectedReport._id) === hazardId) {
        setSelectedReport(null);
        setAdminNote('');
      }

      if (onRefresh) onRefresh();
    } catch (err) {
      alert(`Action failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', fontFamily: 'inherit' }}>
      
      {/* Header and Filter Controls */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '22px', 
        flexWrap: 'wrap', 
        gap: '14px',
        background: 'rgba(255, 255, 255, 0.42)',
        backdropFilter: 'blur(18px) saturate(160%)',
        WebkitBackdropFilter: 'blur(18px) saturate(160%)',
        padding: '18px 22px',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.55)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.04), inset 0 0 0 1px rgba(255, 255, 255, 0.4)'
      }}>
        <div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 900, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldCheck size={28} color="#0284c7" />
            Live Driver Detections & Hazard Verification Queue
          </h1>
          <p style={{ fontSize: '0.86rem', color: '#64748b', margin: '4px 0 0' }}>
            Review real-time hazard detections captured by onboard YOLOv11s dashcams and citizen driver uploads before broadcasting to route corridors.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Source Filter Tabs */}
          <div style={{ display: 'flex', background: '#f1f5f9', padding: '4px', borderRadius: '10px', gap: '4px' }}>
            <button
              onClick={() => setActiveTab('ALL')}
              style={{
                border: 'none',
                background: activeTab === 'ALL' ? '#ffffff' : 'transparent',
                color: activeTab === 'ALL' ? '#0f172a' : '#64748b',
                fontWeight: 700,
                fontSize: '0.78rem',
                padding: '6px 14px',
                borderRadius: '8px',
                cursor: 'pointer',
                boxShadow: activeTab === 'ALL' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none'
              }}
            >
              All Real-Time ({pendingReports.length})
            </button>
            <button
              onClick={() => setActiveTab('AI')}
              style={{
                border: 'none',
                background: activeTab === 'AI' ? '#ffffff' : 'transparent',
                color: activeTab === 'AI' ? '#0284c7' : '#64748b',
                fontWeight: 700,
                fontSize: '0.78rem',
                padding: '6px 14px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                boxShadow: activeTab === 'AI' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none'
              }}
            >
              <Camera size={13} /> Dashcam AI
            </button>
            <button
              onClick={() => setActiveTab('USER')}
              style={{
                border: 'none',
                background: activeTab === 'USER' ? '#ffffff' : 'transparent',
                color: activeTab === 'USER' ? '#b45309' : '#64748b',
                fontWeight: 700,
                fontSize: '0.78rem',
                padding: '6px 14px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                boxShadow: activeTab === 'USER' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none'
              }}
            >
              <User size={13} /> Driver Reports
            </button>
          </div>

          {/* View Mode Toggle: Cards vs Table */}
          <div style={{ display: 'flex', background: '#f1f5f9', padding: '4px', borderRadius: '10px', gap: '4px' }}>
            <button
              onClick={() => setViewMode('CARDS')}
              title="Card Grid Mode (Visual Photo Inspection)"
              style={{
                border: 'none',
                background: viewMode === 'CARDS' ? '#ffffff' : 'transparent',
                color: viewMode === 'CARDS' ? '#0284c7' : '#64748b',
                padding: '6px 10px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.78rem',
                fontWeight: 700,
                boxShadow: viewMode === 'CARDS' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none'
              }}
            >
              <LayoutGrid size={14} /> Cards
            </button>
            <button
              onClick={() => setViewMode('TABLE')}
              title="Compact Table Mode"
              style={{
                border: 'none',
                background: viewMode === 'TABLE' ? '#ffffff' : 'transparent',
                color: viewMode === 'TABLE' ? '#0284c7' : '#64748b',
                padding: '6px 10px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.78rem',
                fontWeight: 700,
                boxShadow: viewMode === 'TABLE' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none'
              }}
            >
              <TableIcon size={14} /> Table
            </button>
          </div>

          <button 
            onClick={() => pdfReportService.generateComprehensiveDisasterReport({ hazards: pendingReports })} 
            className="btn btn-secondary" 
            style={{ padding: '8px 14px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            title="Export all unverified/pending reports queue to PDF"
          >
            <FileDown size={14} /> Export Queue (PDF)
          </button>

          <button 
            onClick={() => { fetchPendingReports(); if (onRefresh) onRefresh(); }} 
            className="btn btn-secondary" 
            disabled={loadingReports}
            style={{ padding: '8px 14px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} className={loadingReports ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {feedbackNotice && (
        <div style={{
          background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '12px',
          padding: '12px 18px', marginBottom: '18px', fontSize: '0.86rem', color: '#166534',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          boxShadow: '0 2px 8px rgba(22, 101, 52, 0.08)'
        }}>
          <span style={{ fontWeight: 600 }}>{feedbackNotice}</span>
          <button onClick={() => setFeedbackNotice(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#166534' }}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Main Content Area */}
      {pendingReports.length === 0 ? (
        <div style={{
          background: 'rgba(255, 255, 255, 0.4)',
          backdropFilter: 'blur(18px) saturate(160%)',
          WebkitBackdropFilter: 'blur(18px) saturate(160%)',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.55)',
          padding: '50px 24px',
          textAlign: 'center',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.03), inset 0 0 0 1px rgba(255, 255, 255, 0.4)'
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'rgba(2, 132, 199, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px'
          }}>
            <Radio size={32} color="#0284c7" className="animate-pulse" />
          </div>

          <h3 style={{ fontSize: '1.25rem', color: '#0f172a', fontWeight: 800, margin: 0 }}>
            Real-Time Vehicle Network Active & Listening
          </h3>
          <p style={{ fontSize: '0.9rem', color: '#64748b', maxWidth: '520px', margin: '8px auto 20px', lineHeight: 1.5 }}>
            No unverified hazards in queue. When a driver encounters a hazard or the onboard YOLOv11s camera detects floodwater, fire, or road damage, the live detection with photo evidence will appear here immediately via WebSocket.
          </p>

          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#f8fafc', padding: '8px 16px', borderRadius: '10px', border: '1px solid #e2e8f0', fontSize: '0.82rem', color: '#475569' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
            WebSocket Live Telemetry Listener: <strong>Connected</strong>
          </div>
        </div>
      ) : viewMode === 'CARDS' ? (
        
        /* ========================================================= */
        /* 1. REAL-TIME VISUAL CARDS GRID MODE                       */
        /* ========================================================= */
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
          gap: '20px'
        }}>
          {pendingReports.map((h, idx) => {
            const id = h._id || h.id || `rep_${idx}`;
            const isBusy = processingId === id;
            const isAI = (h.source || '').toUpperCase() === 'AI' || (h.reported_by?.includes('YOLO')) || (h.detectedBy?.includes('Dashcam'));
            const imgSrc = getHazardImage(h);
            const latVal = h.latitude !== undefined ? h.latitude : h.lat;
            const lngVal = h.longitude !== undefined ? h.longitude : h.lng;
            const hazardTitle = h.name || h.disasterType || h.type || 'Hazard';
            const severityUpper = (h.severity || 'HIGH').toUpperCase();

            return (
              <div 
                key={id}
                style={{
                  background: 'rgba(255, 255, 255, 0.42)',
                  backdropFilter: 'blur(18px) saturate(160%)',
                  WebkitBackdropFilter: 'blur(18px) saturate(160%)',
                  borderRadius: '16px',
                  border: '1px solid rgba(255, 255, 255, 0.55)',
                  overflow: 'hidden',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.05), inset 0 0 0 1px rgba(255, 255, 255, 0.4)',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease'
                }}
              >
                {/* Visual Evidence Banner */}
                <div 
                  style={{
                    position: 'relative',
                    width: '100%',
                    height: '210px',
                    background: '#090d16',
                    cursor: imgSrc ? 'pointer' : 'default',
                    overflow: 'hidden'
                  }}
                  onClick={() => imgSrc && setSelectedReport(h)}
                  title={imgSrc ? "Click to inspect driver photo evidence in high resolution" : "Driver reported via GPS without photo"}
                >
                  {imgSrc ? (
                    <img 
                      src={imgSrc} 
                      alt={hazardTitle}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        transition: 'transform 0.3s ease'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.04)'}
                      onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1.0)'}
                    />
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8', flexDirection: 'column', gap: '8px', background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)' }}>
                      <Radio size={36} color="#38bdf8" style={{ opacity: 0.8 }} />
                      <span style={{ fontSize: '0.84rem', fontWeight: 700, color: '#f8fafc' }}>
                        Driver GPS Hazard Alert
                      </span>
                      <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                        No photo attached • Live GPS coordinates verified
                      </span>
                    </div>
                  )}

                  {/* Overlay Badges */}
                  <div style={{
                    position: 'absolute',
                    top: '12px',
                    left: '12px',
                    display: 'flex',
                    gap: '6px'
                  }}>
                    {isAI ? (
                      <span style={{
                        background: 'rgba(29, 78, 216, 0.9)',
                        backdropFilter: 'blur(6px)',
                        color: '#ffffff',
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        padding: '4px 8px',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        boxShadow: '0 2px 6px rgba(0,0,0,0.3)'
                      }}>
                        <Camera size={11} /> Driver Dashcam AI
                      </span>
                    ) : (
                      <span style={{
                        background: 'rgba(180, 83, 9, 0.9)',
                        backdropFilter: 'blur(6px)',
                        color: '#ffffff',
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        padding: '4px 8px',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        boxShadow: '0 2px 6px rgba(0,0,0,0.3)'
                      }}>
                        <User size={11} /> Driver Report
                      </span>
                    )}

                    <span style={{
                      background: severityUpper === 'CRITICAL' ? 'rgba(220, 38, 38, 0.9)' : 
                                  severityUpper === 'HIGH' ? 'rgba(217, 119, 6, 0.9)' : 'rgba(16, 185, 129, 0.9)',
                      backdropFilter: 'blur(6px)',
                      color: '#ffffff',
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      padding: '4px 8px',
                      borderRadius: '6px',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.3)'
                    }}>
                      {severityUpper}
                    </span>
                  </div>

                  {/* Zoom Action Icon Overlay */}
                  {imgSrc && (
                    <div style={{
                      position: 'absolute',
                      bottom: '10px',
                      right: '10px',
                      background: 'rgba(15, 23, 42, 0.85)',
                      backdropFilter: 'blur(6px)',
                      color: '#ffffff',
                      padding: '4px 10px',
                      borderRadius: '8px',
                      fontSize: '0.74rem',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      border: '1px solid rgba(255,255,255,0.15)'
                    }}>
                      <ZoomIn size={13} /> Inspect Photo Evidence
                    </div>
                  )}
                </div>

                {/* Card Body */}
                <div style={{ padding: '18px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <div>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                        {hazardTitle}
                      </h3>
                      <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#64748b' }}>
                        ID: #{String(id).slice(-8)}
                      </span>
                    </div>

                    {h.confidence && (
                      <span style={{
                        background: '#eff6ff',
                        color: '#0284c7',
                        border: '1px solid #bae6fd',
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        padding: '3px 8px',
                        borderRadius: '6px'
                      }}>
                        {Math.round(h.confidence * 100)}% Conf
                      </span>
                    )}
                  </div>

                  {/* Physical Telemetry / Water Depth */}
                  {(h.depth_cm || h.distance_m) && (
                    <div style={{ display: 'flex', gap: '10px', marginBottom: '12px', background: '#f8fafc', padding: '8px 12px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
                      {h.depth_cm && (
                        <div style={{ fontSize: '0.78rem', color: '#0369a1', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Droplets size={13} /> Water Depth: ~{h.depth_cm} cm
                        </div>
                      )}
                      {h.distance_m && (
                        <div style={{ fontSize: '0.78rem', color: '#475569', fontWeight: 600 }}>
                          Distance: ~{h.distance_m} m
                        </div>
                      )}
                    </div>
                  )}

                  {/* Description */}
                  <p style={{ fontSize: '0.84rem', color: '#475569', margin: '0 0 14px', lineHeight: 1.4, flex: 1 }}>
                    {h.description || 'Observed hazardous condition flagged by vehicle in transit.'}
                  </p>

                  {/* Location & Time */}
                  <div style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#334155', fontWeight: 600 }}>
                      <MapPin size={13} color="#0284c7" />
                      <span>{h.address || 'Live Corridor GPS Location'}</span>
                    </div>
                    {latVal && lngVal && (
                      <a 
                        href={`https://www.google.com/maps?q=${latVal},${lngVal}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: '0.72rem', color: '#0284c7', display: 'inline-flex', alignItems: 'center', gap: '3px', textDecoration: 'none' }}
                      >
                        Coordinates: {Number(latVal).toFixed(4)}, {Number(lngVal).toFixed(4)} <ExternalLink size={10} />
                      </a>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                      <Clock size={12} />
                      <span>Reported: {new Date(h.timestamp || h.createdAt || Date.now()).toLocaleTimeString()}</span>
                      {h.reported_by && (
                        <span style={{ color: '#64748b', marginLeft: '6px' }}>by {h.reported_by}</span>
                      )}
                    </div>
                  </div>

                  {/* Verification Buttons */}
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      onClick={() => handleVerify(id, 'approve')}
                      disabled={isBusy}
                      style={{
                        flex: 1,
                        background: '#16a34a',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '10px',
                        padding: '10px',
                        fontSize: '0.82rem',
                        fontWeight: 800,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        boxShadow: '0 2px 8px rgba(22, 163, 74, 0.25)',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.background = '#15803d'}
                      onMouseOut={(e) => e.currentTarget.style.background = '#16a34a'}
                      title="Verify hazard and broadcast immediate detours to approaching drivers"
                    >
                      {isBusy ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} 
                      VERIFY & BROADCAST
                    </button>

                    <button
                      onClick={() => handleVerify(id, 'reject')}
                      disabled={isBusy}
                      style={{
                        background: '#fee2e2',
                        color: '#dc2626',
                        border: '1px solid #fca5a5',
                        borderRadius: '10px',
                        padding: '10px 14px',
                        fontSize: '0.82rem',
                        fontWeight: 800,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.background = '#fecaca'}
                      onMouseOut={(e) => e.currentTarget.style.background = '#fee2e2'}
                      title="Reject as false alarm"
                    >
                      <X size={14} /> REJECT
                    </button>

                    <button
                      onClick={() => pdfReportService.generateIndividualIncidentDossier({ hazard: h })}
                      style={{
                        background: 'rgba(2, 132, 199, 0.1)',
                        color: '#0284c7',
                        border: '1px solid #bae6fd',
                        borderRadius: '10px',
                        padding: '10px 12px',
                        fontSize: '0.82rem',
                        fontWeight: 800,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.background = '#e0f2fe'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'rgba(2, 132, 199, 0.1)'}
                      title="Export single incident PDF report with photo evidence"
                    >
                      <FileDown size={14} /> PDF
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (

        /* ========================================================= */
        /* 2. COMPACT TABLE MODE                                     */
        /* ========================================================= */
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div className="hud-table-wrapper">
            <table className="hud-table">
              <thead>
                <tr>
                  <th>Report ID</th>
                  <th>Visual Evidence</th>
                  <th>Source</th>
                  <th>Hazard Category</th>
                  <th>Severity</th>
                  <th>Location / Coordinates</th>
                  <th>Observed At</th>
                  <th>Status</th>
                  <th>Verification Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingReports.map((h, idx) => {
                  const id = h._id || h.id || `rep_${idx}`;
                  const isBusy = processingId === id;
                  const isAI = (h.source || '').toUpperCase() === 'AI' || (h.reported_by?.includes('YOLO')) || (h.detectedBy?.includes('Dashcam'));
                  const imgSrc = getHazardImage(h);
                  const latVal = h.latitude !== undefined ? h.latitude : h.lat;
                  const lngVal = h.longitude !== undefined ? h.longitude : h.lng;

                  return (
                    <tr key={id}>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#0284c7' }}>
                        #{String(id).slice(-6)}
                      </td>

                      {/* Visual Evidence Thumbnail */}
                      <td>
                        {imgSrc ? (
                          <div
                            onClick={() => setSelectedReport(h)}
                            style={{
                              width: '74px',
                              height: '52px',
                              borderRadius: '8px',
                              overflow: 'hidden',
                              cursor: 'pointer',
                              border: '2px solid #cbd5e1',
                              position: 'relative',
                              boxShadow: '0 2px 6px rgba(0,0,0,0.08)'
                            }}
                            title="Click to inspect full photo evidence"
                          >
                            <img src={imgSrc} alt="Hazard Evidence" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            <div style={{
                              position: 'absolute',
                              bottom: 0,
                              right: 0,
                              background: 'rgba(0,0,0,0.6)',
                              color: '#fff',
                              padding: '2px 4px',
                              borderRadius: '4px 0 0 0'
                            }}>
                              <ZoomIn size={10} />
                            </div>
                          </div>
                        ) : (
                          <span style={{ fontSize: '0.74rem', color: '#94a3b8', fontStyle: 'italic' }}>
                            GPS Only (No Photo)
                          </span>
                        )}
                      </td>

                      {/* Source */}
                      <td>
                        {isAI ? (
                          <span style={{
                            background: '#eff6ff',
                            color: '#1d4ed8',
                            border: '1px solid #bfdbfe',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '0.72rem',
                            fontWeight: 800,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <Camera size={12} /> Dashcam AI
                          </span>
                        ) : (
                          <span style={{
                            background: '#fffbeb',
                            color: '#b45309',
                            border: '1px solid #fde68a',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '0.72rem',
                            fontWeight: 800,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <User size={12} /> Driver Report
                          </span>
                        )}
                      </td>

                      {/* Hazard Type & Confidence */}
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          <strong style={{ color: '#0f172a', fontSize: '0.88rem' }}>
                            {h.name || h.disasterType || h.type || 'Hazard'}
                          </strong>
                          <div style={{ fontSize: '0.74rem', color: '#64748b', display: 'flex', gap: '8px' }}>
                            {h.confidence && (
                              <span style={{ color: '#0284c7', fontWeight: 700 }}>
                                {Math.round(h.confidence * 100)}% Conf
                              </span>
                            )}
                            {h.depth_cm && (
                              <span style={{ color: '#d97706', fontWeight: 700 }}>
                                ~{h.depth_cm} cm
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Severity */}
                      <td>
                        <span className={`badge ${
                          (h.severity || '').toUpperCase() === 'CRITICAL' ? 'badge-danger' : 
                          (h.severity || '').toUpperCase() === 'HIGH' ? 'badge-warning' : 'badge-safe'
                        }`}>
                          {h.severity || 'HIGH'}
                        </span>
                      </td>

                      {/* Location */}
                      <td style={{ fontSize: '0.8rem', color: '#334155' }}>
                        <div>{h.address || 'Corridor GPS'}</div>
                        {latVal && lngVal && (
                          <a
                            href={`https://www.google.com/maps?q=${latVal},${lngVal}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              fontSize: '0.72rem',
                              color: '#0284c7',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '3px',
                              marginTop: '2px'
                            }}
                          >
                            <MapPin size={11} /> {Number(latVal).toFixed(4)}, {Number(lngVal).toFixed(4)} <ExternalLink size={10} />
                          </a>
                        )}
                      </td>

                      {/* Time */}
                      <td style={{ fontSize: '0.76rem', color: '#64748b' }}>
                        {new Date(h.timestamp || h.createdAt || Date.now()).toLocaleTimeString()}
                      </td>

                      {/* Status */}
                      <td>
                        <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>
                          Awaiting Review
                        </span>
                      </td>

                      {/* Action buttons */}
                      <td>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            onClick={() => handleVerify(id, 'approve')}
                            className="btn btn-secondary"
                            disabled={isBusy}
                            style={{
                              padding: '6px 12px',
                              fontSize: '0.78rem',
                              color: '#15803d',
                              fontWeight: 800,
                              background: '#f0fdf4',
                              border: '1px solid #86efac'
                            }}
                            title="Verify and broadcast live"
                          >
                            {isBusy ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />} VERIFY
                          </button>

                          <button
                            onClick={() => handleVerify(id, 'reject')}
                            className="btn btn-secondary"
                            disabled={isBusy}
                            style={{
                              padding: '6px 12px',
                              fontSize: '0.78rem',
                              color: '#dc2626',
                              fontWeight: 800,
                              background: '#fef2f2',
                              border: '1px solid #fca5a5'
                            }}
                            title="Reject hazard as false alarm"
                          >
                            <X size={13} /> REJECT
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 3. FULL-SCREEN EVIDENCE INSPECTION & MODERATION MODAL     */}
      {/* ========================================================= */}
      {selectedReport && (
        <div
          onClick={() => setSelectedReport(null)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            zIndex: 9999,
            background: 'rgba(9, 13, 22, 0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: '920px',
              width: '100%',
              background: '#0f172a',
              borderRadius: '20px',
              overflow: 'hidden',
              boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.7)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              flexDirection: 'column',
              maxHeight: '90vh'
            }}
          >
            {/* Modal Header */}
            <div style={{
              padding: '16px 22px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              background: '#1e293b'
            }}>
              <div>
                <span style={{ color: '#38bdf8', fontSize: '0.78rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Authentic Driver Evidence Inspection
                </span>
                <h2 style={{ color: '#ffffff', fontSize: '1.25rem', fontWeight: 800, margin: '2px 0 0' }}>
                  {selectedReport.name || selectedReport.disasterType || selectedReport.type || 'Hazard'} Photo Snapshot
                </h2>
              </div>
              <button 
                onClick={() => setSelectedReport(null)} 
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: '#ffffff', cursor: 'pointer', borderRadius: '8px', padding: '6px' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Content: Split Image & Telemetry */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1.4fr) minmax(0, 1fr)',
              overflowY: 'auto',
              flex: 1
            }}>
              {/* Left: High-Resolution Photo */}
              <div style={{
                background: '#020617',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
                borderRight: '1px solid rgba(255, 255, 255, 0.08)'
              }}>
                {getHazardImage(selectedReport) ? (
                  <img 
                    src={getHazardImage(selectedReport)} 
                    alt="Driver Photo Evidence"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '480px',
                      borderRadius: '12px',
                      objectFit: 'contain',
                      boxShadow: '0 8px 30px rgba(0,0,0,0.5)'
                    }}
                  />
                ) : (
                  <div style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                    <Radio size={48} color="#38bdf8" style={{ margin: '0 auto 12px' }} />
                    <p style={{ color: '#ffffff', fontWeight: 700 }}>Driver Submitted via GPS Only</p>
                    <p style={{ fontSize: '0.8rem' }}>No camera snapshot was attached to this report.</p>
                  </div>
                )}
              </div>

              {/* Right: Telemetry & Verification Actions */}
              <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '14px', background: '#0f172a' }}>
                <div>
                  <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                    Hazard Metadata
                  </span>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '6px', flexWrap: 'wrap' }}>
                    <span style={{
                      background: (selectedReport.severity || '').toUpperCase() === 'CRITICAL' ? '#dc2626' : '#d97706',
                      color: '#fff',
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      padding: '4px 10px',
                      borderRadius: '6px'
                    }}>
                      Severity: {(selectedReport.severity || 'HIGH').toUpperCase()}
                    </span>

                    {selectedReport.confidence && (
                      <span style={{ background: '#0284c7', color: '#fff', fontSize: '0.75rem', fontWeight: 800, padding: '4px 10px', borderRadius: '6px' }}>
                        Confidence: {Math.round(selectedReport.confidence * 100)}%
                      </span>
                    )}
                  </div>
                </div>

                {/* Physical metrics */}
                {(selectedReport.depth_cm || selectedReport.distance_m) && (
                  <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                    {selectedReport.depth_cm && (
                      <div style={{ color: '#38bdf8', fontSize: '0.86rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Droplets size={16} /> Estimated Inundation Depth: {selectedReport.depth_cm} cm
                      </div>
                    )}
                    {selectedReport.distance_m && (
                      <div style={{ color: '#cbd5e1', fontSize: '0.82rem', marginTop: '4px' }}>
                        Proximity to Vehicle: ~{selectedReport.distance_m} meters
                      </div>
                    )}
                  </div>
                )}

                {/* Description */}
                <div>
                  <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                    Driver Observation Description
                  </span>
                  <p style={{ color: '#e2e8f0', fontSize: '0.88rem', margin: '4px 0 0', lineHeight: 1.4 }}>
                    {selectedReport.description || 'Live driver observation flagged for moderation.'}
                  </p>
                </div>

                {/* Location */}
                <div>
                  <span style={{ fontSize: '0.74rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>
                    Corridor GPS Position
                  </span>
                  <div style={{ color: '#ffffff', fontSize: '0.88rem', fontWeight: 600, marginTop: '2px' }}>
                    {selectedReport.address || 'Corridor GPS Location'}
                  </div>
                  {selectedReport.latitude && selectedReport.longitude && (
                    <a
                      href={`https://www.google.com/maps?q=${selectedReport.latitude},${selectedReport.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#38bdf8', fontSize: '0.78rem', display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '4px', textDecoration: 'none' }}
                    >
                      <MapPin size={12} /> {Number(selectedReport.latitude).toFixed(4)}, {Number(selectedReport.longitude).toFixed(4)} (Open Google Maps)
                    </a>
                  )}
                </div>

                {/* Optional Admin Note */}
                <div style={{ marginTop: 'auto', paddingTop: '10px' }}>
                  <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700, display: 'block', marginBottom: '4px' }}>
                    Optional Verification Notes
                  </label>
                  <input
                    type="text"
                    value={adminNote}
                    onChange={(e) => setAdminNote(e.target.value)}
                    placeholder="e.g., Confirmed by traffic police, detour active"
                    style={{
                      width: '100%',
                      background: 'rgba(255,255,255,0.06)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      borderRadius: '8px',
                      padding: '8px 12px',
                      color: '#ffffff',
                      fontSize: '0.82rem',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                {/* Modal Verification Actions */}
                <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                  <button
                    onClick={() => handleVerify(selectedReport.id || selectedReport._id, 'approve', adminNote)}
                    disabled={processingId === (selectedReport.id || selectedReport._id)}
                    style={{
                      flex: 1,
                      background: '#16a34a',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '10px',
                      padding: '12px',
                      fontSize: '0.88rem',
                      fontWeight: 800,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      boxShadow: '0 4px 14px rgba(22, 163, 74, 0.4)'
                    }}
                  >
                    {processingId === (selectedReport.id || selectedReport._id) ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Check size={16} />
                    )}
                    APPROVE & BROADCAST
                  </button>

                  <button
                    onClick={() => handleVerify(selectedReport.id || selectedReport._id, 'reject', adminNote)}
                    disabled={processingId === (selectedReport.id || selectedReport._id)}
                    style={{
                      background: 'rgba(239, 68, 68, 0.15)',
                      color: '#f87171',
                      border: '1px solid #ef4444',
                      borderRadius: '10px',
                      padding: '12px 18px',
                      fontSize: '0.88rem',
                      fontWeight: 800,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px'
                    }}
                  >
                    <X size={16} /> REJECT
                  </button>

                  <button
                    onClick={() => pdfReportService.generateIndividualIncidentDossier({ hazard: selectedReport })}
                    style={{
                      background: 'rgba(2, 132, 199, 0.15)',
                      color: '#38bdf8',
                      border: '1px solid #0284c7',
                      borderRadius: '10px',
                      padding: '12px 16px',
                      fontSize: '0.88rem',
                      fontWeight: 800,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      transition: 'background 0.2s'
                    }}
                    title="Export official incident PDF report with photo evidence"
                  >
                    <FileDown size={16} /> EXPORT PDF
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VerifyReportsView;
