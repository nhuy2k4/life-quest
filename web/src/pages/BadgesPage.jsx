import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  FiAward, FiCheck, FiChevronLeft, FiChevronRight, FiEdit2, FiEye,
  FiEyeOff, FiImage, FiPlus, FiSearch, FiToggleLeft, FiToggleRight,
  FiTrash2, FiUpload, FiX
} from 'react-icons/fi';
import {
  createBadge,
  deleteBadge,
  listBadgeConditionTypes,
  listBadges,
  updateBadge,
  uploadBadgeIcon,
} from '../api/badges';
import Modal from '../components/Modal';

const PAGE_SIZE = 20;

const RARITIES = [
  { value: 'common', label: 'Common', className: 'badge-user' },
  { value: 'rare', label: 'Rare', className: 'badge-success' },
  { value: 'epic', label: 'Epic', className: 'badge-warning' },
  { value: 'legendary', label: 'Legendary', className: 'badge-danger' },
];

const CATEGORIES = [
  { value: 'quests', label: 'Quests' },
  { value: 'social', label: 'Social' },
  { value: 'streak', label: 'Streak' },
  { value: 'progression', label: 'Progression' },
  { value: 'trust', label: 'Trust' },
  { value: 'event', label: 'Event' },
  { value: 'general', label: 'General' },
];

const EMPTY_FORM = {
  name: '',
  description: '',
  icon_url: '',
  rarity: 'common',
  category: 'general',
  condition_type: 'quests_completed',
  target: 1,
  is_hidden: false,
  is_active: true,
  sort_order: 0,
};

const rarityMeta = (rarity) => RARITIES.find((item) => item.value === rarity) || RARITIES[0];

function criteriaTarget(criteria) {
  return criteria?.target ?? criteria?.count ?? 1;
}

function criteriaType(criteria) {
  return criteria?.type || 'quests_completed';
}

function badgeFormFromItem(badge) {
  return {
    name: badge.name || '',
    description: badge.description || '',
    icon_url: badge.icon_url || '',
    rarity: badge.rarity || 'common',
    category: badge.category || 'general',
    condition_type: criteriaType(badge.criteria),
    target: criteriaTarget(badge.criteria),
    is_hidden: Boolean(badge.is_hidden),
    is_active: Boolean(badge.is_active),
    sort_order: badge.sort_order || 0,
  };
}

function normalizePayload(form) {
  return {
    ...form,
    target: Math.max(1, parseInt(form.target, 10) || 1),
    sort_order: Math.max(0, parseInt(form.sort_order, 10) || 0),
  };
}

function BadgeIcon({ badge }) {
  const icon = badge.icon_url;
  if (icon?.startsWith('http://') || icon?.startsWith('https://')) {
    return <img className="badge-icon-img" src={icon} alt="" />;
  }
  return (
    <div className="badge-icon-key">
      <FiAward size={16} />
      <span>{icon || 'badge'}</span>
    </div>
  );
}

