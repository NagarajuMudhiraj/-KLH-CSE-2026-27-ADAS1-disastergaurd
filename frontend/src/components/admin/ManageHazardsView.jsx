import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import cacheService from '../../services/cacheService';
import { 
  ShieldAlert, 
  Plus, 
  Search, 
  Trash2, 
  Edit3, 
  CheckCircle, 
  Power, 
  MapPin, 
  Clock, 
  AlertTriangle, 
  Sliders, 
  X, 
  Loader2,
  Cpu,
  User,
  ShieldCheck,
  FileDown
} from 'lucide-react';
import pdfReportService from '../../services/pdfReportService';

const SEVERITY_COLORS = {
  Critical: '#dc2626',
  High: '#ea580c',
  Medium: '#f59e0b',
  Low: '#10b981'
};

export const ManageHazardsView = ({ hazards = [], onRefresh, onNavigateToCreate }) => {
  const [localHazards, setLocalHazards] = useState(hazards);
  const [busyIds, setBusyIds] = useState({});
  const [sourceFilter, setSourceFilter] = useState('ALL'); // 'ALL', 'ADMIN', 'AI', 'USER'
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL', 'ACTIVE', 'INACTIVE', 'RESOLVED'
  const [searchQuery, setSearchQuery] = useState('');

  // Keep local state in sync when parent passes fresh data
  useEffect(() => {
    setLocalHazards(hazards);
  }, [hazards]);

  // Edit Modal State
  const [editingHazard, setEditingHazard] = useState(null);
  const [editForm, setEditForm] = useState({
    type: '',
    severity: 'High',
    description: '',
    status: 'ACTIVE',
    address: ''
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [actionNotice, setActionNotice] = useState(null);

  // Filter logic over localHazards for instant responsiveness
  const filteredHazards = localHazards.filter((h) => {
    const src = (h.source || (h.created_by || h.createdBy === 'admin' ? 'ADMIN' : (h.reported_by ? 'USER' : 'AI'))).toUpperCase();
    if (sourceFilter !== 'ALL' && src !== sourceFilter) return false;

    const st = (h.status || 'ACTIVE').toUpperCase();
    if (statusFilter !== 'ALL' && st !== statusFilter) return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchType = (h.name || h.type || '').toLowerCase().includes(q);
      const matchAddr = (h.address || '').toLowerCase().includes(q);
      const matchDesc = (h.description || '').toLowerCase().includes(q);
      const matchSrc = src.toLowerCase().includes(q);
      if (!matchType && !matchAddr && !matchDesc && !matchSrc) return false;
    }

    return true;
  });

  const countBySource = {
    ALL: localHazards.length,
    ADMIN: localHazards.filter((h) => (h.source || (h.created_by ? 'ADMIN' : '')).toUpperCase() === 'ADMIN').length,
    AI: localHazards.filter((h) => (h.source || '').toUpperCase() === 'AI' || (!h.source && !h.created_by && !h.reported_by)).length,
    USER: localHazards.filter((h) => (h.source || (h.reported_by ? 'USER' : '')).toUpperCase() === 'USER').length
  };

  // Open Edit Modal
  const handleOpenEdit = (h) => {
    setEditingHazard(h);
    setEditForm({
      type: h.name || h.type || 'Hazard',
      severity: h.severity || 'High',
      description: h.description || '',
      status: (h.status || 'ACTIVE').toUpperCase(),
      address: h.address || ''
    });
  };

  // Submit Edit
  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editingHazard) return;
    setIsUpdating(true);
    const id = editingHazard._id || editingHazard.id;

    // Optimistic UI update
    setLocalHazards((prev) =>
      prev.map((item) =>
        String(item._id || item.id) === String(id)
          ? {
              ...item,
              name: editForm.type,
              type: editForm.type,
              disasterType: editForm.type,
              severity: editForm.severity,
              address: editForm.address,
              description: editForm.description,
              status: editForm.status
            }
          : item
      )
    );

    try {
      cacheService.invalidateCache('active_hazards');
      await api.editAdminHazard(id, editForm);
      setActionNotice(`Hazard #${String(id).slice(-6)} updated successfully.`);
      setEditingHazard(null);
      if (onRefresh) onRefresh();
    } catch (err) {
      setLocalHazards(hazards);
      alert(`Update failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  // Toggle Status (ACTIVE <-> INACTIVE)
  const handleToggleStatus = async (h) => {
    const id = h._id || h.id;
    const current = (h.status || 'ACTIVE').toUpperCase();
    const newStatus = current === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';

    setBusyIds((prev) => ({ ...prev, [id]: true }));

    // Instant optimistic update so power button flips color immediately
    setLocalHazards((prev) =>
      prev.map((item) =>
        String(item._id || item.id) === String(id) ? { ...item, status: newStatus } : item
      )
    );

    try {
      cacheService.invalidateCache('active_hazards');
      await api.updateAdminHazardStatus(id, newStatus);
      setActionNotice(`Hazard status toggled to ${newStatus}.`);
      if (onRefresh) onRefresh();
    } catch (err) {
      setLocalHazards(hazards);
      alert(`Status update failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setBusyIds((prev) => ({ ...prev, [id]: false }));
    }
  };

  // Delete Hazard
  const handleDeleteHazard = async (h) => {
    const id = h._id || h.id;
    if (!window.confirm(`Are you sure you want to delete hazard "${h.name || h.type}" from database?`)) return;

    setBusyIds((prev) => ({ ...prev, [id]: true }));

    // Instant optimistic removal from UI
    setLocalHazards((prev) =>
      prev.filter((item) => String(item._id || item.id) !== String(id))
    );

    try {
      cacheService.invalidateCache('active_hazards');
      await api.deleteAdminHazard(id);
      setActionNotice(`Hazard #${String(id).slice(-6)} removed from database.`);
      if (onRefresh) onRefresh();
    } catch (err) {
      setLocalHazards(hazards);
      alert(`Delete failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setBusyIds((prev) => ({ ...prev, [id]: false }));
    }
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
      
      {/* Header with Quick Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 900, color: '#0f172a', margin: 0 }}>
            Hazard Database & Lifecycle Management
          </h1>
          <p style={{ fontSize: '0.86rem', color: '#64748b', margin: '2px 0 0' }}>
            Full control over AI-detected, Driver-reported, and Admin-created hazards across the city network.
          </p>
        </div>

        <button
          onClick={onNavigateToCreate}
          style={{
            background: '#7c3aed',
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
            boxShadow: '0 4px 14px rgba(124, 58, 237, 0.35)'
          }}
        >
          <Plus size={18} /> + Create New Admin Hazard
        </button>
      </div>

      {/* Action Notification Banner */}
      {actionNotice && (
        <div style={{
          background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '10px',
          padding: '10px 16px', marginBottom: '16px', fontSize: '0.84rem', color: '#166534',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span>✓ {actionNotice}</span>
          <button onClick={() => setActionNotice(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#166534' }}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Filter & Search Toolbar */}
      <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Source Pills (ADMIN, AI, USER) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#64748b', marginRight: '4px' }}>
            SOURCE:
          </span>
          {[
            { id: 'ALL', label: 'All Sources', count: countBySource.ALL, icon: null },
            { id: 'ADMIN', label: 'Admin Created', count: countBySource.ADMIN, icon: ShieldCheck, color: '#6d28d9', bg: '#f5f3ff' },
            { id: 'AI', label: 'AI Detected (YOLOv11)', count: countBySource.AI, icon: Cpu, color: '#0369a1', bg: '#f0f9ff' },
            { id: 'USER', label: 'User Reported', count: countBySource.USER, icon: User, color: '#b45309', bg: '#fef3c7' }
          ].map((pill) => {
            const isSelected = sourceFilter === pill.id;
            const Icon = pill.icon;
            return (
              <button
                key={pill.id}
                onClick={() => setSourceFilter(pill.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '20px',
                  border: isSelected ? `2px solid ${pill.color || '#0284c7'}` : '1px solid #cbd5e1',
                  background: isSelected ? (pill.bg || '#f0f9ff') : '#ffffff',
                  color: isSelected ? (pill.color || '#0284c7') : '#475569',
                  fontWeight: 800,
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                {Icon && <Icon size={14} />}
                <span>{pill.label}</span>
                <span style={{
                  background: isSelected ? (pill.color || '#0284c7') : '#e2e8f0',
                  color: isSelected ? '#ffffff' : '#475569',
                  borderRadius: '10px',
                  padding: '1px 6px',
                  fontSize: '0.7rem'
                }}>
                  {pill.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Right Search Input & Status Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="form-select"
            style={{ padding: '6px 12px', fontSize: '0.8rem', width: 'auto' }}
          >
            <option value="ALL">Status: All</option>
            <option value="ACTIVE">Status: ACTIVE</option>
            <option value="INACTIVE">Status: INACTIVE</option>
            <option value="RESOLVED">Status: RESOLVED</option>
          </select>

          <div style={{
            display: 'flex', alignItems: 'center', background: '#f8fafc',
            border: '1px solid #cbd5e1', borderRadius: '8px', padding: '6px 10px', minWidth: '220px'
          }}>
            <Search size={14} color="#64748b" style={{ marginRight: '6px' }} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search hazards..."
              style={{ border: 'none', background: 'transparent', width: '100%', outline: 'none', fontSize: '0.82rem' }}
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={12} />
              </button>
            )}
          </div>

          <button
            onClick={() => pdfReportService.generateComprehensiveDisasterReport({ hazards: filteredHazards })}
            className="btn btn-secondary"
            style={{ padding: '7px 12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '5px' }}
            title="Download PDF registry report for current active hazards"
          >
            <FileDown size={14} /> Export PDF
          </button>
        </div>
      </div>

      {/* Hazards Table */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <div className="hud-table-wrapper">
          <table className="hud-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Hazard Type</th>
                <th>Severity</th>
                <th>Location & Address</th>
                <th>Description</th>
                <th>Author / Timestamp</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredHazards.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                    No hazards found matching current filters.
                  </td>
                </tr>
              ) : (
                filteredHazards.map((h, idx) => {
                  const id = h._id || h.id || `hz_${idx}`;
                  const src = (h.source || (h.created_by || h.createdBy === 'admin' ? 'ADMIN' : (h.reported_by ? 'USER' : 'AI'))).toUpperCase();
                  const isAdmin = src === 'ADMIN';
                  const isUser = src === 'USER';
                  const status = (h.status || 'ACTIVE').toUpperCase();
                  const severity = h.severity || 'High';

                  const lat = h.latitude !== undefined ? h.latitude : h.lat;
                  const lng = h.longitude !== undefined ? h.longitude : h.lng;

                  return (
                    <tr key={id}>
                      {/* Source Badge */}
                      <td>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '0.72rem',
                          fontWeight: 900,
                          background: isAdmin ? '#f5f3ff' : (isUser ? '#fef3c7' : '#f0f9ff'),
                          color: isAdmin ? '#6d28d9' : (isUser ? '#b45309' : '#0369a1'),
                          border: `1px solid ${isAdmin ? '#ddd6fe' : (isUser ? '#fde68a' : '#bae6fd')}`
                        }}>
                          {isAdmin ? <ShieldCheck size={12} /> : (isUser ? <User size={12} /> : <Cpu size={12} />)}
                          {src}
                        </span>
                      </td>

                      {/* Type */}
                      <td>
                        <strong style={{ color: '#0f172a', fontSize: '0.88rem' }}>
                          {h.name || h.type || 'Hazard'}
                        </strong>
                      </td>

                      {/* Severity */}
                      <td>
                        <span className={`badge ${
                          severity.toLowerCase() === 'critical' ? 'badge-danger' : 
                          severity.toLowerCase() === 'high' ? 'badge-warning' : 'badge-safe'
                        }`}>
                          {severity}
                        </span>
                      </td>

                      {/* Location */}
                      <td style={{ maxWidth: '240px' }}>
                        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1e293b' }}>
                          {h.address || 'Corridor Coordinate'}
                        </div>
                        {lat !== undefined && lng !== undefined && (
                          <div style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace' }}>
                            {lat?.toFixed(4)}, {lng?.toFixed(4)}
                          </div>
                        )}
                      </td>

                      {/* Description */}
                      <td style={{ maxWidth: '220px', fontSize: '0.8rem', color: '#475569' }}>
                        {h.description || '—'}
                      </td>

                      {/* Created By & Timestamp */}
                      <td style={{ fontSize: '0.78rem', color: '#64748b' }}>
                        <div><strong>{h.created_by || h.reported_by || (isAdmin ? 'Admin' : 'System')}</strong></div>
                        <div style={{ fontSize: '0.72rem' }}>
                          {new Date(h.start_time || h.timestamp || h.createdAt || Date.now()).toLocaleDateString()}
                        </div>
                      </td>

                      {/* Status */}
                      <td>
                        <span className={`badge ${
                          status === 'ACTIVE' ? 'badge-safe' : 
                          (status === 'INACTIVE' ? 'badge-warning' : 'badge-danger')
                        }`}>
                          {status}
                        </span>
                      </td>

                      {/* Actions */}
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <button
                            onClick={() => pdfReportService.generateIndividualIncidentDossier({ hazard: h })}
                            className="btn btn-secondary"
                            style={{ padding: '6px 9px', fontSize: '0.75rem', color: '#0284c7', cursor: 'pointer', background: '#eff6ff', borderColor: '#bae6fd' }}
                            title="Export Hazard Incident Dossier (PDF)"
                          >
                            <FileDown size={14} />
                          </button>

                          <button
                            onClick={() => handleOpenEdit(h)}
                            disabled={busyIds[h._id || h.id]}
                            className="btn btn-secondary"
                            style={{ padding: '6px 9px', fontSize: '0.75rem', cursor: 'pointer' }}
                            title="Edit Hazard"
                          >
                            <Edit3 size={14} color="#7c3aed" />
                          </button>

                          <button
                            onClick={() => handleToggleStatus(h)}
                            disabled={busyIds[h._id || h.id]}
                            className="btn btn-secondary"
                            style={{
                              padding: '6px 9px',
                              fontSize: '0.75rem',
                              cursor: 'pointer',
                              color: status === 'ACTIVE' ? '#10b981' : '#64748b',
                              background: status === 'ACTIVE' ? '#f0fdf4' : '#f8fafc',
                              borderColor: status === 'ACTIVE' ? '#bbf7d0' : '#e2e8f0'
                            }}
                            title={status === 'ACTIVE' ? 'Click to Deactivate Hazard' : 'Click to Activate Hazard'}
                          >
                            {busyIds[h._id || h.id] ? (
                              <Loader2 size={14} className="animate-spin" />
                            ) : (
                              <Power size={14} />
                            )}
                          </button>

                          <button
                            onClick={() => handleDeleteHazard(h)}
                            disabled={busyIds[h._id || h.id]}
                            className="btn btn-secondary"
                            style={{ padding: '6px 9px', fontSize: '0.75rem', color: '#ef4444', cursor: 'pointer', background: '#fef2f2', borderColor: '#fecaca' }}
                            title="Delete Hazard from Database"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Hazard Modal */}
      {editingHazard && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)',
          zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px'
        }}>
          <div className="glass-panel" style={{ maxWidth: '480px', width: '100%', padding: '28px', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Edit3 size={18} color="#7c3aed" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, color: '#0f172a' }}>
                  Edit Hazard Record
                </h3>
              </div>
              <button onClick={() => setEditingHazard(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div className="form-group">
                <label className="form-label">Hazard Type</label>
                <input
                  type="text"
                  value={editForm.type}
                  onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Severity</label>
                <select
                  value={editForm.severity}
                  onChange={(e) => setEditForm({ ...editForm, severity: e.target.value })}
                  className="form-select"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Address / Location</label>
                <input
                  type="text"
                  value={editForm.address}
                  onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  rows="3"
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  className="form-textarea"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Status</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="form-select"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="INACTIVE">INACTIVE</option>
                  <option value="RESOLVED">RESOLVED</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setEditingHazard(null)}
                  className="btn btn-secondary"
                  disabled={isUpdating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isUpdating}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {isUpdating ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                  <span>Save Changes</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManageHazardsView;
