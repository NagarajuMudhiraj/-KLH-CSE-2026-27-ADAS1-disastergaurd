import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import mapboxService from '../../services/mapboxService';
import { 
  Sliders, 
  ShieldCheck, 
  MapPin, 
  Key, 
  Radio, 
  Server, 
  Bell, 
  Save, 
  CheckCircle2 
} from 'lucide-react';

export const AdminSettingsView = () => {
  const { user } = useAuth();
  const [savedNotice, setSavedNotice] = useState(false);

  const [settings, setSettings] = useState({
    defaultHazardRadius: 2.5,
    autoBroadcastOnCreate: true,
    riskThreshold: 'Medium',
    audioAlertsEnabled: true,
    cityBoundary: 'Hyderabad Metropolitan Region'
  });

  const handleSave = (e) => {
    e.preventDefault();
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  const isMapboxConfigured = mapboxService.isConfigured();

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '1.4rem', fontWeight: 900, color: '#0f172a', margin: 0 }}>
          Admin Panel Configuration & Settings
        </h1>
        <p style={{ fontSize: '0.86rem', color: '#64748b', margin: '2px 0 0' }}>
          Configure emergency dispatch parameters, hazard broadcast sensitivity, and mapping credentials.
        </p>
      </div>

      {savedNotice && (
        <div style={{
          background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '10px',
          padding: '12px 18px', marginBottom: '20px', color: '#166534', fontSize: '0.86rem',
          display: 'flex', alignItems: 'center', gap: '8px'
        }}>
          <CheckCircle2 size={18} />
          <span>Configuration saved successfully.</span>
        </div>
      )}

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* System & Mapbox Status */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={18} color="#0284c7" />
            Core Integrations & Map Provider
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.86rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div>
                <strong>Mapbox GL JS & Geocoding v6</strong>
                <div style={{ fontSize: '0.76rem', color: '#64748b' }}>Primary map engine & forward/reverse address geocoding</div>
              </div>
              <span className={`badge ${isMapboxConfigured ? 'badge-safe' : 'badge-danger'}`}>
                {isMapboxConfigured ? 'Configured & Active' : 'Token Missing'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div>
                <strong>ADAS Backend REST API</strong>
                <div style={{ fontSize: '0.76rem', color: '#64748b' }}>FastAPI service running on http://localhost:8000</div>
              </div>
              <span className="badge badge-safe">Online</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div>
                <strong>Disaster WebSocket Feed</strong>
                <div style={{ fontSize: '0.76rem', color: '#64748b' }}>Real-time event stream at ws://localhost:8000/ws/disasters</div>
              </div>
              <span className="badge badge-safe">Active Stream</span>
            </div>
          </div>
        </div>

        {/* Hazard Broadcast Policies */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Radio size={18} color="#7c3aed" />
            Hazard Broadcast & Detour Policies
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Default Danger Perimeter (km)</label>
              <input
                type="number"
                step="0.5"
                min="0.5"
                max="50"
                value={settings.defaultHazardRadius}
                onChange={(e) => setSettings({ ...settings, defaultHazardRadius: parseFloat(e.target.value) })}
                className="form-input"
              />
              <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                Vehicles navigating within this perimeter of an Admin hazard are automatically offered detour bypasses.
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0' }}>
              <input
                type="checkbox"
                id="autoBroadcast"
                checked={settings.autoBroadcastOnCreate}
                onChange={(e) => setSettings({ ...settings, autoBroadcastOnCreate: e.target.checked })}
                style={{ width: '18px', height: '18px' }}
              />
              <label htmlFor="autoBroadcast" style={{ fontSize: '0.86rem', fontWeight: 700, color: '#0f172a', cursor: 'pointer' }}>
                Automatically broadcast WebSocket alert when an Admin hazard is published
              </label>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '4px 0' }}>
              <input
                type="checkbox"
                id="audioAlerts"
                checked={settings.audioAlertsEnabled}
                onChange={(e) => setSettings({ ...settings, audioAlertsEnabled: e.target.checked })}
                style={{ width: '18px', height: '18px' }}
              />
              <label htmlFor="audioAlerts" style={{ fontSize: '0.86rem', fontWeight: 700, color: '#0f172a', cursor: 'pointer' }}>
                Enable Speech Synthesis voice alert broadcasts on driver console
              </label>
            </div>
          </div>
        </div>

        {/* Admin Account Credentials Summary */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={18} color="#16a34a" />
            Current Authenticated Authority
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.84rem' }}>
            <div>
              <span style={{ color: '#64748b', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700 }}>USERNAME</span>
              <div style={{ fontWeight: 800, color: '#0f172a' }}>{user?.username || 'admin'}</div>
            </div>
            <div>
              <span style={{ color: '#64748b', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700 }}>ROLE</span>
              <div style={{ fontWeight: 800, color: '#7c3aed' }}>HQ INCIDENT COMMANDER (ADMIN)</div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ padding: '12px 24px', fontSize: '0.9rem', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
        >
          <Save size={16} /> Save Settings
        </button>
      </form>
    </div>
  );
};

export default AdminSettingsView;
