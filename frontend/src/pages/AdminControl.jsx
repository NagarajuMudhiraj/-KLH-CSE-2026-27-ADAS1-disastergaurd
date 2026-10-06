import React, { useState, useEffect } from 'react';
import api from '../services/api';
import hazardService from '../services/hazardService';
import cacheService from '../services/cacheService';
import { useAuth } from '../context/AuthContext';
import AdminDashboardOverview from '../components/admin/AdminDashboardOverview';
import AdminHazardMapView from '../components/admin/AdminHazardMapView';
import CreateHazardView from '../components/admin/CreateHazardView';
import VerifyReportsView from '../components/admin/VerifyReportsView';
import ManageHazardsView from '../components/admin/ManageHazardsView';
import AdminSettingsView from '../components/admin/AdminSettingsView';
import Dashboard from './Dashboard';
import { 
  LayoutDashboard, 
  Map, 
  PlusCircle, 
  CheckSquare, 
  Layers, 
  BarChart3, 
  Settings, 
  LogOut, 
  RefreshCw,
  Radio,
  Sliders,
  FileDown
} from 'lucide-react';
import pdfReportService from '../services/pdfReportService';

export const AdminControl = ({ onLogout }) => {
  const { user, logout } = useAuth();

  // 8 Main Options:
  // - Dashboard
  // - Hazard Map
  // - Create Hazard
  // - Verify Reports
  // - Manage Hazards
  // - Analytics
  // - Settings
  // - Logout
  const [activeTab, setActiveTab] = useState('dashboard');

  const [hazards, setHazards] = useState([]);
  const [emergencies, setEmergencies] = useState([]);
  const [loading, setLoading] = useState(true);

  const [pendingCount, setPendingCount] = useState(0);

  const loadData = async () => {
    setLoading(true);
    try {
      cacheService.invalidateCache('active_hazards');
      const [hazardList, sosList, pendingReports] = await Promise.all([
        hazardService.getActiveHazards(true).catch(() => []),
        api.getEmergencyList().catch(() => []),
        api.getAdminReports().catch(() => [])
      ]);
      setHazards(hazardList);
      setEmergencies(sosList);

      const cleanPending = Array.isArray(pendingReports) ? pendingReports.filter(h => 
        !String(h.id || h._id || '').startsWith('hz_rep_') &&
        !['person', 'pedestrian'].includes((h.type || h.disasterType || h.name || '').toLowerCase().trim())
      ) : [];
      setPendingCount(cleanPending.length);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Listen to live WebSocket hazard notifications
    const cleanupWs = hazardService.connectHazardWebSocket((event) => {
      if (event.event === 'NEW_DISASTER_DETECTED' || event.event === 'HAZARD_REPORTED') {
        loadData();
      }
    });

    return () => cleanupWs();
  }, []);

  const handleHazardCreated = (newHazard) => {
    loadData();
    setActiveTab('manage_hazards');
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'hazard_map', label: 'Hazard Map', icon: Map },
    { id: 'create_hazard', label: 'Create Hazard', icon: PlusCircle, highlight: true },
    { id: 'verify_reports', label: 'Verify Reports', icon: CheckSquare, badge: pendingCount },
    { id: 'manage_hazards', label: 'Manage Hazards', icon: Layers, badge: hazards.length },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div style={{ minHeight: 'calc(100vh - 120px)', padding: '20px 24px', background: 'transparent' }}>
      
      {/* Admin Top Menu Bar: 8 Clean Main Options */}
      <div 
        className="glass-panel"
        style={{
          background: 'rgba(255, 255, 255, 0.42)',
          backdropFilter: 'blur(18px) saturate(160%)',
          WebkitBackdropFilter: 'blur(18px) saturate(160%)',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.55)',
          padding: '8px 16px',
          marginBottom: '24px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.05), inset 0 0 0 1px rgba(255, 255, 255, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 16px',
                  borderRadius: '10px',
                  border: isActive ? '1px solid #7c3aed' : '1px solid transparent',
                  background: isActive ? 'rgba(245, 243, 255, 0.9)' : 'transparent',
                  color: isActive ? '#6d28d9' : '#475569',
                  fontWeight: isActive ? 800 : 600,
                  fontSize: '0.86rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={16} color={isActive ? '#6d28d9' : (item.highlight ? '#7c3aed' : '#64748b')} />
                <span>{item.label}</span>
                {item.badge !== undefined && item.badge > 0 && (
                  <span style={{
                    background: isActive ? '#7c3aed' : '#e2e8f0',
                    color: isActive ? '#ffffff' : '#475569',
                    fontSize: '0.7rem',
                    fontWeight: 800,
                    padding: '1px 6px',
                    borderRadius: '10px'
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Right Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => pdfReportService.generateComprehensiveDisasterReport({
              hazards,
              emergencies,
              adminUser: user?.username || 'HQ Incident Commander'
            })}
            className="btn btn-primary"
            style={{
              padding: '8px 16px',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
              border: 'none',
              borderRadius: '10px',
              boxShadow: '0 4px 12px rgba(2, 132, 199, 0.25)',
              color: '#ffffff',
              fontWeight: 700,
              cursor: 'pointer'
            }}
            title="Generate & download official citywide disaster & hazard incident PDF report"
          >
            <FileDown size={15} />
            <span>Export Report (PDF)</span>
          </button>

          <button
            onClick={loadData}
            className="btn btn-secondary"
            style={{ padding: '8px 14px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            title="Sync Database & Hazards"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Main Panel Viewport */}
      <div>
        {/* 1. Dashboard */}
        {activeTab === 'dashboard' && (
          <AdminDashboardOverview
            hazards={hazards}
            emergencies={emergencies}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}

        {/* 2. Hazard Map */}
        {activeTab === 'hazard_map' && (
          <AdminHazardMapView
            hazards={hazards}
            onNavigateToCreate={() => setActiveTab('create_hazard')}
            onRefresh={loadData}
          />
        )}

        {/* 3. Create Hazard */}
        {activeTab === 'create_hazard' && (
          <CreateHazardView
            onHazardCreated={handleHazardCreated}
            onCancel={() => setActiveTab('dashboard')}
            onViewOnMap={() => setActiveTab('hazard_map')}
          />
        )}

        {/* 4. Verify Reports */}
        {activeTab === 'verify_reports' && (
          <VerifyReportsView
            onRefresh={loadData}
          />
        )}

        {/* 5. Manage Hazards */}
        {activeTab === 'manage_hazards' && (
          <ManageHazardsView
            hazards={hazards}
            onRefresh={loadData}
            onNavigateToCreate={() => setActiveTab('create_hazard')}
          />
        )}

        {/* 6. Analytics */}
        {activeTab === 'analytics' && (
          <Dashboard setActiveTab={setActiveTab} />
        )}

        {/* 7. Settings */}
        {activeTab === 'settings' && (
          <AdminSettingsView />
        )}
      </div>
    </div>
  );
};

export default AdminControl;
