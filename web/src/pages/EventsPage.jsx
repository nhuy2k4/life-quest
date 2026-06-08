import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  FiCalendar,
  FiCheck,
  FiEdit2,
  FiPlus,
  FiSearch,
  FiX,
} from 'react-icons/fi';
import { createEvent, endEvent, getEvent, listEvents, updateEvent } from '../api/events';
import { listQuests } from '../api/quests';
import Modal from '../components/Modal';

const STATUS_OPTIONS = ['draft', 'active', 'ended'];

const emptyForm = {
  title: '',
  description: '',
  banner_url: '',
  start_at: '',
  end_at: '',
  status: 'draft',
  quest_ids: [],
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
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [modalMode, setModalMode] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [actionLoading, setActionLoading] = useState(false);
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

  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  useEffect(() => {
    listQuests(1, 100)
      .then((res) => setQuests(res.data.items || []))
      .catch(() => setQuests([]));
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
      setSelectedEvent(detail);
      setForm({
        title: detail.title || '',
        description: detail.description || '',
        banner_url: detail.banner_url || '',
        start_at: toDateTimeLocal(detail.start_at),
        end_at: toDateTimeLocal(detail.end_at),
        status: detail.status || 'draft',
        quest_ids: (detail.quests || []).map((quest) => quest.id),
      });
      setModalMode('edit');
    } catch {
      showToast('Failed to open event', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const toggleQuest = (questId) => {
    setForm((current) => {
      const exists = current.quest_ids.includes(questId);
      return {
        ...current,
        quest_ids: exists
          ? current.quest_ids.filter((id) => id !== questId)
          : [...current.quest_ids, questId],
      };
    });
  };

  const buildPayload = () => ({
    title: form.title.trim(),
    description: form.description.trim() || null,
    banner_url: form.banner_url.trim() || null,
    start_at: fromDateTimeLocal(form.start_at),
    end_at: fromDateTimeLocal(form.end_at),
    status: form.status,
    reward_config: [],
    quest_ids: form.quest_ids,
  });

  const handleSave = async () => {
    const payload = buildPayload();
    if (!payload.title || !payload.start_at || !payload.end_at || payload.quest_ids.length === 0) {
      showToast('Title, time window, and at least one quest are required', 'error');
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
    } catch {
      showToast('Failed to save event', 'error');
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

            <label>Banner URL</label>
            <input
              type="url"
              value={form.banner_url}
              onChange={(e) => setForm((current) => ({ ...current, banner_url: e.target.value }))}
            />

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

            <label>Quests</label>
            <div className="tag-list" style={{ maxHeight: 180, overflow: 'auto' }}>
              {quests.map((quest) => (
                <label key={quest.id} className="checkbox-label" style={{ width: '100%' }}>
                  <input
                    type="checkbox"
                    checked={form.quest_ids.includes(quest.id)}
                    onChange={() => toggleQuest(quest.id)}
                  />
                  <span className="text-truncate">{quest.title}</span>
                </label>
              ))}
              {quests.length === 0 && <div className="text-muted text-sm">No quests available</div>}
            </div>
          </div>

          <div className="modal-actions">
            <button className="btn-secondary" onClick={() => setModalMode(null)}>
              <FiX /> Cancel
            </button>
            <button className="btn-primary" onClick={handleSave} disabled={actionLoading}>
              {actionLoading ? <span className="spinner-sm" /> : <FiCheck />}
              Save
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
