import React, { useState, useEffect, useRef } from 'react';
import { Camera, X, AlertTriangle, ShieldCheck, RefreshCw, Layers, Activity, AlertCircle, Maximize2, Minimize2 } from 'lucide-react';
import api from '../../services/api';
import detectionFilter from '../../services/detectionFilter';

const CLASS_COLORS = {
  pothole: '#f59e0b',        // Amber
  flood: '#06b6d4',          // Cyan
  fire: '#ef4444',           // Red
  smoke: '#94a3b8',          // Gray
  pedestrian: '#eab308',     // Yellow-Gold
  person: '#eab308',
  vehicle: '#10b981',        // Emerald Green
  damage: '#f97316'          // Orange
};

export const LiveCameraSidePanel = ({
  currentLocation,
  onDriverAlert,
  onClose,
  isExpanded,
  onToggleExpand
}) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const containerRef = useRef(null);
  const isRunningRef = useRef(false);

  const [activeDetections, setActiveDetections] = useState([]);
  const [adminNotice, setAdminNotice] = useState(null);
  const [streakCount, setStreakCount] = useState(0);
  const [inferenceMs, setInferenceMs] = useState(0);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);

  // Start Camera on mount, stop on unmount
  useEffect(() => {
    isRunningRef.current = true;
    startCamera();

    // Trigger window resize so the adjacent map recalculates its dimensions smoothly
    const t = setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 100);

    return () => {
      clearTimeout(t);
      isRunningRef.current = false;
      stopCamera();
      detectionFilter.reset();
      window.dispatchEvent(new Event('resize'));
    };
  }, []);

  const startCamera = async () => {
    setCameraError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera access API is not supported in this browser.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: { ideal: 'environment' }
        },
        audio: false
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraActive(true);
      }
    } catch (err) {
      console.warn('Live camera access notice:', err.message);
      setCameraActive(false);
      setCameraError(
        err.name === 'NotAllowedError'
          ? 'Camera permission denied. Please allow camera permissions in your browser address bar.'
          : err.name === 'NotFoundError'
          ? 'No camera input hardware found on this system.'
          : err.message || 'Unable to access camera hardware.'
      );
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject;
      const tracks = stream.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  // Draw real-time bounding boxes directly onto overlay canvas
  const drawBoundingBoxes = (detections, sourceW = 640, sourceH = 480) => {
    const canvas = overlayCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const displayW = canvas.width;
    const displayH = canvas.height;

    ctx.clearRect(0, 0, displayW, displayH);

    // Compute exact cover scale and letterbox/crop offset to match video objectFit: cover
    const scale = Math.max(displayW / (sourceW || 640), displayH / (sourceH || 480));
    const offsetX = (displayW - (sourceW || 640) * scale) / 2;
    const offsetY = (displayH - (sourceH || 480) * scale) / 2;

    detections.forEach(det => {
      const bbox = det.bbox || [0, 0, 0, 0];
      const x1 = Math.max(0, bbox[0] * scale + offsetX);
      const y1 = Math.max(0, bbox[1] * scale + offsetY);
      const x2 = Math.min(displayW, bbox[2] * scale + offsetX);
      const y2 = Math.min(displayH, bbox[3] * scale + offsetY);
      const w = Math.max(10, x2 - x1);
      const h = Math.max(10, y2 - y1);

      const cat = (det.class_name || '').toLowerCase();
      let strokeColor = '#f59e0b';
      for (const [key, color] of Object.entries(CLASS_COLORS)) {
        if (cat.includes(key)) {
          strokeColor = color;
          break;
        }
      }

      // 1. Draw Bounding Box with subtle glow
      ctx.save();
      ctx.shadowColor = strokeColor;
      ctx.shadowBlur = 8;
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 2.5;
      ctx.strokeRect(x1, y1, w, h);
      ctx.restore();

      // 2. High-Tech ADAS Corner Brackets
      const cornerLen = Math.min(16, w / 4, h / 4);
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 3;
      // Top-Left
      ctx.beginPath();
      ctx.moveTo(x1, y1 + cornerLen);
      ctx.lineTo(x1, y1);
      ctx.lineTo(x1 + cornerLen, y1);
      ctx.stroke();
      // Bottom-Right
      ctx.beginPath();
      ctx.moveTo(x2, y2 - cornerLen);
      ctx.lineTo(x2, y2);
      ctx.lineTo(x2 - cornerLen, y2);
      ctx.stroke();

      // 3. Label Tag
      const confPct = Math.round((det.confidence || 0.85) * 100);
      let labelText = `${det.class_name?.toUpperCase() || 'HAZARD'} ${confPct}%`;
      if (det.depth_cm) labelText += ` · ${det.depth_cm}cm`;
      if (det.distance_m) labelText += ` · ~${Math.round(det.distance_m)}m`;

      ctx.font = 'bold 11px system-ui, -apple-system, sans-serif';
      const textMetrics = ctx.measureText(labelText);
      const tagWidth = textMetrics.width + 12;
      const tagHeight = 20;

      ctx.fillStyle = strokeColor;
      ctx.fillRect(x1, Math.max(0, y1 - tagHeight), tagWidth, tagHeight);

      ctx.fillStyle = '#000000';
      ctx.fillText(labelText, x1 + 6, Math.max(14, y1 - 5));
    });
  };

  // Continuous adaptive real-time inference loop
  useEffect(() => {
    if (!cameraActive) return;

    let timeoutId = null;

    const runInferenceCycle = async () => {
      if (!isRunningRef.current) return;
      const t0 = performance.now();

      try {
        if (videoRef.current && canvasRef.current && videoRef.current.readyState >= 2) {
          const video = videoRef.current;
          const canvas = canvasRef.current;

          const vw = video.videoWidth || 640;
          const vh = video.videoHeight || 480;

          canvas.width = vw;
          canvas.height = vh;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(video, 0, 0, vw, vh);

          // Sync overlay canvas size to container only when altered (prevents blanking canvas)
          if (overlayCanvasRef.current && containerRef.current) {
            const cw = containerRef.current.clientWidth;
            const ch = containerRef.current.clientHeight;
            if (overlayCanvasRef.current.width !== cw || overlayCanvasRef.current.height !== ch) {
              overlayCanvasRef.current.width = cw;
              overlayCanvasRef.current.height = ch;
            }
          }

          // Convert frame to blob for YOLO endpoint
          await new Promise((resolve) => {
            canvas.toBlob(async (blob) => {
              if (!blob) return resolve();
              const formData = new FormData();
              formData.append('file', blob, 'frame.jpg');
              if (currentLocation) {
                formData.append('lat', currentLocation.lat);
                formData.append('lng', currentLocation.lng);
              }

              try {
                const res = await api.predictImage(formData);
                const dets = res?.detections || [];
                setActiveDetections(dets);
                drawBoundingBoxes(dets, vw, vh);

                const filterRes = await detectionFilter.processFrame(
                  dets,
                  currentLocation,
                  canvas.toDataURL('image/jpeg', 0.5)
                );

                if (filterRes.driverAlert && onDriverAlert) {
                  onDriverAlert(filterRes.driverAlert);
                }
                if (filterRes.adminEventDispatched) {
                  setAdminNotice(`Persistent ${filterRes.adminEventDispatched.category?.toUpperCase()} forwarded to Admin HQ`);
                }
                const st = filterRes.activeStreaks[0]?.streak || 0;
                setStreakCount(st);
              } catch (err) {
                console.warn('Real-time frame prediction notice:', err);
              }
              resolve();
            }, 'image/jpeg', 0.65);
          });
        }
      } catch (err) {
        console.warn('Real-time frame error:', err.message);
      }

      const elapsed = Math.round(performance.now() - t0);
      setInferenceMs(elapsed > 0 ? elapsed : 35);

      if (isRunningRef.current) {
        timeoutId = setTimeout(runInferenceCycle, 180);
      }
    };

    runInferenceCycle();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [cameraActive, currentLocation]);

  const primaryDetection = activeDetections[0] || null;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: '#090d16',
        color: '#ffffff'
      }}
    >
      {/* Header Bar */}
      <div
        style={{
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255, 255, 255, 0.04)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 10px rgba(2, 132, 199, 0.5)'
            }}
          >
            <Camera size={16} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '0.84rem', fontWeight: 900, display: 'flex', alignItems: 'center', gap: '6px' }}>
              ADAS LIVE VISION
              <span
                style={{
                  fontSize: '0.62rem',
                  background: cameraActive ? '#22c55e' : '#ef4444',
                  color: '#000',
                  padding: '1px 5px',
                  borderRadius: '4px',
                  fontWeight: 900
                }}
              >
                {cameraActive ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
              Real-Time YOLOv11 Road Detection
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#94a3b8',
                borderRadius: '6px',
                cursor: 'pointer',
                padding: '4px 6px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.68rem',
                fontWeight: 700
              }}
              title={isExpanded ? "Standard Camera Size (520px)" : "Wider Camera Size (640px)"}
            >
              {isExpanded ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
              <span>{isExpanded ? 'Shrink' : 'Enlarge'}</span>
            </button>
          )}

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px'
            }}
            title="Close Camera Panel"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Video Canvas Container (Directly beside the map) */}
      <div
        ref={containerRef}
        style={{
          position: 'relative',
          width: '100%',
          flex: 1,
          minHeight: '260px',
          background: '#020617',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <video
          ref={videoRef}
          playsInline
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            display: cameraActive ? 'block' : 'none'
          }}
        />

        {!cameraActive && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
              textAlign: 'center',
              gap: '10px',
              color: '#94a3b8'
            }}
          >
            <AlertCircle size={32} color="#ef4444" />
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc', maxWidth: '300px' }}>
              {cameraError || 'Accessing camera stream...'}
            </div>
            <button
              onClick={startCamera}
              className="btn btn-secondary"
              style={{
                padding: '6px 12px',
                fontSize: '0.74rem',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                background: '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px'
              }}
            >
              <RefreshCw size={12} /> Retry Camera Access
            </button>
          </div>
        )}

        {/* Offscreen frame capture canvas */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* Real-time Bounding Box Overlay Canvas */}
        <canvas
          ref={overlayCanvasRef}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
            zIndex: 10
          }}
        />

        {/* Telemetry Chips */}
        {cameraActive && (
          <div
            style={{
              position: 'absolute',
              top: '8px',
              left: '8px',
              right: '8px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              pointerEvents: 'none',
              zIndex: 20
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.88)',
                padding: '3px 8px',
                borderRadius: '6px',
                fontSize: '0.68rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <Layers size={11} color="#38bdf8" />
              <span>Streak: {streakCount}/3</span>
            </div>

            <div
              style={{
                background: 'rgba(15, 23, 42, 0.88)',
                padding: '3px 8px',
                borderRadius: '6px',
                fontSize: '0.68rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <Activity size={11} color="#4ade80" />
              <span>{inferenceMs} ms</span>
            </div>
          </div>
        )}

        {/* Real-time Hazard Alert Overlay at Bottom of Video */}
        {primaryDetection && cameraActive && (
          <div
            style={{
              position: 'absolute',
              bottom: '8px',
              left: '8px',
              right: '8px',
              background: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid #f59e0b',
              borderRadius: '8px',
              padding: '6px 12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 20,
              boxShadow: '0 4px 16px rgba(0,0,0,0.5)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertTriangle size={16} color="#f59e0b" />
              <div>
                <div style={{ fontSize: '0.78rem', fontWeight: 900, color: '#f59e0b' }}>
                  [ {primaryDetection.class_name?.toUpperCase() || 'HAZARD'} ]
                </div>
                {primaryDetection.depth_cm && (
                  <div style={{ fontSize: '0.68rem', color: '#ffffff', fontWeight: 700 }}>
                    Depth: ~{primaryDetection.depth_cm} cm
                  </div>
                )}
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 700 }}>
                ⚠ Hazard ahead
              </div>
              <div style={{ fontSize: '0.80rem', fontWeight: 900, color: '#38bdf8' }}>
                Distance: ~{Math.round(primaryDetection.distance_m || 6)} m
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Detected Hazards & Road Surface Metrics Section */}
      <div
        style={{
          padding: '12px 14px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          maxHeight: '180px',
          overflowY: 'auto'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Vision Stream Detections ({activeDetections.length})
          </span>
          {currentLocation && (
            <span style={{ fontSize: '0.68rem', color: '#64748b', fontFamily: 'monospace' }}>
              GPS: {currentLocation.lat?.toFixed(4)}, {currentLocation.lng?.toFixed(4)}
            </span>
          )}
        </div>

        {activeDetections.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {activeDetections.map((det, idx) => {
              const cat = (det.class_name || '').toLowerCase();
              let badgeColor = '#f59e0b';
              for (const [key, color] of Object.entries(CLASS_COLORS)) {
                if (cat.includes(key)) {
                  badgeColor = color;
                  break;
                }
              }

              return (
                <div
                  key={idx}
                  style={{
                    background: 'rgba(15, 23, 42, 0.75)',
                    border: `1px solid ${badgeColor}40`,
                    borderLeft: `3px solid ${badgeColor}`,
                    borderRadius: '6px',
                    padding: '6px 10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.76rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 800, color: '#ffffff' }}>
                      {det.class_name?.toUpperCase() || 'OBJECT'}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: badgeColor, fontWeight: 700 }}>
                      {Math.round((det.confidence || 0.8) * 100)}%
                    </span>
                    {det.depth_cm && (
                      <span style={{ fontSize: '0.68rem', background: '#334155', color: '#f8fafc', padding: '1px 5px', borderRadius: '4px' }}>
                        Depth: {det.depth_cm}cm
                      </span>
                    )}
                  </div>
                  <div style={{ fontWeight: 800, color: '#38bdf8', fontSize: '0.74rem' }}>
                    ~{Math.round(det.distance_m || 6)} m
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ fontSize: '0.72rem', color: '#475569', textAlign: 'center', padding: '10px 0' }}>
            ✓ Road corridor clear • Continuous YOLO vision scanning
          </div>
        )}
      </div>

      {/* Panel Footer Info */}
      <div style={{ padding: '10px 14px', background: 'rgba(255, 255, 255, 0.02)', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
        {adminNotice ? (
          <div
            style={{
              fontSize: '0.72rem',
              color: '#86efac',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <ShieldCheck size={13} color="#86efac" />
            <span>{adminNotice}</span>
          </div>
        ) : (
          <div style={{ fontSize: '0.70rem', color: '#64748b' }}>
            Continuous vision stream active. Detections automatically connect to GPS coordinates and feed route risk.
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveCameraSidePanel;
