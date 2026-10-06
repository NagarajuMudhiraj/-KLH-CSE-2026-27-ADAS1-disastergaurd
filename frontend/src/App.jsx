import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import LoginModal from './components/LoginModal';
import Dashboard from './pages/Dashboard';
import Detection from './pages/Detection';
import RoadSafety from './pages/RoadSafety';
import DisasterRadar from './pages/DisasterRadar';
import EmergencySOS from './pages/EmergencySOS';
import AdminControl from './pages/AdminControl';
import Profile from './pages/Profile';
import LoginPage from './pages/LoginPage';

function AppContent() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  
  // Set active portal strictly according to authenticated user role
  const [activePortal, setActivePortal] = useState(() => (user?.role === 'admin' ? 'admin' : 'user'));
  const [activeTab, setActiveTab] = useState(() => {
    if (!user) return 'login';
    return user?.role === 'admin' ? 'admin' : 'roadsafety';
  });
  
  // Login Modal state
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  // When user signs in, changes account, or logs out, automatically switch to dedicated panel or login
  useEffect(() => {
    if (user?.role === 'admin') {
      setActivePortal('admin');
      setActiveTab('admin');
    } else if (user?.role === 'driver') {
      setActivePortal('user');
      setActiveTab('roadsafety');
    } else {
      if (window.location.pathname !== '/') {
        window.history.replaceState(null, '', '/');
      }
      setActivePortal('user');
      setActiveTab('login');
    }
  }, [user]);

  // Clean initial path if visitor visits /admin without credentials
  useEffect(() => {
    if (window.location.pathname === '/admin' && (!user || user?.role !== 'admin')) {
      window.history.replaceState(null, '', '/');
      setActivePortal('user');
      setActiveTab('login');
    }
  }, []);

  const handleOpenLogin = () => {
    setActiveTab('login');
  };

  const handleLogout = () => {
    logout();
    if (window.location.pathname !== '/') {
      window.history.replaceState(null, '', '/');
    }
    setActivePortal('user');
    setActiveTab('login');
  };

  const handleLoginSuccess = (loggedInUser) => {
    if (loggedInUser.role === 'admin') {
      setActivePortal('admin');
      setActiveTab('admin');
    } else {
      setActivePortal('user');
      setActiveTab('roadsafety');
    }
  };

  return (
    <div className="app-container">
      {/* Top Navigation Bar - Hidden on dedicated Login Page */}
      {activeTab !== 'login' && (
        <Navbar 
          activePortal={activePortal} 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          onOpenLoginModal={handleOpenLogin}
          onLogout={handleLogout}
        />
      )}

      {/* Login / Auth Modal */}
      <LoginModal 
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      {/* Main Workspace */}
      <main className={`main-content ${
        activeTab === 'login' 
          ? 'main-content-login' 
          : (activeTab === 'roadsafety' || activeTab === 'radar' ? 'main-content-full' : '')
      }`}>
        {activeTab === 'login' ? (
          <LoginPage 
            onLoginSuccess={handleLoginSuccess} 
            onExploreAsGuest={() => {
              setActivePortal('user');
              setActiveTab('roadsafety');
            }}
          />
        ) : activePortal === 'admin' ? (
          // ==================== ADMIN PANEL VIEWS ONLY ====================
          <>
            {activeTab === 'admin' && <AdminControl setActiveTab={setActiveTab} onLogout={handleLogout} />}
            {activeTab === 'dashboard' && <Dashboard setActiveTab={setActiveTab} />}
            {activeTab === 'radar' && <DisasterRadar setActiveTab={setActiveTab} />}
          </>
        ) : (
          // ==================== USER / DRIVER PANEL VIEWS ONLY ====================
          <>
            {activeTab === 'roadsafety' && <RoadSafety setActiveTab={setActiveTab} />}
            {activeTab === 'radar' && <DisasterRadar setActiveTab={setActiveTab} />}
            {activeTab === 'detection' && <Detection setActiveTab={setActiveTab} />}
            {activeTab === 'sos' && <EmergencySOS setActiveTab={setActiveTab} />}
            {activeTab === 'profile' && <Profile setActiveTab={setActiveTab} />}
            {!['roadsafety', 'radar', 'detection', 'sos', 'profile'].includes(activeTab) && (
              <RoadSafety setActiveTab={setActiveTab} />
            )}
          </>
        )}
      </main>

    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
