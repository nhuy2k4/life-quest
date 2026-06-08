import { useEffect, useState } from 'react';
import { FiCalendar, FiMessageSquare, FiTrendingUp, FiZap } from 'react-icons/fi';
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { getDashboardStats } from '../api/dashboard';

const EMPTY_STATS = {
  quests_completed_today: [],
  quests_completed_this_month: [],
  top_interaction_posts: [],
  top_participation_events: [],
};

const fmtDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleDateString();
};

const sum = (items, key) => items.reduce((total, item) => total + (item[key] || 0), 0);

export default function DashboardPage() {
  const [stats, setStats] = useState(EMPTY_STATS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then((res) => setStats({ ...EMPTY_STATS, ...res.data }))
      .catch(() => setStats(EMPTY_STATS))
      .finally(() => setLoading(false));
  }, []);

  const cards = [
    {
      id: 'quests-today',
      label: 'Completed Today',
      value: sum(stats.quests_completed_today, 'completed_count'),
      icon: FiZap,
      color: '#22c55e',
    },
    {
      id: 'quests-month',
      label: 'Completed This Month',
      value: sum(stats.quests_completed_this_month, 'completed_count'),
      icon: FiTrendingUp,
      color: '#6366f1',
    },
    {
      id: 'post-interactions',
      label: 'Top Post Interactions',
      value: sum(stats.top_interaction_posts, 'interaction_count'),
      icon: FiMessageSquare,
      color: '#f59e0b',
    },
    {
      id: 'event-participants',
      label: 'Event Participants',
      value: sum(stats.top_participation_events, 'participant_count'),
      icon: FiCalendar,
      color: '#06b6d4',
    },
  ];

  if (loading) {
    return (
      <div className="page">
        <div className="loading-center" style={{ height: '60vh' }}>
          <span className="spinner"></span>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Quest, post, and event performance</p>
        </div>
      </div>

      <div className="stats-grid">
        {cards.map(({ id, label, value, icon: Icon, color }) => (
          <div key={id} id={id} className="stat-card">
            <div className="stat-icon" style={{ background: `${color}22`, color }}>
              <Icon size={22} />
            </div>
            <div>
              <div className="stat-value">{value.toLocaleString()}</div>
              <div className="stat-label">{label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="charts-grid">
        <div className="card chart-card">
          <h3 className="chart-title">Top Quests Completed Today</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={stats.quests_completed_today} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <XAxis dataKey="title" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="completed_count" name="Completed" fill="#22c55e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card chart-card">
          <h3 className="chart-title">Top Quests Completed This Month</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={stats.quests_completed_this_month} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <XAxis dataKey="title" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="completed_count" name="Completed" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card chart-card">
          <h3 className="chart-title">Posts With Highest Interactions</h3>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Post</th>
                  <th>Author</th>
                  <th>Likes</th>
                  <th>Comments</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {stats.top_interaction_posts.map((post) => (
                  <tr key={post.post_id}>
                    <td className="text-truncate">{post.caption || '(no caption)'}</td>
                    <td>@{post.author}</td>
                    <td>{post.like_count}</td>
                    <td>{post.comment_count}</td>
                    <td className="fw-600">{post.interaction_count}</td>
                  </tr>
                ))}
                {stats.top_interaction_posts.length === 0 && (
                  <tr><td colSpan={5} className="empty-row">No post interactions yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card chart-card">
          <h3 className="chart-title">Events With Most Participants</h3>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Status</th>
                  <th>Participants</th>
                  <th>End</th>
                </tr>
              </thead>
              <tbody>
                {stats.top_participation_events.map((event) => (
                  <tr key={event.event_id}>
                    <td className="text-truncate">{event.title}</td>
                    <td><span className="badge badge-success">{event.status}</span></td>
                    <td className="fw-600">{event.participant_count}</td>
                    <td className="text-muted">{fmtDate(event.end_at)}</td>
                  </tr>
                ))}
                {stats.top_participation_events.length === 0 && (
                  <tr><td colSpan={4} className="empty-row">No event participation yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
