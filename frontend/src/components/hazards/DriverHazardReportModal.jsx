import React, { useState, useRef, useEffect } from 'react';
import api from '../../services/api';
import { 
  AlertTriangle, 
  Camera, 
  Upload, 
  X, 
  MapPin, 
  CheckCircle2, 
  Loader2, 
  Droplets, 
  Flame, 
  TreePine, 
  Car, 
  Layers, 
  ShieldAlert,
  Zap,
  RefreshCw
} from 'lucide-react';

const HAZARD_CATEGORIES = [
  { id: 'Flooding', label: 'Flooding / Water', icon: Droplets, color: '#0284c7', bg: '#f0f9ff', border: '#bae6fd' },
  { id: 'Pothole', label: 'Pothole / Road Cavity', icon: Layers, color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
  { id: 'Fallen Tree', label: 'Fallen Tree / Debris', icon: TreePine, color: '#15803d', bg: '#f0fdf4', border: '#bbf7d0' },
  { id: 'Road Damage', label: 'Road Damage / Crack', icon: AlertTriangle, color: '#ea580c', bg: '#fff7ed', border: '#fed7aa' },
  { id: 'Fire / Smoke', label: 'Fire / Dense Smoke', icon: Flame, color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
  { id: 'Landslide', label: 'Landslide / Rocks', icon: Layers, color: '#854d0e', bg: '#fefce8', border: '#fef08a' },
  { id: 'Vehicle Accident', label: 'Vehicle Crash', icon: Car, color: '#7c3aed', bg: '#f5f3ff', border: '#ddd6fe' },
  { id: 'Obstacle', label: 'Other Blockade', icon: ShieldAlert, color: '#475569', bg: '#f8fafc', border: '#e2e8f0' }
];

export const DriverHazardReportModal = ({ 
  isOpen, 
  onClose, 
  currentLocation, 
  onHazardReported 
}) => {
  const [disasterType, setDisasterType] = useState('Flooding');
  const [severity, setSeverity] = useState('High');
  const [description, setDescription] = useState('');
  const [depthCm, setDepthCm] = useState('');
  const [imageBase64, setImageBase64] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  
  // Camera capture states
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // File input ref
  const fileInputRef = useRef(null);

  // Default coordinates to user's real GPS or baseline
  const lat = currentLocation?.latitude ?? currentLocation?.lat ?? 12.9716;
  const lng = currentLocation?.longitude ?? currentLocation?.lng ?? 77.5946;

  // Cleanup camera stream when modal closes
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const startCamera = async () => {
    setError('');
    try {
      setCameraActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      console.warn('Camera access denied or unavailable', err);
      setError('Camera access unavailable. Please use file upload instead.');
      setCameraActive(false);
    }
  };

  const captureCameraSnapshot = () => {
    if (!videoRef.current) return;
    try {
      const video = videoRef.current;
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUri = canvas.toDataURL('image/jpeg', 0.85);
      setImagePreview(dataUri);
      setImageBase64(dataUri);
      stopCamera();
    } catch (e) {
      setError('Failed to capture snapshot.');
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setError('Please select an image file (JPEG, PNG).');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setImagePreview(reader.result);
      setImageBase64(reader.result);
      setError('');
    };
    reader.onerror = () => {
      setError('Failed to read image file.');
    };
    reader.readAsDataURL(file);
  };

  const handleClearImage = () => {
    setImagePreview(null);
    setImageBase64(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    stopCamera();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        disasterType: disasterType,
        lat: Number(lat),
        lng: Number(lng),
        severity: severity,
        address: `Corridor GPS (${Number(lat).toFixed(4)}, ${Number(lng).toFixed(4)})`,
        description: description.trim() || `Driver flagged ${disasterType} on driving corridor.`,
        image_base64: imageBase64 || undefined,
        depth_cm: depthCm ? Number(depthCm) : undefined
      };

      const res = await api.reportHazard(payload);

      if (res && (res.status === 'Pending' || res.message || res.id)) {
        setSuccess(true);
        if (onHazardReported) {
          onHazardReported(res);
        }
        setTimeout(() => {
          setSuccess(false);
          handleClearImage();
          setDescription('');
          onClose();
        }, 1500);
      } else {
        setError(res?.message || 'Failed to submit report. Please retry.');
      }
    } catch (err) {
      setError(err?.response?.data?.message || err?.response?.data?.detail || 'Failed to dispatch hazard report to HQ.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
      onClick={() => { stopCamera(); onClose(); }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '560px',
          maxHeight: '92vh',
          background: 'rgba(255, 255, 255, 0.96)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderRadius: '24px',
          border: '1px solid rgba(255, 255, 255, 0.8)',
          boxShadow: '0 25px 60px rgba(15, 23, 42, 0.25)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              background: '#fff7ed',
              color: '#ea580c',
              border: '1px solid #fed7aa',
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <AlertTriangle size={22} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Report Road Hazard
              </h2>
              <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '2px 0 0' }}>
                Crowdsource road blockades to City HQ & warn oncoming vehicles
              </p>
            </div>
          </div>

          <button
            onClick={() => { stopCamera(); onClose(); }}
            style={{ background: '#f1f5f9', border: 'none', borderRadius: '8px', padding: '6px', cursor: 'pointer', color: '#64748b' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '22px 24px' }}>
          {success ? (
            <div style={{ textAlign: 'center', padding: '36px 16px' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: '#dcfce7',
                color: '#15803d',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px',
                boxShadow: '0 4px 16px rgba(22, 163, 74, 0.2)'
              }}>
                <CheckCircle2 size={36} />
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Hazard Dispatched to HQ
              </h3>
              <p style={{ fontSize: '0.86rem', color: '#475569', marginTop: '6px' }}>
                Your report has been queued for verification. Approaching vehicles on this corridor will be notified.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {/* GPS Auto-tag Banner */}
              <div style={{
                background: '#f0f9ff',
                border: '1px solid #bae6fd',
                borderRadius: '12px',
                padding: '10px 14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MapPin size={16} color="#0284c7" />
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#0369a1' }}>
                    Auto-Tagged GPS Fix: {Number(lat).toFixed(4)}, {Number(lng).toFixed(4)}
                  </span>
                </div>
                <span style={{
                  fontSize: '0.68rem',
                  background: '#10b981',
                  color: '#ffffff',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '10px'
                }}>
                  LIVE GPS
                </span>
              </div>

              {/* 1. Pick Hazard Category */}
              <div>
                <label style={{ fontSize: '0.84rem', fontWeight: 700, color: '#0f172a', display: 'block', marginBottom: '8px' }}>
                  1. Select Hazard Type
                </label>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
                  gap: '8px'
                }}>
                  {HAZARD_CATEGORIES.map((cat) => {
                    const Icon = cat.icon;
                    const isSelected = disasterType === cat.id;
                    return (
                      <button
                        type="button"
                        key={cat.id}
                        onClick={() => setDisasterType(cat.id)}
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '10px 6px',
                          borderRadius: '12px',
                          border: isSelected ? `2px solid ${cat.color}` : '1px solid #e2e8f0',
                          background: isSelected ? cat.bg : '#ffffff',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                          boxShadow: isSelected ? `0 2px 8px ${cat.color}30` : 'none'
                        }}
                      >
                        <Icon size={20} color={cat.color} />
                        <span style={{ fontSize: '0.72rem', fontWeight: isSelected ? 800 : 600, color: isSelected ? cat.color : '#334155', textAlign: 'center', lineHeight: 1.2 }}>
                          {cat.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 2. Photo Snapshot Upload / Camera Snap */}
              <div>
                <label style={{ fontSize: '0.84rem', fontWeight: 700, color: '#0f172a', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span>2. Photo Evidence (Camera Snapshot)</span>
                  {imagePreview && (
                    <button
                      type="button"
                      onClick={handleClearImage}
                      style={{ background: 'none', border: 'none', color: '#dc2626', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Remove Photo
                    </button>
                  )}
                </label>

                {cameraActive ? (
                  <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden', background: '#090d16', border: '1px solid #334155' }}>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      style={{ width: '100%', height: '220px', objectFit: 'cover' }}
                    />
                    <div style={{ position: 'absolute', bottom: '12px', left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: '10px' }}>
                      <button
                        type="button"
                        onClick={captureCameraSnapshot}
                        style={{
                          background: '#0284c7',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '10px',
                          padding: '8px 18px',
                          fontWeight: 800,
                          fontSize: '0.84rem',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)'
                        }}
                      >
                        <Camera size={16} /> Snap Photo
                      </button>
                      <button
                        type="button"
                        onClick={stopCamera}
                        style={{
                          background: 'rgba(255, 255, 255, 0.9)',
                          color: '#0f172a',
                          border: 'none',
                          borderRadius: '10px',
                          padding: '8px 14px',
                          fontWeight: 700,
                          fontSize: '0.84rem',
                          cursor: 'pointer'
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : imagePreview ? (
                  <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden', border: '1px solid #cbd5e1', height: '180px' }}>
                    <img
                      src={imagePreview}
                      alt="Hazard Evidence"
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                    <div style={{
                      position: 'absolute',
                      top: '8px',
                      right: '8px',
                      background: 'rgba(0,0,0,0.6)',
                      color: '#ffffff',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      fontSize: '0.72rem',
                      fontWeight: 700
                    }}>
                      ✓ Evidence Attached
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      type="button"
                      onClick={startCamera}
                      style={{
                        flex: 1,
                        padding: '16px',
                        border: '1.5px dashed #0284c7',
                        borderRadius: '12px',
                        background: '#f0f9ff',
                        color: '#0284c7',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <Camera size={24} />
                      <span style={{ fontSize: '0.82rem', fontWeight: 800 }}>Snap Live Photo</span>
                      <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Use device camera</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      style={{
                        flex: 1,
                        padding: '16px',
                        border: '1.5px dashed #cbd5e1',
                        borderRadius: '12px',
                        background: '#f8fafc',
                        color: '#475569',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <Upload size={24} />
                      <span style={{ fontSize: '0.82rem', fontWeight: 800 }}>Upload Image</span>
                      <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Browse gallery / frame</span>
                    </button>

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      capture="environment"
                      onChange={handleFileChange}
                      style={{ display: 'none' }}
                    />
                  </div>
                )}
              </div>

              {/* 3. Severity & Observation Description */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.84rem', fontWeight: 700, color: '#0f172a', display: 'block', marginBottom: '6px' }}>
                    Severity Level
                  </label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="form-select"
                    style={{ padding: '9px 12px', fontSize: '0.86rem' }}
                  >
                    <option value="Low">Low (Passable with care)</option>
                    <option value="Medium">Medium (Significant delay)</option>
                    <option value="High">High (Dangerous / Blockage)</option>
                    <option value="Critical">Critical (Completely impassable)</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.84rem', fontWeight: 700, color: '#0f172a', display: 'block', marginBottom: '6px' }}>
                    Water Depth (Optional)
                  </label>
                  <input
                    type="number"
                    value={depthCm}
                    onChange={(e) => setDepthCm(e.target.value)}
                    placeholder="e.g. 25 cm"
                    className="form-input"
                    style={{ padding: '9px 12px', fontSize: '0.86rem' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.84rem', fontWeight: 700, color: '#0f172a', display: 'block', marginBottom: '6px' }}>
                  Observation Notes (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Deep pothole right in center lane after bridge, cars swerving."
                  rows={2}
                  className="form-textarea"
                  style={{ padding: '10px 12px', fontSize: '0.85rem' }}
                />
              </div>

              {/* Error Notice */}
              {error && (
                <div style={{
                  padding: '10px 14px',
                  background: '#fef2f2',
                  border: '1px solid #fecaca',
                  borderRadius: '10px',
                  color: '#dc2626',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <AlertTriangle size={16} />
                  <span>{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
                style={{
                  padding: '13px',
                  fontSize: '0.92rem',
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #ea580c 0%, #c2410c 100%)',
                  border: 'none',
                  boxShadow: '0 4px 14px rgba(234, 88, 12, 0.35)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  borderRadius: '12px',
                  marginTop: '4px'
                }}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Transmitting Telemetry...</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={18} />
                    <span>Submit & Broadcast Hazard</span>
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default DriverHazardReportModal;
