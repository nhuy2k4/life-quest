import { useState, useEffect } from 'react';
import { listUsers } from '../api/users';
import { listQuests } from '../api/quests';
import {
  FiUsers, FiMap, FiActivity, FiTrendingUp
} from 'react-icons/fi';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const DIFFICULTY_COLORS = {
  easy: '#4ade80',
  medium: '#facc15',
  hard: '#f87171',
};

const STAT_CARDS = [
  { id: 'total-users', key: 'totalUsers', label: 'Total Users', icon: FiUsers, color: '#6366f1' },
  { id: 'active-users', key: 'activeUsers', label: 'Active Users', icon: FiActivity, color: '#22d3ee' },
  { id: 'total-quests', key: 'totalQuests', label: 'Total Quests', icon: FiMap, color: '#a78bfa' },
  { id: 'active-quests', key: 'activeQuests', label: 'Active Quests', icon: FiTrendingUp, color: '#4ade80' },
];

export default function DashboardPage() {
  const [stats, setStats] = useState({ totalUsers: 0, activeUsers: 0, totalQuests: 0, activeQuests: 0 });
  const [questDiffData, setQuestDiffData] = useState([]);
  const [userRoleData, setUserRoleData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listUsers(1, 100), listQuests(1, 100)]).then(([uRes, qRes]) => {
      const users = uRes.data.users || [];
      const quests = qRes.data.quests || [];

      setStats({
        totalUsers: uRes.data.total || users.length,
        activeUsers: users.filter(u => !u.is_banned && u.is_verified).length,
        totalQuests: qRes.data.total || quests.length,
        activeQuests: quests.filter(q => q.is_active).length,
      });

      // Difficulty pie
      const diffCount = { easy: 0, medium: 0, hard: 0 };
      quests.forEach(q => { if (diffCount[q.difficulty] !== undefined) diffCount[q.difficulty]++; });
      setQuestDiffData([
        { name: 'Easy', value: diffCount.easy, color: DIFFICULTY_COLORS.easy },
        { name: 'Medium', value: diffCount.medium, color: DIFFICULTY_COLORS.medium },
        { name: 'Hard', value: diffCount.hard, color: DIFFICULTY_COLORS.hard },
      ]);

      // Role distribution
      const roleCount = { user: 0, admin: 0 };
      users.forEach(u => { if (roleCount[u.role] !== undefined) roleCount[u.role]++; });
      setUserRoleData([
        { name: 'Users', value: roleCount.user, color: '#6366f1' },
        { name: 'Admins', value: roleCount.admin, color: '#f43f5e' },
      ]);

      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  // XP bar chart — top 10 users by XP (simulated from loaded data)
  const [topUsers, setTopUsers] = useState([]);
  useEffect(() => {
    listUsers(1, 100).then(res => {
      const sorted = [...(res.data.users || [])].sort((a, b) => (b.xp || 0) - (a.xp || 0)).slice(0, 8);
      setTopUsers(sorted.map(u => ({ name: u.username || u.display_name, xp: u.xp || 0 })));
    });
  }, []);

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
          <p className="page-subtitle">LifeQuest System Overview</p>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid">
        {STAT_CARDS.map(({ id, key, label, icon: Icon, color }) => (
          <div key={key} id={id} className="stat-card">
            <div className="stat-icon" style={{ background: `${color}22`, color }}>
              <Icon size={22} />
            </div>
            <div>
              <div className="stat-value">{stats[key].toLocaleString()}</div>
              <div className="stat-label">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Top users by XP */}
        <div className="card chart-card">
          <h3 className="chart-title">Top Users by XP</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={topUsers} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
                itemStyle={{ color: '#a78bfa' }}
              />
              <Bar dataKey="xp" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Quest difficulty */}
        <div className="card chart-card">
          <h3 className="chart-title">Quest Difficulty Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={questDiffData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value">
                {questDiffData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 13 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* User roles */}
        <div className="card chart-card">
          <h3 className="chart-title">User Role Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={userRoleData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value">
                {userRoleData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 13 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
