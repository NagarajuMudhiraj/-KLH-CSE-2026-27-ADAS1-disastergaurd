import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, Car, Sliders, Lock, User, Mail, Eye, EyeOff, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';

const LoginModal = ({ isOpen, onClose, targetRole = null, onLoginSuccess }) => {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form states
  const [username, setUsername] = useState(targetRole === 'admin' ? 'admin' : 'driver');
  const [password, setPassword] = useState(targetRole === 'admin' ? 'admin123' : 'driver123');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState(targetRole === 'admin' ? 'admin' : 'driver');

  if (!isOpen) return null;

  const handleQuickFill = (type) => {
    setError('');
    setSuccessMsg('');
    if (type === 'driver') {
      setUsername('driver');
      setPassword('driver123');
      setRole('driver');
    } else {
      setUsername('admin');
      setPassword('admin123');
      setRole('admin');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      if (isRegister) {
        if (!email.includes('@')) {
          setError('Please provide a valid email address.');
          setLoading(false);
          return;
        }
        const res = await register({ username, email, password, role });
        if (res.success) {
          const destination = res.user.role === 'admin' ? 'Admin Command Center' : 'Driver ADAS Console';
          setSuccessMsg(`Account registered! Routing to ${destination}...`);
          setTimeout(() => {
            if (onLoginSuccess) onLoginSuccess(res.user);
            onClose();
          }, 800);
        } else {
          setError(res.error || 'Registration failed.');
        }
      } else {
        const res = await login(username, password);
        if (res.success) {
          const destination = res.user.role === 'admin' ? 'Admin Command Center' : 'Driver ADAS Console';
          setSuccessMsg(`Login verified (${res.user.role.toUpperCase()})! Launching ${destination}...`);
          setTimeout(() => {
            if (onLoginSuccess) onLoginSuccess(res.user);
            onClose();
          }, 800);
        } else {
          setError(res.error || 'Invalid username or password.');
        }
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Authentication service error.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(15, 23, 42, 0.55)',
        backdropFilter: 'blur(5px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 3000,
        padding: '16px'
      }}
      onClick={onClose}
    >
      <div 
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '460px',
          background: 'rgba(255, 255, 255, 0.42)',
          backdropFilter: 'blur(24px) saturate(170%)',
          WebkitBackdropFilter: 'blur(24px) saturate(170%)',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.6)',
          boxShadow: '0 25px 60px rgba(15, 23, 42, 0.25), inset 0 0 0 1px rgba(255, 255, 255, 0.4)',
          padding: '28px',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Icon & Title */}
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div 
            style={{
              width: '54px',
              height: '54px',
              margin: '0 auto 12px',
              borderRadius: '14px',
              background: role === 'admin' ? '#f5f3ff' : '#f0f9ff',
              border: `1px solid ${role === 'admin' ? '#ddd6fe' : '#bae6fd'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {role === 'admin' ? (
              <Sliders size={28} color="#7c3aed" />
            ) : (
              <Car size={28} color="#0284c7" />
            )}
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a', margin: '0 0 6px 0' }}>
            {isRegister ? 'Create DisaterShield Account' : 'Sign In to Portal'}
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
            {isRegister 
              ? 'Choose your role to get automated access to the respective panel.'
              : 'Enter your credentials. You will automatically be routed to your panel.'
            }
          </p>
        </div>

        {/* Quick Demo Pre-fill Buttons */}
        {!isRegister && (
          <div style={{ marginBottom: '18px' }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', marginBottom: '8px' }}>
              Quick Demo Logins (Click to load):
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <button
                type="button"
                onClick={() => handleQuickFill('driver')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: username === 'driver' ? '2px solid #0284c7' : '1px solid #e2e8f0',
                  background: username === 'driver' ? '#f0f9ff' : '#f8fafc',
                  cursor: 'pointer',
                  textAlign: 'left'
                }}
              >
                <Car size={16} color="#0284c7" />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.8rem', color: '#0f172a' }}>Driver Panel</div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>driver / driver123</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickFill('admin')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: username === 'admin' ? '2px solid #7c3aed' : '1px solid #e2e8f0',
                  background: username === 'admin' ? '#f5f3ff' : '#f8fafc',
                  cursor: 'pointer',
                  textAlign: 'left'
                }}
              >
                <Sliders size={16} color="#7c3aed" />
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.8rem', color: '#0f172a' }}>Admin HQ</div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>admin / admin123</div>
                </div>
              </button>
            </div>
          </div>
        )}

        {/* Feedback messages */}
        {error && (
          <div 
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#dc2626',
              fontSize: '0.82rem',
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
              borderRadius: '8px',
              background: '#ecfdf5',
              border: '1px solid #a7f3d0',
              color: '#059669',
              fontSize: '0.82rem',
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

        {/* Auth Form */}
        <form onSubmit={handleSubmit}>
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
              className="form-input"
              placeholder="e.g. driver or admin"
            />
          </div>

          {/* Email (If registering) */}
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
                className="form-input"
                placeholder="name@emergency.org"
              />
            </div>
          )}

          {/* Password */}
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
                className="form-input"
                placeholder="••••••••"
                style={{ paddingRight: '40px' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#94a3b8'
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Role selector if Registering */}
          {isRegister && (
            <div className="form-group">
              <label className="form-label">Assign Portal Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="form-select"
              >
                <option value="driver">🚗 Vehicle Driver (Driver ADAS Console)</option>
                <option value="admin">🛡️ HQ Incident Commander (Admin Command Center)</option>
              </select>
            </div>
          )}

          {/* Destination notice */}
          <div 
            style={{
              padding: '10px 12px',
              borderRadius: '8px',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              fontSize: '0.78rem',
              color: '#475569',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <ArrowRight size={14} color="#0284c7" />
            <span>
              Role routing: <strong>Admin</strong> opens HQ Command Center; <strong>Driver</strong> opens ADAS Vehicle Console.
            </span>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
              style={{
                flex: 1,
                padding: '10px 16px',
                fontSize: '0.9rem',
                fontWeight: 700,
                background: username === 'admin' || role === 'admin' ? '#7c3aed' : '#0284c7'
              }}
            >
              {loading ? 'Authenticating...' : isRegister ? 'Register & Open Portal' : 'Sign In'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              style={{ padding: '10px 16px' }}
            >
              Cancel
            </button>
          </div>
        </form>

        {/* Toggle between Login and Register */}
        <div style={{ marginTop: '18px', textAlign: 'center', fontSize: '0.82rem', color: '#64748b' }}>
          {isRegister ? (
            <span>
              Already registered?{' '}
              <button
                type="button"
                onClick={() => { setIsRegister(false); setError(''); setSuccessMsg(''); }}
                style={{ background: 'transparent', border: 'none', color: '#0284c7', fontWeight: 700, cursor: 'pointer', textDecoration: 'underline' }}
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Need a new account?{' '}
              <button
                type="button"
                onClick={() => { setIsRegister(true); setError(''); setSuccessMsg(''); }}
                style={{ background: 'transparent', border: 'none', color: '#0284c7', fontWeight: 700, cursor: 'pointer', textDecoration: 'underline' }}
              >
                Create Account
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginModal;
