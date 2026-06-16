import { useState, useEffect, useCallback } from 'react';
import { listQuests, updateQuest } from '../api/quests';
import {
  FiSearch, FiEdit2, FiToggleLeft, FiToggleRight,
  FiChevronLeft, FiChevronRight, FiX, FiCheck, FiStar
} from 'react-icons/fi';
import Modal from '../components/Modal';

const DIFFICULTY_MAP = {
  easy: { label: 'Easy', class: 'badge-success' },
  medium: { label: 'Medium', class: 'badge-warning' },
  hard: { label: 'Hard', class: 'badge-danger' },
};

export default function QuestsPage() {
  const [quests, setQuests] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [editModal, setEditModal] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const PAGE_SIZE = 15;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchQuests = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listQuests(page, PAGE_SIZE);
      setQuests(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch {
      showToast('Failed to load quests', 'error');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchQuests(); }, [fetchQuests]);

  const filtered = quests.filter((q) =>
    q.title?.toLowerCase().includes(search.toLowerCase()) ||
    q.description?.toLowerCase().includes(search.toLowerCase())
  );

  const openEdit = (quest) => {
    setEditModal(quest);
    setEditForm({
      title: quest.title,
      description: quest.description || '',
      xp_reward: quest.xp_reward,
      difficulty: quest.difficulty,
      time_limit_hours: quest.time_limit_hours || '',
      is_active: quest.is_active,
      is_event: quest.is_event || false,
    });
  };

  const handleToggleActive = async (quest) => {
    try {
      await updateQuest(quest.id, { is_active: !quest.is_active });
      showToast(quest.is_active ? 'Quest hidden' : 'Quest activated');
      fetchQuests();
    } catch {
      showToast('Action failed', 'error');
    }
  };

  const handleSaveEdit = async () => {
    if (!editModal) return;
    setActionLoading(true);
    try {
      const payload = {
        ...editForm,
        xp_reward: parseInt(editForm.xp_reward) || editModal.xp_reward,
        time_limit_hours: editForm.time_limit_hours ? parseInt(editForm.time_limit_hours) : null,
      };
      await updateQuest(editModal.id, payload);
      showToast('Quest updated');
      setEditModal(null);
      fetchQuests();
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
          <h1 className="page-title">Quest Management</h1>
          <p className="page-subtitle">{total} quests in the system</p>
        </div>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            id="quest-search"
            type="text"
            placeholder="Search quests..."
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
                <col style={{ width: '30%' }} />
                <col style={{ width: '11%' }} />
                <col style={{ width: '9%' }} />
                <col style={{ width: '18%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '10%' }} />
                <col style={{ width: '9%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Quest Name</th>
                  <th>Difficulty</th>
                  <th>XP</th>
                  <th>Categories</th>
                  <th>Time Limit</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((q) => (
                  <tr key={q.id}>
                    <td>
                      <div className="quest-cell">
                        <div className="quest-icon">
                          <FiStar size={13} />
                        </div>
                        <div style={{ minWidth: 0 }}>
                          <div className="fw-600 text-truncate">{q.title}</div>
                          {q.description && (
                            <div className="text-muted text-sm text-truncate">
                              {q.description}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${DIFFICULTY_MAP[q.difficulty]?.class}`}>
                        {DIFFICULTY_MAP[q.difficulty]?.label}
                      </span>
                    </td>
                    <td>
                      <span className="xp-chip">⚡ {q.xp_reward}</span>
                    </td>
                    <td>
                      <div className="tag-list">
                        {(q.categories || []).slice(0, 3).map((c) => (
                          <span key={c.id} className="tag">{c.name}</span>
                        ))}
                      </div>
                    </td>
                    <td className="text-muted">
                      {q.time_limit_hours ? `${q.time_limit_hours}h` : '—'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-start' }}>
                        {q.is_active ? (
                          <span className="badge badge-success">Active</span>
                        ) : (
                          <span className="badge badge-danger">Hidden</span>
                        )}
                        {q.is_event && (
                          <span className="badge badge-info">Event</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="action-btns">
                        <button
                          id={`edit-quest-${q.id}`}
                          className="icon-btn icon-btn-primary"
                          title="Edit"
                          onClick={() => openEdit(q)}
                        >
                          <FiEdit2 size={14} />
                        </button>
                        <button
                          id={`toggle-quest-${q.id}`}
                          className={`icon-btn ${q.is_active ? 'icon-btn-danger' : 'icon-btn-success'}`}
                          title={q.is_active ? 'Hide quest' : 'Activate'}
                          onClick={() => handleToggleActive(q)}
                        >
                          {q.is_active ? <FiToggleRight size={16} /> : <FiToggleLeft size={16} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr><td colSpan={8} className="empty-row">No quests found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="pagination">
        <button id="quest-prev" className="page-btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
          <FiChevronLeft />
        </button>
        <span className="page-info">Page {page} / {totalPages || 1}</span>
        <button id="quest-next" className="page-btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
          <FiChevronRight />
        </button>
      </div>

      {/* Edit Modal */}
      {editModal && (
        <Modal onClose={() => setEditModal(null)} wide>
          <h3 className="modal-title">Edit Quest</h3>
          <div className="modal-form">
            <label>Title</label>
            <input
              id="edit-title"
              type="text"
              value={editForm.title}
              onChange={(e) => setEditForm(f => ({ ...f, title: e.target.value }))}
            />
            <label>Description</label>
            <textarea
              id="edit-desc"
              rows={3}
              value={editForm.description}
              onChange={(e) => setEditForm(f => ({ ...f, description: e.target.value }))}
            />
            <div className="form-row">
              <div className="form-col">
                <label>XP Reward</label>
                <input
                  id="edit-xp"
                  type="number"
                  value={editForm.xp_reward}
                  onChange={(e) => setEditForm(f => ({ ...f, xp_reward: e.target.value }))}
                />
              </div>
              <div className="form-col">
                <label>Difficulty</label>
                <select
                  id="edit-difficulty"
                  value={editForm.difficulty}
                  onChange={(e) => setEditForm(f => ({ ...f, difficulty: e.target.value }))}
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
              <div className="form-col">
                <label>Time Limit (hours)</label>
                <input
                  id="edit-timelimit"
                  type="number"
                  placeholder="Unlimited"
                  value={editForm.time_limit_hours}
                  onChange={(e) => setEditForm(f => ({ ...f, time_limit_hours: e.target.value }))}
                />
              </div>
            </div>
            <label className="checkbox-label">
              <input
                id="edit-active"
                type="checkbox"
                checked={editForm.is_active}
                onChange={(e) => setEditForm(f => ({ ...f, is_active: e.target.checked }))}
              />
              Activate quest
            </label>
            <label className="checkbox-label" style={{ marginTop: '8px' }}>
              <input
                id="edit-isevent"
                type="checkbox"
                checked={editForm.is_event}
                onChange={(e) => setEditForm(f => ({ ...f, is_event: e.target.checked }))}
              />
              Event Quest (only show in Event settings)
            </label>
          </div>
          <div className="modal-actions">
            <button className="btn-secondary" onClick={() => setEditModal(null)}>
              <FiX /> Cancel
            </button>
            <button id="save-quest" className="btn-primary" onClick={handleSaveEdit} disabled={actionLoading}>
              {actionLoading ? <span className="spinner-sm" /> : <FiCheck />}
              Save
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
