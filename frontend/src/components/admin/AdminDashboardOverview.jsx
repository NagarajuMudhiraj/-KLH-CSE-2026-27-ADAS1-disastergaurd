import React from 'react';
import { 
  ShieldAlert, 
  Plus, 
  Map, 
  CheckCircle, 
  Layers, 
  Cpu, 
  User, 
  Radio, 
  AlertTriangle, 
  ArrowRight,
  ShieldCheck,
  Activity,
  FileDown
} from 'lucide-react';
import pdfReportService from '../../services/pdfReportService';

export const AdminDashboardOverview = ({ hazards = [], emergencies = [], onNavigateTab }) => {
  const adminHazards = hazards.filter((h) => (h.source || (h.created_by ? 'ADMIN' : '')).toUpperCase() === 'ADMIN');
  const aiHazards = hazards.filter((h) => (h.source || '').toUpperCase() === 'AI' || (!h.source && !h.created_by && !h.reported_by));
  const userHazards = hazards.filter((h) => (h.source || (h.reported_by ? 'USER' : '')).toUpperCase() === 'USER');

  const pendingSOS = emergencies.filter((e) => (e.status || 'Pending') === 'Pending');

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0f172a', margin: 0 }}>
            Incident Command Dashboard
          </h1>
          <p style={{ fontSize: '0.88rem', color: '#64748b', margin: '3px 0 0' }}>
            City disaster risk status, live road hazards, and autonomous vehicle safety coordination.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={() => pdfReportService.generateComprehensiveDisasterReport({ hazards, emergencies })}
            style={{
              background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
              color: '#fff',
              border: 'none',
              borderRadius: '10px',
              padding: '10px 18px',
              fontWeight: 800,
              fontSize: '0.88rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.3)'
            }}
            title="Download formatted multi-page incident audit PDF"
          >
            <FileDown size={18} /> Export Incident Audit (PDF)
          </button>

          <button
            onClick={() => onNavigateTab('create_hazard')}
            style={{
              background: '#7c3aed',
              color: '#fff',
              border: 'none',
              borderRadius: '10px',
              padding: '10px 20px',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(124, 58, 237, 0.4)'
            }}
          >
            <Plus size={18} /> Create New Hazard
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        
        {/* Total Hazards */}
        <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #0284c7' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 800, textTransform: 'uppercase' }}>
                TOTAL CITY HAZARDS
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#0f172a', marginTop: '4px' }}>
                {hazards.length}
              </div>
            </div>
            <div style={{ background: '#f0f9ff', padding: '10px', borderRadius: '10px', color: '#0284c7' }}>
              <Layers size={22} />
            </div>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#0369a1', marginTop: '8px', fontWeight: 600 }}>
            Active across road network
          </div>
        </div>

        {/* Admin Created Hazards */}
        <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #7c3aed' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 800, textTransform: 'uppercase' }}>
                ADMIN CREATED HAZARDS
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#6d28d9', marginTop: '4px' }}>
                {adminHazards.length}
              </div>
            </div>
            <div style={{ background: '#f5f3ff', padding: '10px', borderRadius: '10px', color: '#7c3aed' }}>
              <ShieldCheck size={22} />
            </div>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#6d28d9', marginTop: '8px', fontWeight: 600 }}>
            Broadcasted directly to driver HUDs
          </div>
        </div>

        {/* AI Vision Detections */}
        <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #06b6d4' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 800, textTransform: 'uppercase' }}>
                AI DETECTED (YOLOV11)
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#0891b2', marginTop: '4px' }}>
                {aiHazards.length}
              </div>
            </div>
            <div style={{ background: '#ecfeff', padding: '10px', borderRadius: '10px', color: '#0891b2' }}>
              <Cpu size={22} />
            </div>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#0e7490', marginTop: '8px', fontWeight: 600 }}>
            Camera & sensor inference stream
          </div>
        </div>

        {/* User / Driver Reports */}
        <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 800, textTransform: 'uppercase' }}>
                USER FIELD REPORTS
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#b45309', marginTop: '4px' }}>
                {userHazards.length}
              </div>
            </div>
            <div style={{ background: '#fef3c7', padding: '10px', borderRadius: '10px', color: '#b45309' }}>
              <User size={22} />
            </div>
          </div>
          <div style={{ fontSize: '0.78rem', color: '#92400e', marginTop: '8px', fontWeight: 600 }}>
            Community crowd reports
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', marginBottom: '14px' }}>
          Quick Incident Actions
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
          
          <div 
            onClick={() => onNavigateTab('create_hazard')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.2s ease', border: '1px solid #ddd6fe' }}
            onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-3px)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <div style={{ background: '#7c3aed', color: '#fff', padding: '8px', borderRadius: '8px' }}>
                <Plus size={20} />
              </div>
              <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>Create Hazard</strong>
            </div>
            <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0 0 12px' }}>
              Click map or search location to drop a live hazard pin and notify vehicles.
            </p>
            <span style={{ fontSize: '0.82rem', color: '#7c3aed', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}>
              Open Creator ➔
            </span>
          </div>

          <div 
            onClick={() => onNavigateTab('hazard_map')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.2s ease', border: '1px solid #bae6fd' }}
            onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-3px)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <div style={{ background: '#0284c7', color: '#fff', padding: '8px', borderRadius: '8px' }}>
                <Map size={20} />
              </div>
              <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>Hazard Map</strong>
            </div>
            <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0 0 12px' }}>
              View city-wide geospatial distribution of admin, AI, and driver hazards.
            </p>
            <span style={{ fontSize: '0.82rem', color: '#0284c7', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}>
              Launch Live Map ➔
            </span>
          </div>

          <div 
            onClick={() => onNavigateTab('manage_hazards')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.2s ease', border: '1px solid #e2e8f0' }}
            onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-3px)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <div style={{ background: '#334155', color: '#fff', padding: '8px', borderRadius: '8px' }}>
                <Layers size={20} />
              </div>
              <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>Manage Hazards</strong>
            </div>
            <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0 0 12px' }}>
              Edit, activate, deactivate, or delete existing hazards with Source tags.
            </p>
            <span style={{ fontSize: '0.82rem', color: '#334155', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}>
              Manage Database ➔
            </span>
          </div>

          <div 
            onClick={() => onNavigateTab('verify_reports')}
            className="glass-panel"
            style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.2s ease', border: '1px solid #fde68a' }}
            onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-3px)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <div style={{ background: '#d97706', color: '#fff', padding: '8px', borderRadius: '8px' }}>
                <CheckCircle size={20} />
              </div>
              <strong style={{ fontSize: '1.05rem', color: '#0f172a' }}>Verify Reports</strong>
            </div>
            <p style={{ fontSize: '0.82rem', color: '#64748b', margin: '0 0 12px' }}>
              Review pending reports submitted by drivers and field observers.
            </p>
            <span style={{ fontSize: '0.82rem', color: '#d97706', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '4px' }}>
              Review Queue ➔
            </span>
          </div>
        </div>
      </div>

      {/* Recent Hazards List */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
            Recent Network Hazards
          </h3>
          <button 
            onClick={() => onNavigateTab('manage_hazards')}
            style={{ background: 'none', border: 'none', color: '#7c3aed', fontWeight: 800, cursor: 'pointer', fontSize: '0.82rem' }}
          >
            View All ({hazards.length}) ➔
          </button>
        </div>

        <div className="hud-table-wrapper">
          <table className="hud-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Hazard Type</th>
                <th>Severity</th>
                <th>Location</th>
                <th>Description</th>
                <th>Created At</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {hazards.slice(0, 5).map((h, idx) => {
                const src = (h.source || (h.created_by ? 'ADMIN' : (h.reported_by ? 'USER' : 'AI'))).toUpperCase();
                return (
                  <tr key={h._id || h.id || idx}>
                    <td>
                      <span style={{
                        padding: '2px 8px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 800,
                        background: src === 'ADMIN' ? '#f5f3ff' : (src === 'USER' ? '#fef3c7' : '#f0f9ff'),
                        color: src === 'ADMIN' ? '#6d28d9' : (src === 'USER' ? '#b45309' : '#0369a1')
                      }}>
                        {src}
                      </span>
                    </td>
                    <td><strong>{h.name || h.type || 'Hazard'}</strong></td>
                    <td>
                      <span className={`badge ${
                        h.severity?.toLowerCase() === 'critical' ? 'badge-danger' : 
                        h.severity?.toLowerCase() === 'high' ? 'badge-warning' : 'badge-safe'
                      }`}>
                        {h.severity || 'High'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.82rem' }}>{h.address || 'Road Segment'}</td>
                    <td style={{ fontSize: '0.82rem', color: '#475569' }}>{h.description || '—'}</td>
                    <td style={{ fontSize: '0.78rem', color: '#64748b' }}>
                      {new Date(h.start_time || h.timestamp || h.createdAt || Date.now()).toLocaleTimeString()}
                    </td>
                    <td>
                      <span className="badge badge-safe">{h.status || 'ACTIVE'}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardOverview;
