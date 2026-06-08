import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  FiAward, FiCalendar, FiGrid, FiUsers, FiMap, FiLogOut, FiZap, FiMenu, FiX, FiMapPin, FiMessageSquare
} from 'react-icons/fi';
import { useState } from 'react';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: FiGrid, id: 'nav-dashboard' },
  { to: '/users', label: 'Users', icon: FiUsers, id: 'nav-users' },
  { to: '/quests', label: 'Quests', icon: FiMap, id: 'nav-quests' },
  { to: '/posts', label: 'Posts', icon: FiMessageSquare, id: 'nav-posts' },
  { to: '/events', label: 'Events', icon: FiCalendar, id: 'nav-events' },
  { to: '/badges', label: 'Badges', icon: FiAward, id: 'nav-badges' },
  { to: '/map', label: 'Map POI', icon: FiMapPin, id: 'nav-map' },
];

export default function Sidebar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    signOut();
    navigate('/login');
  };

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-logo">
          <FiZap size={20} />
        </div>
        {!collapsed && <span className="brand-name">LifeQuest</span>}
        <button
          id="sidebar-toggle"
          className="sidebar-toggle"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? <FiMenu size={18} /> : <FiX size={18} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, label, icon: Icon, id }) => (
          <NavLink
            key={to}
            id={id}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon size={18} />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* User profile */}
      <div className="sidebar-footer">
        {!collapsed && user && (
          <div className="sidebar-user">
            <div className="avatar-sm">{(user.display_name || user.username || 'A')[0].toUpperCase()}</div>
            <div className="sidebar-user-info">
              <div className="fw-600 text-sm">{user.display_name || user.username}</div>
              <div className="text-muted" style={{ fontSize: 11 }}>Administrator</div>
            </div>
          </div>
        )}
        <button id="logout-btn" className="logout-btn" onClick={handleLogout} title="Logout">
          <FiLogOut size={17} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
