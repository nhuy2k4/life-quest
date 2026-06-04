import { useState, useEffect, useCallback } from 'react';
import { listUsers, banUser, updateUser } from '../api/users';
import {
  FiSearch, FiShield, FiShieldOff, FiEdit2, FiChevronLeft, FiChevronRight,
  FiUser, FiCheck, FiX, FiEye, FiEyeOff
} from 'react-icons/fi';
import Modal from '../components/Modal';

const ROLE_BADGE = {
  admin: { label: 'Admin', class: 'badge-admin' },
  user: { label: 'User', class: 'badge-user' },
};

const DIFFICULTY_COLOR = { easy: '#4ade80', medium: '#facc15', hard: '#f87171' };

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [banModal, setBanModal] = useState(null);     // { user }
  const [editModal, setEditModal] = useState(null);   // { user }
  const [editForm, setEditForm] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const PAGE_SIZE = 15;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listUsers(page, PAGE_SIZE);
      setUsers(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch {
      showToast('Failed to load users', 'error');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const filtered = users.filter((u) =>
    u.username?.toLowerCase().includes(search.toLowerCase()) ||
    u.email?.toLowerCase().includes(search.toLowerCase()) ||
    u.display_name?.toLowerCase().includes(search.toLowerCase())
  );

  const handleBan = async () => {
    if (!banModal) return;
    setActionLoading(true);
    try {
      await banUser(banModal.user.id, !banModal.user.is_banned);
      showToast(banModal.user.is_banned ? 'Account unlocked' : 'Account banned');
      setBanModal(null);
      fetchUsers();
    } catch {
      showToast('Action failed', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const openEditModal = (user) => {
    setEditModal({ user });
    setEditForm({
      username: user.username || '',
      email: user.email || '',
      password: '',
    });
    setShowPassword(false);
  };

  const handleEditUser = async () => {
    if (!editModal) return;
    setActionLoading(true);
    try {
      const payload = {};
      if (editForm.username !== editModal.user.username) payload.username = editForm.username;
      if (editForm.email !== editModal.user.email) payload.email = editForm.email;
      if (editForm.password) payload.password = editForm.password;
      await updateUser(editModal.user.id, payload);
      showToast('Account updated successfully');
      setEditModal(null);
      fetchUsers();
    } catch {
      showToast('Update failed', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="page">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      <div className="page-header">
        <div>
          <h1 className="page-title">User Management</h1>
          <p className="page-subtitle">{total} accounts in the system</p>
        </div>
      </div>

      {/* Search bar */}
      <div className="toolbar">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            id="user-search"
            type="text"
            placeholder="Search by username, email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="card table-card">
        {loading ? (
          <div className="loading-center">
            <span className="spinner"></span>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <colgroup>
                <col style={{ width: '22%' }} />
                <col style={{ width: '22%' }} />
                <col style={{ width: '7%' }} />
                <col style={{ width: '10%' }} />
                <col style={{ width: '9%' }} />
                <col style={{ width: '11%' }} />
                <col style={{ width: '10%' }} />
                <col style={{ width: '9%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Email</th>
                  <th>Level</th>
                  <th>XP</th>
                  <th>Streak</th>
                  <th>Trust</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <div className="user-cell">
                        <div className="avatar">{(u.display_name || u.username || '?')[0].toUpperCase()}</div>
                        <div style={{ minWidth: 0 }}>
                          <div className="fw-600 text-truncate">{u.display_name || u.username}</div>
                          <div className="text-muted text-sm">@{u.username}</div>
                        </div>
                      </div>
                    </td>
                    <td className="text-muted text-truncate">{u.email}</td>
                    <td className="text-center fw-600">{u.level_id}</td>
                    <td>
                      <span className="xp-chip">⚡ {u.xp?.toLocaleString()}</span>
                    </td>
                    <td className="text-center">🔥 {u.streak_days}</td>
                    <td>
                      <div className="trust-bar-wrap">
                        <div className="trust-bar" style={{ width: `${(u.trust_score || 0) * 100}%` }}></div>
                        <span className="trust-label">{((u.trust_score || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td>
                      {u.is_banned ? (
                        <span className="badge badge-danger">Banned</span>
                      ) : u.is_verified ? (
                        <span className="badge badge-success">Active</span>
                      ) : (
                        <span className="badge badge-warning">Unverified</span>
                      )}
                    </td>
                    <td>
                      <div className="action-btns">
                        <button
                          id={`ban-btn-${u.id}`}
                          className={`icon-btn ${u.is_banned ? 'icon-btn-success' : 'icon-btn-danger'}`}
                          title={u.is_banned ? 'Unban' : 'Ban account'}
                          onClick={() => setBanModal({ user: u })}
                        >
                          {u.is_banned ? <FiShield size={15} /> : <FiShieldOff size={15} />}
                        </button>
                        <button
                          id={`edit-btn-${u.id}`}
                          className="icon-btn icon-btn-primary"
                          title="Edit Account"
                          onClick={() => openEditModal(u)}
                        >
                          <FiEdit2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr><td colSpan={9} className="empty-row">No users found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button
          id="prev-page"
          className="page-btn"
          disabled={page <= 1}
          onClick={() => setPage(p => p - 1)}
        >
          <FiChevronLeft />
        </button>
        <span className="page-info">Page {page} / {totalPages || 1}</span>
        <button
          id="next-page"
          className="page-btn"
          disabled={page >= totalPages}
          onClick={() => setPage(p => p + 1)}
        >
          <FiChevronRight />
        </button>
      </div>

      {/* Ban/Unban Modal */}
      {banModal && (
        <Modal onClose={() => setBanModal(null)}>
          <div className="modal-icon">{banModal.user.is_banned ? '🔓' : '🔒'}</div>
          <h3 className="modal-title">
            {banModal.user.is_banned ? 'Unban Account' : 'Ban Account'}
          </h3>
          <p className="modal-desc">
            Are you sure you want to {banModal.user.is_banned ? 'unban' : 'ban'} account{' '}
            <strong>@{banModal.user.username}</strong>?
          </p>
          <div className="modal-actions">
            <button className="btn-secondary" onClick={() => setBanModal(null)}>
              <FiX /> Cancel
            </button>
            <button
              id="confirm-ban"
              className={`btn-${banModal.user.is_banned ? 'success' : 'danger'}`}
              onClick={handleBan}
              disabled={actionLoading}
            >
              {actionLoading ? <span className="spinner-sm" /> : <FiCheck />}
              Confirm
            </button>
          </div>
        </Modal>
      )}

      {/* Edit Account Modal */}
      {editModal && (
        <Modal onClose={() => setEditModal(null)}>
          <div className="modal-icon">✏️</div>
          <h3 className="modal-title">Edit Account</h3>
          <p className="modal-desc">
            Editing: <strong>@{editModal.user.username}</strong>
          </p>
          <div className="modal-form">
            <label>Username</label>
            <input
              id="edit-username"
              type="text"
              placeholder="Username"
              value={editForm.username}
              onChange={(e) => setEditForm(f => ({ ...f, username: e.target.value }))}
            />
            <label>Email</label>
            <input
              id="edit-email"
              type="email"
              placeholder="Email address"
              value={editForm.email}
              onChange={(e) => setEditForm(f => ({ ...f, email: e.target.value }))}
            />
            <label>New Password <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>(để trống nếu không đổi)</span></label>
            <div style={{ position: 'relative' }}>
              <input
                id="edit-password"
                type={showPassword ? 'text' : 'password'}
                placeholder="New password..."
                value={editForm.password}
                onChange={(e) => setEditForm(f => ({ ...f, password: e.target.value }))}
                style={{ paddingRight: '2.5rem' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(v => !v)}
                style={{
                  position: 'absolute', right: '10px', top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none', border: 'none', padding: '2px',
                  color: 'var(--text-muted)', cursor: 'pointer',
                  display: 'flex', alignItems: 'center',
                  transition: 'color 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
                onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
                tabIndex={-1}
              >
                {showPassword ? <FiEyeOff size={16} /> : <FiEye size={16} />}
              </button>
            </div>
          </div>
          <div className="modal-actions">
            <button className="btn-secondary" onClick={() => setEditModal(null)}>
              <FiX /> Cancel
            </button>
            <button
              id="confirm-edit"
              className="btn-primary"
              onClick={handleEditUser}
              disabled={actionLoading}
            >
              {actionLoading ? <span className="spinner-sm" /> : <FiCheck />}
              Save Changes
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
