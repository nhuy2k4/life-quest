import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  FiCalendar,
  FiCheck,
  FiEdit2,
  FiImage,
  FiPlus,
  FiSearch,
  FiUpload,
  FiX,
} from 'react-icons/fi';
import { listBadges } from '../api/badges';
import { createEvent, endEvent, getEvent, listEvents, updateEvent, uploadEventBanner } from '../api/events';
import { listQuests } from '../api/quests';
import Modal from '../components/Modal';

const STATUS_OPTIONS = ['draft', 'active', 'ended'];
const XP_REWARD_RANKS = [1, 2, 3, 4, 5];
const BADGE_REWARD_RANKS = [1, 2, 3];

const emptyForm = {
  title: '',
  description: '',
  banner_url: '',
  start_at: '',
  end_at: '',
  status: 'draft',
  quest_ids: [],
  reward_xp: { 1: '', 2: '', 3: '', 4: '', 5: '' },
  reward_badges: { 1: '', 2: '', 3: '' },
};

const toDateTimeLocal = (value) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const offsetMs = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
};

const fromDateTimeLocal = (value) => {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
};

const fmtDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString();
};

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [quests, setQuests] = useState([]);
  const [badges, setBadges] = useState([]);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [modalMode, setModalMode] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [actionLoading, setActionLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listEvents(status || undefined);
      setEvents(res.data || []);
    } catch {
      showToast('Failed to load events', 'error');
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    const run = async () => {
      await fetchEvents();
    };
    run();
  }, [fetchEvents]);

  useEffect(() => {
    Promise.all([listQuests(1, 100), listBadges(1, 100)])
      .then(([questRes, badgeRes]) => {
        setQuests(questRes.data.items || []);
        setBadges(badgeRes.data.items || []);
      })
      .catch(() => {
        setQuests([]);
        setBadges([]);
      });
  }, []);

  const filteredEvents = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return events;
    return events.filter((event) =>
      event.title?.toLowerCase().includes(term) ||
      event.description?.toLowerCase().includes(term)
    );
  }, [events, search]);

  const openCreate = () => {
    setSelectedEvent(null);
    setForm(emptyForm);
    setModalMode('create');
  };

  const openEdit = async (event) => {
    setActionLoading(true);
    try {
      const res = await getEvent(event.id);
      const detail = res.data;
      const rewardXp = { 1: '', 2: '', 3: '', 4: '', 5: '' };
      const rewardBadges = { 1: '', 2: '', 3: '' };
      (detail.reward_config || []).forEach((tier) => {
        for (let rank = tier.rank_from; rank <= tier.rank_to; rank += 1) {
          if (XP_REWARD_RANKS.includes(rank)) rewardXp[rank] = String(tier.bonus_xp || '');
          if (BADGE_REWARD_RANKS.includes(rank)) rewardBadges[rank] = tier.badge_id || '';
        }
      });
      setSelectedEvent(detail);
      setForm({
        title: detail.title || '',
        description: detail.description || '',
        banner_url: detail.banner_url || '',
        start_at: toDateTimeLocal(detail.start_at),
        end_at: toDateTimeLocal(detail.end_at),
        status: detail.status || 'draft',
        quest_ids: (detail.quests || []).map((quest) => quest.id),
        reward_xp: rewardXp,
        reward_badges: rewardBadges,
      });
      setModalMode('edit');
    } catch {
      showToast('Failed to open event', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const selectQuest = (questId) => {
    setForm((current) => ({ ...current, quest_ids: [questId] }));
  };

  const handleBannerUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      const res = await uploadEventBanner(file);
      setForm((current) => ({ ...current, banner_url: res.data.url }));
      showToast('Banner uploaded');
    } catch {
      showToast('Upload failed. Check Cloudinary or image file.', 'error');
    } finally {
      setUploading(false);
    }
  };

  const buildRewardConfig = () => XP_REWARD_RANKS.map((rank) => ({
    rank_from: rank,
    rank_to: rank,
    bonus_xp: Math.max(0, parseInt(form.reward_xp[rank], 10) || 0),
    badge_id: BADGE_REWARD_RANKS.includes(rank) && form.reward_badges[rank]
      ? form.reward_badges[rank]
      : null,
  }));

  const buildPayload = () => ({
    title: form.title.trim(),
    description: form.description.trim() || null,
    banner_url: form.banner_url.trim() || null,
    start_at: fromDateTimeLocal(form.start_at),
    end_at: fromDateTimeLocal(form.end_at),
    status: form.status,
    reward_config: buildRewardConfig(),
    quest_ids: form.quest_ids,
  });

  const handleSave = async () => {
    const payload = buildPayload();
    if (!payload.title || !payload.banner_url || !payload.start_at || !payload.end_at || payload.quest_ids.length !== 1) {
      showToast('Title, uploaded banner, time window, and exactly one quest are required', 'error');
      return;
    }
    setActionLoading(true);
    try {
      if (modalMode === 'edit' && selectedEvent) {
        await updateEvent(selectedEvent.id, payload);
        showToast('Event updated');
      } else {
        await createEvent(payload);
        showToast('Event created');
      }
      setModalMode(null);
      setSelectedEvent(null);
      fetchEvents();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to save event';
      showToast(msg, 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEnd = async (event) => {
    const ok = window.confirm(`End event "${event.title}" now?`);
    if (!ok) return;
    setActionLoading(true);
    try {
      await endEvent(event.id);
      showToast('Event ended');
      fetchEvents();
    } catch {
      showToast('Failed to end event', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="page">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      <div className="page-header">
        <div>
          <h1 className="page-title">Event Management</h1>
          <p className="page-subtitle">Create events and assign quests for users to join</p>
        </div>
        <button className="btn-primary" onClick={openCreate}>
          <FiPlus /> Create Event
        </button>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            id="event-search"
            type="text"
            placeholder="Search events..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
      </div>

      <div className="card table-card">
        {loading ? (
          <div className="loading-center"><span className="spinner"></span></div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <colgroup>
                <col style={{ width: '34%' }} />
                <col style={{ width: '12%' }} />
                <col style={{ width: '19%' }} />
                <col style={{ width: '19%' }} />
                <col style={{ width: '16%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Status</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map((event) => (
                  <tr key={event.id}>
                    <td>
                      <div className="quest-cell">
                        <div className="quest-icon"><FiCalendar size={13} /></div>
                        <div style={{ minWidth: 0 }}>
                          <div className="fw-600 text-truncate">{event.title}</div>
                          <div className="text-muted text-sm text-truncate">
                            {event.description || 'No description'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td><span className="badge badge-success">{event.status}</span></td>
                    <td className="text-muted">{fmtDate(event.start_at)}</td>
                    <td className="text-muted">{fmtDate(event.end_at)}</td>
                    <td>
                      <div className="action-btns">
                        <button
                          className="icon-btn icon-btn-primary"
                          title="Edit event"
                          disabled={actionLoading}
                          onClick={() => openEdit(event)}
                        >
                          <FiEdit2 size={14} />
                        </button>
                        {event.status !== 'ended' && (
                          <button
                            className="icon-btn icon-btn-danger"
                            title="End event"
                            disabled={actionLoading}
                            onClick={() => handleEnd(event)}
                          >
                            <FiCheck size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredEvents.length === 0 && (
                  <tr><td colSpan={5} className="empty-row">No events found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modalMode && (
        <Modal onClose={() => setModalMode(null)} wide>
          <h3 className="modal-title">{modalMode === 'edit' ? 'Edit Event' : 'Create Event'}</h3>
          <div className="modal-form">
            <label>Title</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm((current) => ({ ...current, title: e.target.value }))}
            />

            <label>Description</label>
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))}
            />

            <label>Banner image</label>
            <div className="event-banner-input">
              <div className="event-banner-preview">
                {form.banner_url ? (
                  <img src={form.banner_url} alt="" />
                ) : (
                  <FiImage size={20} />
                )}
              </div>
              <label className="btn-secondary event-banner-upload" title="Upload banner">
                {uploading ? <span className="spinner-sm" /> : <FiUpload />}
                Upload
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleBannerUpload(e.target.files?.[0])}
                />
              </label>
            </div>

            <div className="form-row">
              <div className="form-col">
                <label>Start</label>
                <input
                  type="datetime-local"
                  value={form.start_at}
                  onChange={(e) => setForm((current) => ({ ...current, start_at: e.target.value }))}
                />
              </div>
              <div className="form-col">
                <label>End</label>
                <input
                  type="datetime-local"
                  value={form.end_at}
                  onChange={(e) => setForm((current) => ({ ...current, end_at: e.target.value }))}
                />
              </div>
              <div className="form-col">
                <label>Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm((current) => ({ ...current, status: e.target.value }))}
                >
                  {STATUS_OPTIONS.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>
            </div>

            <label>Quest</label>
            <div className="tag-list" style={{ maxHeight: 180, overflow: 'auto' }}>
              {quests.map((quest) => (
                <label key={quest.id} className="checkbox-label" style={{ width: '100%' }}>
                  <input
                    type="radio"
                    name="event-quest"
                    checked={form.quest_ids.includes(quest.id)}
                    onChange={() => selectQuest(quest.id)}
                  />
                  <span className="text-truncate">{quest.title}</span>
                </label>
              ))}
              {quests.length === 0 && <div className="text-muted text-sm">No quests available</div>}
            </div>

            <label>Top rewards</label>
            <div className="event-reward-grid">
              {XP_REWARD_RANKS.map((rank) => (
                <div key={rank} className="event-reward-row">
                  <div className="event-rank-label">Top {rank}</div>
                  <input
                    type="number"
                    min="0"
                    placeholder="XP"
                    value={form.reward_xp[rank]}
                    onChange={(e) => setForm((current) => ({
                      ...current,
                      reward_xp: { ...current.reward_xp, [rank]: e.target.value },
                    }))}
                  />
                  {BADGE_REWARD_RANKS.includes(rank) ? (
                    <select
                      value={form.reward_badges[rank]}
                      onChange={(e) => setForm((current) => ({
                        ...current,
                        reward_badges: { ...current.reward_badges, [rank]: e.target.value },
                      }))}
                    >
                      <option value="">No badge</option>
                      {badges.map((badge) => (
                        <option key={badge.id} value={badge.id}>{badge.name}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="event-no-badge">No badge</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="modal-actions">
            <button className="btn-secondary" onClick={() => setModalMode(null)}>
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
