import React, { useState, useEffect, useRef } from 'react';
import { Camera, X, AlertTriangle, ShieldCheck, RefreshCw, Layers, Activity, AlertCircle } from 'lucide-react';
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

export const CameraHUDModal = ({
  isOpen,
  onClose,
  currentLocation,
  onDriverAlert
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

  // Start or Stop Camera when modal toggles
  useEffect(() => {
    if (!isOpen) {
      stopCamera();
      isRunningRef.current = false;
      detectionFilter.reset();
      setActiveDetections([]);
      setAdminNotice(null);
      return;
    }

    isRunningRef.current = true;
    startCamera();

    return () => {
      isRunningRef.current = false;
      stopCamera();
    };
  }, [isOpen]);

  const startCamera = async () => {
    setCameraError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera device access API is not supported in this browser.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: { ideal: 'environment' } // Prefer front ADAS / rear road camera on mobile/vehicle
        },
        audio: false
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraActive(true);
      }
    } catch (err) {
      console.warn('Physical camera start notice:', err.message);
      setCameraActive(false);
      setCameraError(
        err.name === 'NotAllowedError'
          ? 'Camera permission was denied. Please allow camera permissions in your browser address bar.'
          : err.name === 'NotFoundError'
          ? 'No camera video input hardware was found on this device.'
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
    if (!isOpen || !cameraActive) return;

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
                  setAdminNotice(`Persistent ${filterRes.adminEventDispatched.category?.toUpperCase()} sent to Admin HQ`);
                }
                const st = filterRes.activeStreaks[0]?.streak || 0;
                setStreakCount(st);
              } catch (err) {
                // Ignore transient frame request drops
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

      // Adaptive throttle: schedule next frame quickly for smooth live vision
      if (isRunningRef.current) {
        timeoutId = setTimeout(runInferenceCycle, 180);
      }
    };

    runInferenceCycle();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [isOpen, cameraActive, currentLocation]);

  if (!isOpen) return null;

  const primaryDetection = activeDetections[0] || null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 1000,
        background: 'rgba(15, 23, 42, 0.72)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '560px',
          background: '#090d16',
          color: '#ffffff',
          borderRadius: '20px',
          overflow: 'hidden',
          border: '1.5px solid rgba(255, 255, 255, 0.18)',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.6)'
        }}
      >
        {/* HUD Top Bar */}
        <div
          style={{
            padding: '12px 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(255, 255, 255, 0.04)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: '#0284c7',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 12px rgba(2, 132, 199, 0.5)'
              }}
            >
              <Camera size={18} color="#ffffff" />
            </div>
            <div>
              <div style={{ fontSize: '0.88rem', fontWeight: 900, letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '6px' }}>
                LIVE ADAS VISION
                <span
                  style={{
                    fontSize: '0.65rem',
                    background: cameraActive ? '#22c55e' : '#ef4444',
                    color: '#000',
                    padding: '1px 6px',
                    borderRadius: '4px',
                    fontWeight: 900
                  }}
                >
                  {cameraActive ? 'CAMERA LIVE' : 'OFFLINE'}
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                YOLOv11 Master Disaster & Road Hazard Detector
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Real-Time Video & Canvas Overlay Viewport */}
        <div
          ref={containerRef}
          style={{
            position: 'relative',
            width: '100%',
            height: '320px',
            background: '#020617',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {/* Live Physical Camera Stream */}
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

          {/* Fallback Camera Hardware Prompt if Permission Denied or Unavailable */}
          {!cameraActive && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '24px',
                textAlign: 'center',
                gap: '12px',
                color: '#94a3b8'
              }}
            >
              <AlertCircle size={36} color="#ef4444" />
              <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f8fafc', maxWidth: '380px' }}>
                {cameraError || 'Initializing Camera Hardware...'}
              </div>
              <button
                onClick={startCamera}
                className="btn btn-secondary"
                style={{
                  padding: '6px 14px',
                  fontSize: '0.78rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#0284c7',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px'
                }}
              >
                <RefreshCw size={13} /> Retry Camera Access
              </button>
            </div>
          )}

          {/* Hidden Offscreen Canvas for Frame Capture */}
          <canvas ref={canvasRef} style={{ display: 'none' }} />

          {/* Real-Time Bounding Box Canvas Overlay */}
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

          {/* Top Real-Time Telemetry Bar */}
          {cameraActive && (
            <div
              style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                right: '12px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                pointerEvents: 'none',
                zIndex: 20
              }}
            >
              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.85)',
                  padding: '4px 10px',
                  borderRadius: '8px',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  border: '1px solid rgba(255, 255, 255, 0.12)'
                }}
              >
                <Layers size={13} color="#38bdf8" />
                <span>Persistence: {streakCount}/3 frames</span>
              </div>

              <div
                style={{
                  background: 'rgba(15, 23, 42, 0.85)',
                  padding: '4px 10px',
                  borderRadius: '8px',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  border: '1px solid rgba(255, 255, 255, 0.12)'
                }}
              >
                <Activity size={13} color="#4ade80" />
                <span>Inference: {inferenceMs} ms</span>
              </div>
            </div>
          )}

          {/* Section 27: Bottom Live Hazard Card in Camera Panel */}
          {primaryDetection && cameraActive && (
            <div
              style={{
                position: 'absolute',
                bottom: '12px',
                left: '12px',
                right: '12px',
                background: 'rgba(15, 23, 42, 0.94)',
                border: '1.5px solid #f59e0b',
                borderRadius: '10px',
                padding: '8px 14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                zIndex: 20,
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={18} color="#f59e0b" />
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 900, color: '#f59e0b' }}>
                    [ {primaryDetection.class_name?.toUpperCase() || 'HAZARD'} ]
                  </div>
                  {primaryDetection.depth_cm && (
                    <div style={{ fontSize: '0.72rem', color: '#ffffff', fontWeight: 700 }}>
                      Depth: ~{primaryDetection.depth_cm} cm
                    </div>
                  )}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 700 }}>
                  ⚠ Hazard detected
                </div>
                <div style={{ fontSize: '0.86rem', fontWeight: 900, color: '#38bdf8' }}>
                  Distance: ~{Math.round(primaryDetection.distance_m || 6)} m
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer: Status Notification only */}
        {adminNotice && (
          <div style={{ padding: '10px 18px', background: 'rgba(255, 255, 255, 0.03)' }}>
            <div
              style={{
                fontSize: '0.74rem',
                color: '#86efac',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <ShieldCheck size={14} color="#86efac" />
              <span>{adminNotice}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CameraHUDModal;