export default function BadgesPage() {
  const [badges, setBadges] = useState([]);
  const [conditionTypes, setConditionTypes] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [modalMode, setModalMode] = useState(null);
  const [selectedBadge, setSelectedBadge] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [actionLoading, setActionLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchBadges = useCallback(async () => {
    setLoading(true);
    try {
      const [badgeRes, conditionRes] = await Promise.all([
        listBadges(page, PAGE_SIZE),
        listBadgeConditionTypes(),
      ]);
      setBadges(badgeRes.data.items || []);
      setTotal(badgeRes.data.total || 0);
      setConditionTypes(conditionRes.data.items || []);
    } catch {
      showToast('Failed to load badges', 'error');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchBadges(); }, [fetchBadges]);

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return badges;
    return badges.filter((badge) =>
      badge.name?.toLowerCase().includes(needle) ||
      badge.description?.toLowerCase().includes(needle) ||
      badge.category?.toLowerCase().includes(needle)
    );
  }, [badges, search]);

  const openCreate = () => {
    setSelectedBadge(null);
    setForm(EMPTY_FORM);
    setModalMode('create');
  };

  const openEdit = (badge) => {
    setSelectedBadge(badge);
    setForm(badgeFormFromItem(badge));
    setModalMode('edit');
  };

  const closeModal = () => {
    setModalMode(null);
    setSelectedBadge(null);
    setForm(EMPTY_FORM);
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      const res = await uploadBadgeIcon(file);
      setForm((current) => ({ ...current, icon_url: res.data.url }));
      showToast('Badge icon uploaded');
    } catch {
      showToast('Upload failed. Check Cloudinary or image file.', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    setActionLoading(true);
    try {
      const payload = normalizePayload(form);
      if (modalMode === 'edit' && selectedBadge) {
        await updateBadge(selectedBadge.id, payload);
        showToast('Badge updated');
      } else {
        await createBadge(payload);
        showToast('Badge created');
      }
      closeModal();
      fetchBadges();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to save badge';
      showToast(msg, 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleActive = async (badge) => {
    try {
      await updateBadge(badge.id, { is_active: !badge.is_active });
      showToast(badge.is_active ? 'Badge disabled' : 'Badge enabled');
      fetchBadges();
    } catch {
      showToast('Action failed', 'error');
    }
  };

  const handleToggleHidden = async (badge) => {
    try {
      await updateBadge(badge.id, { is_hidden: !badge.is_hidden });
      showToast(badge.is_hidden ? 'Badge is now visible on UI' : 'Badge is now hidden');
      fetchBadges();
    } catch {
      showToast('Action failed', 'error');
    }
  };

  const handleDelete = async (badge) => {
    const ok = window.confirm(`Delete badge "${badge.name}"?`);
    if (!ok) return;
    try {
      await deleteBadge(badge.id);
      showToast('Badge deleted');
      fetchBadges();
    } catch {
      showToast('Failed to delete badge', 'error');
    }
  };

  return (
    <div className="page">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      <div className="page-header">
        <div>
          <h1 className="page-title">Badge Management</h1>
          <p className="page-subtitle">{total} badges in the system</p>
        </div>
        <button id="create-badge" className="btn-primary" onClick={openCreate}>
          <FiPlus /> Create Badge
        </button>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            id="badge-search"
            type="text"
            placeholder="Search badges..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="card table-card">
        {loading ? (
          <div className="loading-center"><span className="spinner"></span></div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <colgroup>
                <col style={{ width: '28%' }} />
                <col style={{ width: '10%' }} />
                <col style={{ width: '11%' }} />
                <col style={{ width: '22%' }} />
                <col style={{ width: '7%' }} />
                <col style={{ width: '11%' }} />
                <col style={{ width: '11%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Badge</th>
                  <th>Rarity</th>
                  <th>Category</th>
                  <th>Condition</th>
                  <th>Order</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((badge) => {
                  const rarity = rarityMeta(badge.rarity);
                  return (
                    <tr key={badge.id}>
                      <td>
                        <div className="quest-cell">
                          <div className="badge-icon-wrap">
                            <BadgeIcon badge={badge} />
                          </div>
                          <div style={{ minWidth: 0 }}>
                            <div className="fw-600 text-truncate">{badge.name}</div>
                            <div className="text-muted text-sm text-truncate">
                              {badge.description}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td><span className={`badge ${rarity.className}`}>{rarity.label}</span></td>
                      <td><span className="tag">{badge.category}</span></td>
                      <td>
                        <div className="text-sm" style={{ minWidth: 0 }}>
                          <div className="fw-600 text-truncate">{criteriaType(badge.criteria)}</div>
                          <div className="text-muted"> × {criteriaTarget(badge.criteria)}</div>
                        </div>
                      </td>
                      <td>{badge.sort_order}</td>
                      <td>
                        <div className="tag-list">
                          <span className={`badge ${badge.is_active ? 'badge-success' : 'badge-danger'}`}>
                            {badge.is_active ? 'Active' : 'Off'}
                          </span>
                          {badge.is_hidden && <span className="badge badge-warning">Hidden</span>}
                        </div>
                      </td>
                      <td>
                        <div className="action-btns">
                          <button
                            className="icon-btn icon-btn-primary"
                            title="Edit"
                            onClick={() => openEdit(badge)}
                          >
                            <FiEdit2 size={14} />
                          </button>
                          <button
                            className={`icon-btn ${badge.is_active ? 'icon-btn-danger' : 'icon-btn-success'}`}
                            title={badge.is_active ? 'Disable badge' : 'Enable badge'}
                            onClick={() => handleToggleActive(badge)}
                          >
                            {badge.is_active ? <FiToggleRight size={16} /> : <FiToggleLeft size={16} />}
                          </button>
                          <button
                            className="icon-btn icon-btn-primary"
                            title={badge.is_hidden ? 'Show badge' : 'Hide badge'}
                            onClick={() => handleToggleHidden(badge)}
                          >
                            {badge.is_hidden ? <FiEyeOff size={14} /> : <FiEye size={14} />}
                          </button>
                          <button
                            className="icon-btn icon-btn-danger"
                            title="Delete badge"
                            onClick={() => handleDelete(badge)}
                          >
                            <FiTrash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {filtered.length === 0 && (
                  <tr><td colSpan={7} className="empty-row">No badges found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="pagination">
        <button className="page-btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          <FiChevronLeft />
        </button>
        <span className="page-info">Page {page} / {totalPages || 1}</span>
        <button className="page-btn" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
          <FiChevronRight />
        </button>
      </div>

      {modalMode && (
        <Modal onClose={closeModal} wide>
          <h3 className="modal-title">{modalMode === 'edit' ? 'Edit Badge' : 'Create Badge'}</h3>
          <div className="modal-form">
            <label>Badge name</label>
            <input
              value={form.name}
              onChange={(e) => setForm((current) => ({ ...current, name: e.target.value }))}
            />

            <label>Description</label>
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))}
            />

            <label>Icon URL or icon key</label>
            <div className="badge-icon-input">
              <FiImage />
              <input
                value={form.icon_url}
                onChange={(e) => setForm((current) => ({ ...current, icon_url: e.target.value }))}
                placeholder="https://... or trophy"
              />
              <label className="icon-upload-btn" title="Upload icon">
                {uploading ? <span className="spinner-sm" /> : <FiUpload size={14} />}
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleUpload(e.target.files?.[0])}
                />
              </label>
            </div>

            <div className="form-row">
              <div className="form-col">
                <label>Rarity</label>
                <select
                  value={form.rarity}
                  onChange={(e) => setForm((current) => ({ ...current, rarity: e.target.value }))}
                >
                  {RARITIES.map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-col">
                <label>Category</label>
                <select
                  value={form.category}
                  onChange={(e) => setForm((current) => ({ ...current, category: e.target.value }))}
                >
                  {CATEGORIES.map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-col">
                <label>Sort order</label>
                <input
                  type="number"
                  min="0"
                  value={form.sort_order}
                  onChange={(e) => setForm((current) => ({ ...current, sort_order: e.target.value }))}
                />
              </div>
            </div>

            <div className="form-row form-row-two">
              <div className="form-col">
                <label>Condition</label>
                <select
                  value={form.condition_type}
                  onChange={(e) => setForm((current) => ({ ...current, condition_type: e.target.value }))}
                >
                  {conditionTypes.map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-col">
                <label>Target</label>
                <input
                  type="number"
                  min="1"
                  value={form.target}
                  onChange={(e) => setForm((current) => ({ ...current, target: e.target.value }))}
                />
              </div>
            </div>

            <div className="badge-switch-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm((current) => ({ ...current, is_active: e.target.checked }))}
                />
                Enable badge
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.is_hidden}
                  onChange={(e) => setForm((current) => ({ ...current, is_hidden: e.target.checked }))}
                />
                Hide from UI until earned
              </label>
            </div>
          </div>
          <div className="modal-actions">
            <button className="btn-secondary" onClick={closeModal}>
              <FiX /> Cancel
            </button>
            <button className="btn-primary" onClick={handleSave} disabled={actionLoading || uploading}>
              {actionLoading ? <span className="spinner-sm" /> : <FiCheck />}
              Save
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
