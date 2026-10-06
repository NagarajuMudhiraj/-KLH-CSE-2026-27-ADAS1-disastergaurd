import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import cacheService from '../services/cacheService';
import { 
  User, 
  Phone, 
  HeartPulse, 
  ShieldCheck, 
  Save, 
  CheckCircle2, 
  AlertCircle,
  History,
  Database,
  Trash2,
  HardDrive,
  ShieldAlert,
  Mail,
  Activity,
  MapPin,
  Clock,
  Lock,
  Radio
} from 'lucide-react';

const Profile = ({ setActiveTab }) => {
  const { user, updateUser } = useAuth();
  const [tripHistory, setTripHistory] = useState(() => cacheService.getTripHistory());
  const [adminIncidents, setAdminIncidents] = useState(() => cacheService.getAdminIncidentLog());

  const [formData, setFormData] = useState({
    username: user?.username || 'driver',
    email: user?.email || 'driver@emergency.org',
    role: user?.role || 'driver',
    phone: '+91 98765 43210',
    license_number: 'DL-1420110098765',
    blood_group: 'O+ Positive',
    medical_conditions: 'No major allergies · Cardiac clearance normal',
    emergency_contact_name: 'Ramesh Kumar',
    emergency_contact_phone: '+91 98765 12345',
    adas_auto_sos: true,
    preferred_navigation: 'Safest Route'
  });

  const [savedMessage, setSavedMessage] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const profile = await api.getProfile();
        if (profile) {
          setFormData((prev) => ({ ...prev, ...profile }));
        }
      } catch (e) {
        console.warn("Could not fetch remote profile, using local defaults", e);
      }
    };
    fetchUserProfile();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await api.updateProfile(formData);
      updateUser({ ...user, ...updated });
      setSavedMessage('Driver credentials & medical profile saved successfully!');
      setTimeout(() => setSavedMessage(null), 4000);
    } catch {
      updateUser({ ...user, ...formData });
      setSavedMessage('Profile cached locally in operational memory.');
      setTimeout(() => setSavedMessage(null), 4000);
    } finally {
      setSaving(false);
    }
  };

  // Quick stats derived from trip memory
  const totalTripDistance = tripHistory.reduce((acc, t) => acc + (parseFloat(t.distanceKm) || 0), 0).toFixed(1);
  const totalHazardsAvoided = tripHistory.reduce((acc, t) => acc + (parseInt(t.hazardsAvoided) || 0), 0);

  return (
    <div className="profile-page" style={{ maxWidth: '1240px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      
      {/* ============================================================ */}
      {/* 1. DRIVER IDENTITY & TELEMETRY HERO BANNER */}
      {/* ============================================================ */}
      <div className="glass-panel" style={{ padding: '24px 28px', background: 'linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(240,249,255,0.95) 100%)', border: '1px solid #bae6fd' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px' }}>
          
          {/* Left: Driver Avatar & Quick Credentials */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
            <div style={{ 
              width: '64px', 
              height: '64px', 
              borderRadius: '50%', 
              background: 'linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.35)',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: '1.4rem'
            }}>
              <User size={32} color="#ffffff" />
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a', margin: 0, textTransform: 'capitalize' }}>
                  {formData.username || 'Connected Driver'}
                </h1>
                <span className={`badge ${formData.role === 'admin' ? 'badge-purple' : 'badge-info'}`} style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
                  {formData.role.toUpperCase()}
                </span>
                <span style={{ 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: '6px', 
                  fontSize: '0.75rem', 
                  background: '#f0fdf4', 
                  color: '#15803d', 
                  border: '1px solid #bbf7d0',
                  padding: '3px 9px',
                  borderRadius: '999px',
                  fontWeight: 600
                }}>
                  <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}></span>
                  ADAS Telemetry Active
                </span>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '6px', fontSize: '0.84rem', color: '#475569', flexWrap: 'wrap' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Mail size={14} color="#0284c7" /> {formData.email}
                </span>
                <span style={{ color: '#cbd5e1' }}>•</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Phone size={14} color="#0284c7" /> {formData.phone}
                </span>
                <span style={{ color: '#cbd5e1' }}>•</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <ShieldCheck size={14} color="#059669" /> License: <strong>{formData.license_number}</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Right: Quick Action / Safety Overview Chips */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <div style={{ 
              background: '#ffffff', 
              border: '1px solid #e2e8f0', 
              borderRadius: '10px', 
              padding: '10px 14px', 
              textAlign: 'center',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
            }}>
              <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Blood Group</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#dc2626', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'center' }}>
                <HeartPulse size={14} /> {formData.blood_group || 'O+'}
              </div>
            </div>

            <div style={{ 
              background: '#ffffff', 
              border: '1px solid #e2e8f0', 
              borderRadius: '10px', 
              padding: '10px 14px', 
              textAlign: 'center',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
            }}>
              <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Emergency SOS</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#16a34a', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'center' }}>
                <Radio size={14} /> Ready
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* ============================================================ */}
      {/* 2. SYMMETRICAL 2-COLUMN PROFILE & MEDICAL FORM */}
      {/* ============================================================ */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 460px), 1fr))', 
          gap: '22px' 
        }}>
          
          {/* Card 1: Driver Identification */}
          <div className="glass-panel" style={{ padding: '24px 26px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <h2 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '8px', margin: 0, color: '#0f172a' }}>
                  <User size={19} color="#0284c7" />
                  Driver Identification
                </h2>
                <span style={{ fontSize: '0.72rem', background: '#e0f2fe', color: '#0369a1', padding: '3px 8px', borderRadius: '4px', fontWeight: 700 }}>
                  VERIFIED
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '18px' }}>
                Personal credentials, account login handle, and verified licensing info
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                    Driver Username / Call-Sign
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input 
                      type="text" 
                      value={formData.username} 
                      disabled 
                      className="form-input" 
                      style={{ opacity: 0.8, background: '#f8fafc', cursor: 'not-allowed', paddingLeft: '34px' }}
                    />
                    <Lock size={15} color="#94a3b8" style={{ position: 'absolute', left: '11px', top: '50%', transform: 'translateY(-50%)' }} />
                  </div>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                    Emergency Dispatch Email Address
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input 
                      type="email" 
                      value={formData.email} 
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })} 
                      className="form-input" 
                      required
                      placeholder="driver@emergency.org"
                      style={{ paddingLeft: '34px' }}
                    />
                    <Mail size={15} color="#0284c7" style={{ position: 'absolute', left: '11px', top: '50%', transform: 'translateY(-50%)' }} />
                  </div>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                    Driver Contact Mobile Phone
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input 
                      type="text" 
                      value={formData.phone} 
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })} 
                      className="form-input" 
                      placeholder="+91 98765 43210"
                      style={{ paddingLeft: '34px' }}
                    />
                    <Phone size={15} color="#0284c7" style={{ position: 'absolute', left: '11px', top: '50%', transform: 'translateY(-50%)' }} />
                  </div>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                    Driver License Number
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input 
                      type="text" 
                      value={formData.license_number} 
                      onChange={(e) => setFormData({ ...formData, license_number: e.target.value })} 
                      className="form-input" 
                      placeholder="DL-1420110098765"
                      style={{ paddingLeft: '34px' }}
                    />
                    <ShieldCheck size={15} color="#0284c7" style={{ position: 'absolute', left: '11px', top: '50%', transform: 'translateY(-50%)' }} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Responder Medical Info & Emergency Contact Dispatch */}
          <div className="glass-panel" style={{ padding: '24px 26px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <h2 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '8px', margin: 0, color: '#0f172a' }}>
                  <HeartPulse size={19} color="#ef4444" />
                  Responder Medical & Emergency Contact
                </h2>
                <span style={{ fontSize: '0.72rem', background: '#fee2e2', color: '#b91c1c', padding: '3px 8px', borderRadius: '4px', fontWeight: 700 }}>
                  PRIORITY SOS
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '18px' }}>
                Transmitted automatically to emergency responders and hospitals upon SOS trigger
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '12px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                      Blood Group
                    </label>
                    <input 
                      type="text" 
                      value={formData.blood_group} 
                      onChange={(e) => setFormData({ ...formData, blood_group: e.target.value })} 
                      className="form-input" 
                      placeholder="e.g. O+ Positive"
                    />
                  </div>

                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                      Emergency Contact Phone
                    </label>
                    <input 
                      type="text" 
                      value={formData.emergency_contact_phone} 
                      onChange={(e) => setFormData({ ...formData, emergency_contact_phone: e.target.value })} 
                      className="form-input" 
                      placeholder="+91 98765 12345"
                    />
                  </div>
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                    Primary Emergency Contact Person
                  </label>
                  <input 
                    type="text" 
                    value={formData.emergency_contact_name} 
                    onChange={(e) => setFormData({ ...formData, emergency_contact_name: e.target.value })} 
                    className="form-input" 
                    placeholder="e.g. Ramesh Kumar (Spouse / Guardian)"
                  />
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                  <label className="form-label" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                    Medical Conditions, Allergies & Emergency Notes
                  </label>
                  <textarea 
                    rows="3"
                    value={formData.medical_conditions} 
                    onChange={(e) => setFormData({ ...formData, medical_conditions: e.target.value })} 
                    className="form-textarea" 
                    placeholder="No major allergies · Cardiac clearance normal · Regular medication..."
                    style={{ resize: 'vertical', minHeight: '74px' }}
                  ></textarea>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Bottom Action Bar for Profile Save */}
        <div className="glass-panel" style={{ padding: '14px 22px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button 
              type="submit" 
              disabled={saving} 
              className="btn btn-primary" 
              style={{ padding: '10px 24px', fontSize: '0.92rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <Save size={16} /> 
              {saving ? 'Saving...' : 'Save Profile & Telemetry Config'}
            </button>
            <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
              Changes are updated locally and synced to remote command center.
            </span>
          </div>

          {savedMessage && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px', 
              color: '#15803d', 
              background: '#f0fdf4', 
              border: '1px solid #bbf7d0', 
              padding: '6px 14px', 
              borderRadius: '8px', 
              fontSize: '0.85rem',
              fontWeight: 600
            }}>
              <CheckCircle2 size={16} color="#16a34a" />
              {savedMessage}
            </div>
          )}
        </div>
      </form>

      {/* ============================================================ */}
      {/* 3. PERSISTENT OPERATIONAL MEMORY & CACHE STORAGE */}
      {/* ============================================================ */}
      <div className="glass-panel" style={{ padding: '24px 28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h2 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '8px', margin: '0 0 4px 0', color: '#0f172a' }}>
              <Database size={20} color="#0284c7" />
              Operational Memory & High-Speed Cache Center
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>
              Persistent memory storage for {user?.role === 'admin' ? 'HQ incident dispatch logs and hazard cache' : 'navigation trip records, avoided hazards, and destination cache'}
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.75rem', background: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0', padding: '5px 12px', borderRadius: '6px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '5px' }}>
              <HardDrive size={13} /> In-Memory Cache: ACTIVE (TTL: 25s)
            </span>
          </div>
        </div>

        {/* Telemetry Summary Metric Cards (When Driver) */}
        {user?.role !== 'admin' && (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
            gap: '14px', 
            marginBottom: '20px' 
          }}>
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '12px 16px' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>RECORDED DRIVES</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                {tripHistory.length} <span style={{ fontSize: '0.8rem', fontWeight: 500, color: '#64748b' }}>Trips</span>
              </div>
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '12px 16px' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>DISTANCE COVERED</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#0284c7', marginTop: '2px' }}>
                {totalTripDistance} <span style={{ fontSize: '0.8rem', fontWeight: 500, color: '#64748b' }}>km</span>
              </div>
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '12px 16px' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>HAZARDS REROUTED</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#d97706', marginTop: '2px' }}>
                {totalHazardsAvoided} <span style={{ fontSize: '0.8rem', fontWeight: 500, color: '#64748b' }}>Avoided</span>
              </div>
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '12px 16px' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>SAFETY INDEX</div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#16a34a', marginTop: '2px' }}>
                A+ <span style={{ fontSize: '0.8rem', fontWeight: 500, color: '#16a34a' }}>Optimal</span>
              </div>
            </div>
          </div>
        )}

        {/* User / Driver Trip Memory */}
        {user?.role !== 'admin' ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#334155', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <History size={16} color="#0284c7" />
                Driver Trip & Detour History Memory ({tripHistory.length} Recorded Drives)
              </span>
              {tripHistory.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm("Clear trip history memory?")) {
                      localStorage.removeItem('adas_memory_trip_history');
                      setTripHistory([]);
                    }
                  }}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '5px 10px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <Trash2 size={13} /> Clear Trip Memory
                </button>
              )}
            </div>

            <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: '10px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.83rem', textAlign: 'left' }}>
                <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                  <tr>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Date</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Destination</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Distance</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Duration</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Hazards Avoided</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Safety Index</th>
                  </tr>
                </thead>
                <tbody>
                  {tripHistory.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>
                        No trips recorded in local memory yet. Complete a drive navigation session to store trip metrics.
                      </td>
                    </tr>
                  ) : (
                    tripHistory.map((trip, idx) => (
                      <tr key={idx} style={{ borderBottom: idx < tripHistory.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                        <td style={{ padding: '11px 16px', color: '#64748b' }}>{trip.date}</td>
                        <td style={{ padding: '11px 16px', fontWeight: 700, color: '#0f172a' }}>{trip.destination}</td>
                        <td style={{ padding: '11px 16px', color: '#334155' }}>{trip.distanceKm} km</td>
                        <td style={{ padding: '11px 16px', color: '#334155' }}>{trip.durationMin} mins</td>
                        <td style={{ padding: '11px 16px', color: trip.hazardsAvoided > 0 ? '#d97706' : '#059669', fontWeight: 700 }}>
                          {trip.hazardsAvoided > 0 ? `${trip.hazardsAvoided} Hazard(s) Rerouted` : 'Clear Path'}
                        </td>
                        <td style={{ padding: '11px 16px' }}>
                          <span style={{ fontSize: '0.72rem', background: '#f0fdf4', color: '#16a34a', padding: '3px 9px', borderRadius: '4px', fontWeight: 700 }}>
                            {trip.safetyRating || 'A+ (Optimal)'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          /* Admin Incident & Dispatch Memory */
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#334155', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={16} color="#7c3aed" />
                HQ Incident Dispatch & Resolution Memory ({adminIncidents.length} Events)
              </span>
              {adminIncidents.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm("Clear admin incident memory?")) {
                      localStorage.removeItem('adas_memory_admin_incidents');
                      setAdminIncidents([]);
                    }
                  }}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '5px 10px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <Trash2 size={13} /> Clear Incident Memory
                </button>
              )}
            </div>

            <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: '10px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.83rem', textAlign: 'left' }}>
                <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                  <tr>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Incident ID</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Disaster / Hazard Type</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Corridor Location</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Severity</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Time</th>
                    <th style={{ padding: '11px 16px', color: '#475569', fontWeight: 600 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {adminIncidents.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>
                        No incident dispatches stored in local memory.
                      </td>
                    </tr>
                  ) : (
                    adminIncidents.map((inc, idx) => (
                      <tr key={idx} style={{ borderBottom: idx < adminIncidents.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                        <td style={{ padding: '11px 16px', fontWeight: 800, color: '#7c3aed' }}>{inc.id}</td>
                        <td style={{ padding: '11px 16px', fontWeight: 700, color: '#0f172a' }}>{inc.type}</td>
                        <td style={{ padding: '11px 16px', color: '#334155' }}>{inc.location}</td>
                        <td style={{ padding: '11px 16px' }}>
                          <span style={{ 
                            fontSize: '0.72rem', 
                            background: inc.severity === 'CRITICAL' ? '#fee2e2' : '#fef3c7', 
                            color: inc.severity === 'CRITICAL' ? '#dc2626' : '#d97706', 
                            padding: '3px 8px', 
                            borderRadius: '4px', 
                            fontWeight: 700 
                          }}>
                            {inc.severity}
                          </span>
                        </td>
                        <td style={{ padding: '11px 16px', color: '#64748b' }}>{inc.timestamp}</td>
                        <td style={{ padding: '11px 16px' }}>
                          <span style={{ fontSize: '0.72rem', background: '#f1f5f9', color: '#334155', padding: '3px 8px', borderRadius: '4px', fontWeight: 700 }}>
                            {inc.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};

export default Profile;
