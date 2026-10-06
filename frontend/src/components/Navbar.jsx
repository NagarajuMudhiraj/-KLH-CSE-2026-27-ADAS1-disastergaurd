import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  ShieldAlert, 
  Compass, 
  AlertTriangle, 
  Sliders, 
  User, 
  LogIn,
  LogOut
} from 'lucide-react';

const Navbar = ({ activePortal, activeTab, setActiveTab, onLogout }) => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <nav className="navbar">
      {/* Brand - strictly isolated to current portal */}
      <div className="nav-brand" style={{ cursor: 'default' }}>
        <ShieldAlert size={28} color={activePortal === 'admin' ? '#7c3aed' : '#0284c7'} />
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ letterSpacing: '-0.03em', lineHeight: 1.1, fontSize: '1.2rem', color: '#0f172a' }}>
            DISASTER<span style={{ color: activePortal === 'admin' ? '#7c3aed' : '#0284c7' }}>SHIELD</span>
          </span>
          <span style={{ fontSize: '0.65rem', color: activePortal === 'admin' ? '#7c3aed' : '#0284c7', letterSpacing: '0.08em', fontWeight: 800 }}>
            {activePortal === 'admin' ? 'HQ INCIDENT COMMAND CENTER' : 'DRIVER ADAS & VEHICLE CONSOLE'}
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <ul className="nav-links">
        {!isAuthenticated ? (
          // ==================== PUBLIC / UNVERIFIED VISITOR TABS ====================
          <>
            <li>
              <button
                className={`nav-btn ${activeTab === 'login' ? 'active' : ''}`}
                onClick={() => setActiveTab('login')}
                style={{ color: '#0284c7', fontWeight: 700 }}
              >
                <LogIn size={18} />
                <span>Portal Login</span>
              </button>
            </li>
            <li>
              <button
                className={`nav-btn ${activeTab === 'roadsafety' ? 'active' : ''}`}
                onClick={() => setActiveTab('roadsafety')}
              >
                <Compass size={18} />
                <span>Public Live Map</span>
              </button>
            </li>
            <li>
              <button
                className={`nav-btn ${activeTab === 'sos' ? 'active' : ''}`}
                onClick={() => setActiveTab('sos')}
              >
                <AlertTriangle size={18} />
                <span>Emergency SOS</span>
              </button>
            </li>
          </>
        ) : activePortal === 'user' ? (
          // ==================== USER / DRIVER PANEL TABS ONLY ====================
          <>
            <li>
              <button
                className={`nav-btn ${activeTab === 'roadsafety' ? 'active' : ''}`}
                onClick={() => setActiveTab('roadsafety')}
              >
                <Compass size={18} />
                <span>Live Map</span>
              </button>
            </li>
            <li>
              <button
                className="nav-btn"
                onClick={() => {
                  setActiveTab('roadsafety');
                  setTimeout(() => {
                    window.dispatchEvent(new CustomEvent('open-driver-hazard-report'));
                  }, 50);
                }}
                style={{
                  background: 'rgba(234, 88, 12, 0.1)',
                  color: '#ea580c',
                  border: '1px solid rgba(234, 88, 12, 0.25)',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
                title="Report a Road Hazard with Photo Snapshot & GPS"
              >
                <AlertTriangle size={16} color="#ea580c" />
                <span>Report Hazard</span>
              </button>
            </li>
            <li>
              <button
                className={`nav-btn ${activeTab === 'sos' ? 'active' : ''}`}
                onClick={() => setActiveTab('sos')}
              >
                <AlertTriangle size={18} />
                <span>Emergency</span>
              </button>
            </li>
            <li>
              <button
                className={`nav-btn ${activeTab === 'profile' ? 'active' : ''}`}
                onClick={() => setActiveTab('profile')}
              >
                <User size={18} />
                <span>Profile</span>
              </button>
            </li>
            <li>
              <button
                className="nav-btn"
                onClick={() => {
                  if (onLogout) {
                    onLogout();
                  } else {
                    logout();
                    setActiveTab('login');
                  }
                }}
                style={{ color: '#dc2626', fontWeight: 700 }}
                title="Log Out"
              >
                <LogOut size={18} />
                <span>Logout</span>
              </button>
            </li>
          </>
        ) : (
          // ==================== ADMIN PANEL TABS ONLY ====================
          <>
            <li>
              <button
                className={`nav-btn ${activeTab === 'admin' ? 'active' : ''}`}
                onClick={() => setActiveTab('admin')}
              >
                <Sliders size={18} />
                <span>Admin Command Center</span>
              </button>
            </li>
            <li>
              <button
                className="nav-btn"
                onClick={() => {
                  if (onLogout) {
                    onLogout();
                  } else {
                    logout();
                    setActiveTab('login');
                  }
                }}
                style={{ 
                  color: '#dc2626', 
                  fontWeight: 800,
                  border: '1px solid #fee2e2',
                  background: '#fef2f2',
                  borderRadius: '8px'
                }}
                title="Logout of Admin Command Center"
              >
                <LogOut size={18} color="#dc2626" />
                <span>Logout</span>
              </button>
            </li>
          </>
        )}
      </ul>

    </nav>
  );
};

export default Navbar;
