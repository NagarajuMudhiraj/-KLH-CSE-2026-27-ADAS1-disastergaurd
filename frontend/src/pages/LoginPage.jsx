import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  ShieldAlert,
  User,
  Lock,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export const LoginPage = ({ onLoginSuccess, onExploreAsGuest }) => {
  const { login, register } = useAuth();

  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form Fields
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('driver');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!username.trim() || !password.trim()) {
      setError('Please provide both username and password.');
      return;
    }

    setLoading(true);

    try {
      if (isRegister) {
        if (!email || !email.includes('@')) {
          setError('Please provide a valid email address for registration.');
          setLoading(false);
          return;
        }

        const res = await register({
          username: username.trim(),
          email: email.trim(),
          password: password,
          role: role
        });

        if (res.success) {
          const portalName = res.user.role === 'admin' ? 'HQ Incident Command Center' : 'Driver ADAS Console';
          setSuccessMsg(`Account created! Launching ${portalName}...`);
          setTimeout(() => {
            if (onLoginSuccess) onLoginSuccess(res.user);
          }, 600);
        } else {
          setError(res.error || 'Registration failed. Username may already exist.');
        }
      } else {
        const res = await login(username.trim(), password);
        if (res.success) {
          const portalName = res.user.role === 'admin' ? 'HQ Incident Command Center' : 'Driver ADAS Console';
          setSuccessMsg(`Welcome, ${res.user.username}! Launching ${portalName}...`);
          setTimeout(() => {
            if (onLoginSuccess) onLoginSuccess(res.user);
          }, 600);
        } else {
          setError(res.error || 'Invalid credentials. Check username/password.');
        }
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Authentication server unavailable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-wrapper">
      <div className="login-card-glass glass-panel">
        {/* Brand / Logo Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.55)',
              border: '1px solid rgba(255, 255, 255, 0.75)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
              color: '#0284c7',
              width: '58px',
              height: '58px',
              borderRadius: '16px',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 16px rgba(2, 132, 199, 0.15)',
              marginBottom: '14px'
            }}
          >
            <ShieldAlert size={32} />
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#0f172a', margin: '0 0 6px 0', textShadow: '0 1px 2px rgba(255, 255, 255, 0.5)' }}>
            DisasterShield
          </h1>
          <p style={{ fontSize: '0.82rem', color: '#334155', fontWeight: 500, margin: 0 }}>
            Intelligent Disaster Mobility & Hazard Response Console
          </p>
        </div>

        {/* Tab Toggle: Sign In / Create Account */}
        <div
          style={{
            display: 'flex',
            background: 'rgba(255, 255, 255, 0.35)',
            border: '1px solid rgba(255, 255, 255, 0.5)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            padding: '4px',
            borderRadius: '12px',
            marginBottom: '20px'
          }}
        >
          <button
            type="button"
            onClick={() => {
              setIsRegister(false);
              setError('');
              setSuccessMsg('');
            }}
            style={{
              flex: 1,
              padding: '9px',
              border: 'none',
              borderRadius: '9px',
              background: !isRegister ? 'rgba(255, 255, 255, 0.82)' : 'transparent',
              color: !isRegister ? '#0f172a' : '#475569',
              fontWeight: !isRegister ? 700 : 500,
              fontSize: '0.85rem',
              cursor: 'pointer',
              boxShadow: !isRegister ? '0 2px 6px rgba(0,0,0,0.08)' : 'none',
              transition: 'all 0.15s ease'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsRegister(true);
              setError('');
              setSuccessMsg('');
            }}
            style={{
              flex: 1,
              padding: '9px',
              border: 'none',
              borderRadius: '9px',
              background: isRegister ? 'rgba(255, 255, 255, 0.82)' : 'transparent',
              color: isRegister ? '#0f172a' : '#475569',
              fontWeight: isRegister ? 700 : 500,
              fontSize: '0.85rem',
              cursor: 'pointer',
              boxShadow: isRegister ? '0 2px 6px rgba(0,0,0,0.08)' : 'none',
              transition: 'all 0.15s ease'
            }}
          >
            Register
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div
            style={{
              padding: '10px 14px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '8px',
              color: '#dc2626',
              fontSize: '0.82rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px'
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div
            style={{
              padding: '10px 14px',
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '8px',
              color: '#16a34a',
              fontSize: '0.82rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px'
            }}
          >
            <CheckCircle2 size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Username */}
          <div className="form-group">
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <User size={14} color="#64748b" />
              Username
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. driver or admin"
              className="form-input"
            />
          </div>

          {/* Email (Registration only) */}
          {isRegister && (
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Mail size={14} color="#64748b" />
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@emergency.org"
                className="form-input"
              />
            </div>
          )}

          {/* Role selector (Registration only) */}
          {isRegister && (
            <div className="form-group">
              <label className="form-label">Account Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="form-input"
              >
                <option value="driver">Driver & Citizen</option>
                <option value="admin">HQ Incident Commander (Admin)</option>
              </select>
            </div>
          )}

          {/* Password with Eye Toggle */}
          <div className="form-group">
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Lock size={14} color="#64748b" />
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="form-input"
                style={{ paddingRight: '40px' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{
              marginTop: '8px',
              padding: '13px',
              fontSize: '0.92rem',
              fontWeight: 700,
              background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
              borderColor: '#0284c7',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            {loading ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span>{isRegister ? 'Create Account' : 'Sign In'}</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

      </div>
    </div>
  );
};

export default LoginPage;
