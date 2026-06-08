import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AdminLayout from './components/AdminLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UsersPage from './pages/UsersPage';
import QuestsPage from './pages/QuestsPage';
import MapPage from './pages/MapPage';
import BadgesPage from './pages/BadgesPage';
import PostsPage from './pages/PostsPage';
import EventsPage from './pages/EventsPage';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<AdminLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/quests" element={<QuestsPage />} />
          <Route path="/posts" element={<PostsPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/badges" element={<BadgesPage />} />
          <Route path="/map" element={<MapPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
