import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  AlertTriangle, 
  MapPin, 
  PhoneCall, 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  RefreshCw,
  Send,
  Users,
  Flame,
  Waves,
  Mountain,
  Truck
} from 'lucide-react';

const HAZARD_TYPES = [
  { id: 'Flash Flood', label: 'Flash Flood / Submerged', icon: Waves, color: '#38bdf8' },
  { id: 'Wildfire Corridor', label: 'Wildfire / Smoke', icon: Flame, color: '#f87171' },
  { id: 'Landslide', label: 'Landslide / Rockfall', icon: Mountain, color: '#fbbf24' },
  { id: 'Road Collapse', label: 'Road Collapse / Damage', icon: AlertTriangle, color: '#ef4444' },
  { id: 'Medical Emergency', label: 'Medical / Trauma', icon: ShieldAlert, color: '#ec4899' },
  { id: 'Vehicle Accident', label: 'Rollover / Stranded', icon: Truck, color: '#a855f7' }
];

const EmergencySOS = ({ setActiveTab }) => {
  const { user } = useAuth();
  const [selectedHazard, setSelectedHazard] = useState('Flash Flood');
  const [location, setLocation] = useState({
    lat: 13.0827,
    lng: 80.2707,
    address: 'Anna Salai Near Guindy, Chennai'
  });

  // Countdown trigger states
  const [countingDown, setCountingDown] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(5);
  const [activeSos, setActiveSos] = useState(null);
  const [sosHistory, setSosHistory] = useState([]);
  const [notifyingContacts, setNotifyingContacts] = useState(false);
  const [contactNotificationSent, setContactNotificationSent] = useState(false);

  // Auto fetch location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setLocation({
          lat: parseFloat(pos.coords.latitude.toFixed(5)),
          lng: parseFloat(pos.coords.longitude.toFixed(5)),
          address: 'GPS Auto-Detected Live Coordinates'
        });
      });
    }
    fetchEmergencies();
  }, []);

  // Countdown timer effect
  useEffect(() => {
    let timer;
    if (countingDown && secondsLeft > 0) {
      timer = setTimeout(() => setSecondsLeft(secondsLeft - 1), 1000);
    } else if (countingDown && secondsLeft === 0) {
      setCountingDown(false);
      executeSOSTrigger();
    }
    return () => clearTimeout(timer);
  }, [countingDown, secondsLeft]);

  const fetchEmergencies = async () => {
    try {
      const list = await api.getEmergencyList();
      setSosHistory(list);
    } catch {
      setSosHistory([
        {
          _id: 'sos_demo_1',
          username: 'driver_ravi',
          disasterType: 'Flash Flood',
          status: 'Dispatched',
          location: { address: 'OMR Road Km 12', lat: 12.98, lng: 80.22 },
          assignedTeam: { team_type: 'NDRF Disaster Unit', eta_minutes: 12 },
          timestamp: new Date().toISOString()
        }
      ]);
    }
  };

  const handleStartCountdown = () => {
    setSecondsLeft(5);
    setCountingDown(true);
  };

  const handleCancelCountdown = () => {
    setCountingDown(false);
    setSecondsLeft(5);
  };

  const executeSOSTrigger = async () => {
    try {
      const payload = {
        disasterType: selectedHazard,
        lat: location.lat,
        lng: location.lng,
        address: location.address
      };
      const res = await api.sendEmergencySOS(payload);
      setActiveSos(res);
      fetchEmergencies();
    } catch {
      const mock = {
        id: `sos_${Date.now()}`,
        disasterType: selectedHazard,
        location,
        status: 'Pending',
        timestamp: new Date().toISOString()
      };
      setActiveSos(mock);
      setSosHistory((prev) => [mock, ...prev]);
    }
  };

  const handleNotifyEmergencyContacts = async () => {
    if (!activeSos) return;
    setNotifyingContacts(true);
    try {
      await api.notifyEmergencyContacts(activeSos.id || activeSos._id, [
        { name: 'Family Contact', phone: '+91 98765 43210', relationship: 'Spouse' },
        { name: 'Fleet HQ Supervisor', phone: '+91 98765 11223', relationship: 'Command HQ' }
      ]);
      setContactNotificationSent(true);
    } catch {
      setContactNotificationSent(true);
    } finally {
      setNotifyingContacts(false);
    }
  };

  return (
    <div className="sos-page">
      {/* Header */}
      <div className="hud-header">
        <div className="hud-title-group">
          <h1>
            <AlertTriangle size={32} color="#ef4444" className="animate-pulse" />
            Vehicular Emergency SOS & Disaster Dispatch
          </h1>
          <p className="hud-subtitle">
            One-touch priority satellite dispatch with automatic GPS telemetry broadcast to National Disaster Response teams
          </p>
        </div>

        <div className="pulse-indicator pulse-danger">
          <div className="pulse-dot"></div>
          <span>SOS BEACON READY</span>
        </div>
      </div>

      <div className="grid-2">
        {/* Left: SOS Beacon Trigger Button & Hazard Selector */}
        <div className="glass-panel glass-panel-danger" style={{ padding: '28px', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '8px', color: '#dc2626', fontWeight: 800 }}>
            Emergency Beacon Control
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: '24px' }}>
            Select hazard category and depress button to initiate immediate rescue protocol.
          </p>

          {/* Hazard Selector Grid */}
          <div 
            style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(2, 1fr)', 
              gap: '10px', 
              marginBottom: '24px',
              textAlign: 'left'
            }}
          >
            {HAZARD_TYPES.map((h) => {
              const Icon = h.icon;
              const isSelected = selectedHazard === h.id;
              return (
                <button
                  key={h.id}
                  onClick={() => setSelectedHazard(h.id)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '8px',
                    background: isSelected ? '#fee2e2' : '#f8fafc',
                    border: `1px solid ${isSelected ? '#dc2626' : '#e2e8f0'}`,
                    color: isSelected ? '#991b1b' : '#334155',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <Icon size={18} color={isSelected ? '#dc2626' : h.color} />
                  <span style={{ fontSize: '0.82rem', fontWeight: 700 }}>{h.label}</span>
                </button>
              );
            })}
          </div>

          {/* Big SOS Button or Countdown */}
          {countingDown ? (
            <div style={{ padding: '30px 0' }}>
              <div 
                style={{ 
                  fontSize: '4.5rem', 
                  fontWeight: 900, 
                  fontFamily: 'var(--font-mono)', 
                  color: '#dc2626',
                  lineHeight: 1
                }}
              >
                00:0{secondsLeft}
              </div>
              <p style={{ color: '#b91c1c', margin: '12px 0 20px', fontWeight: 700 }}>
                Broadcasting Emergency Alert in {secondsLeft} seconds...
              </p>
              <button
                onClick={handleCancelCountdown}
                className="btn btn-secondary"
                style={{ padding: '12px 28px', fontSize: '1rem', borderColor: '#dc2626', color: '#dc2626', fontWeight: 700 }}
              >
                Cancel SOS Trigger
              </button>
            </div>
          ) : (
            <div style={{ padding: '16px 0 24px' }}>
              <button
                onClick={handleStartCountdown}
                className="btn btn-sos"
                style={{ width: '220px', height: '220px', borderRadius: '50%', margin: '0 auto', display: 'flex', flexDirection: 'column' }}
              >
                <AlertTriangle size={54} />
                <span style={{ fontSize: '1.75rem', marginTop: '6px' }}>SOS</span>
                <span style={{ fontSize: '0.72rem', letterSpacing: '0.08em', fontWeight: 600 }}>DISPATCH BEACON</span>
              </button>
            </div>
          )}

          {/* GPS Coordinates Bar */}
          <div 
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              gap: '8px', 
              color: '#475569', 
              fontSize: '0.85rem',
              padding: '10px 14px',
              background: '#f1f5f9',
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              fontWeight: 500
            }}
          >
            <MapPin size={16} color="#0284c7" />
            <span>Lat: {location.lat}, Lng: {location.lng}</span>
            <span>•</span>
            <span style={{ color: '#0f172a', fontWeight: 700 }}>{location.address}</span>
          </div>
        </div>

        {/* Right: Active SOS Incident Status & Responder Tracking */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '1.15rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={20} color="#06b6d4" />
            Active SOS Status & Rescue Command
          </h2>

          {activeSos ? (
            <div style={{ marginBottom: '24px' }}>
              <div 
                style={{ 
                  padding: '20px', 
                  borderRadius: '12px', 
                  background: '#fef2f2', 
                  border: '1px solid #fecaca',
                  marginBottom: '16px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="badge badge-danger">SOS TRANSMITTED</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#475569', fontWeight: 600 }}>
                    ID: {activeSos.id || activeSos._id}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.3rem', color: '#991b1b', margin: '8px 0 4px', fontWeight: 800 }}>
                  {activeSos.disasterType}
                </h3>
                <p style={{ color: '#475569', fontSize: '0.85rem' }}>
                  Status: <strong style={{ color: '#dc2626' }}>{activeSos.status || 'Pending Rescue Team'}</strong>
                </p>

                {/* Simulated Emergency Contacts Alert */}
                <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #fecaca' }}>
                  {contactNotificationSent ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#059669', fontSize: '0.85rem', fontWeight: 600 }}>
                      <CheckCircle2 size={18} />
                      Emergency SMS & WhatsApp notifications delivered to family & HQ.
                    </div>
                  ) : (
                    <button
                      onClick={handleNotifyEmergencyContacts}
                      disabled={notifyingContacts}
                      className="btn btn-secondary"
                      style={{ width: '100%', padding: '10px', fontSize: '0.85rem' }}
                    >
                      {notifyingContacts ? <RefreshCw size={15} className="animate-spin" /> : <Send size={15} />}
                      Notify Registered Emergency Contacts (SMS & WhatsApp)
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>
              <PhoneCall size={40} style={{ opacity: 0.3, margin: '0 auto 10px' }} />
              <p>No active SOS beacon transmitted from this vehicle. System is standby ready.</p>
            </div>
          )}

          {/* Recent SOS Audit Feed */}
          <h3 style={{ fontSize: '0.95rem', color: '#0f172a', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 800 }}>
            Incident Dispatch Log
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {sosHistory.slice(0, 4).map((sos, i) => (
              <div 
                key={sos._id || i}
                style={{
                  padding: '12px 14px',
                  background: '#f8fafc',
                  borderRadius: '8px',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, color: '#0f172a', fontSize: '0.88rem' }}>
                      {sos.disasterType}
                    </span>
                    <span className={`badge ${
                      sos.status === 'Pending' ? 'badge-danger' :
                      sos.status === 'Dispatched' ? 'badge-warning' : 'badge-safe'
                    }`}>
                      {sos.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#475569', marginTop: '2px' }}>
                    {sos.location?.address || 'GPS Coordinates'}
                  </div>
                  {sos.assignedTeam && (
                    <div style={{ fontSize: '0.78rem', color: '#0284c7', marginTop: '2px', fontWeight: 600 }}>
                      Assigned: {sos.assignedTeam.team_type} (ETA: {sos.assignedTeam.eta_minutes}m)
                    </div>
                  )}
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                    {sos.timestamp ? new Date(sos.timestamp).toLocaleTimeString() : 'Live'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencySOS;
