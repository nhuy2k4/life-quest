import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, getMe } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';
import { FiUser, FiLock, FiZap } from 'react-icons/fi';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signIn } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await login(username, password);
      const { access_token } = res.data;
      // Fetch user profile
      localStorage.setItem('access_token', access_token);
      const meRes = await getMe();
      // API /users/me trả về { data: { ...user } } dạng wrapped
      const user = meRes.data?.data ?? meRes.data;
      if (user.role !== 'admin') {
        setError('This account does not have Admin privileges.');
        localStorage.removeItem('access_token');
        setLoading(false);
        return;
      }
      signIn(access_token, user);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-bg-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>
      <div className="login-card">
        <div className="login-logo">
          <FiZap size={32} />
        </div>
        <h1 className="login-title">LifeQuest Admin</h1>
        <p className="login-subtitle">Sign in to manage the system</p>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <FiUser className="input-icon" />
            <input
              id="username"
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
          </div>
          <div className="input-group">
            <FiLock className="input-icon" />
            <input
              id="password"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          {error && <p className="login-error">{error}</p>}
          <button
            id="login-submit"
            type="submit"
            className="btn-primary w-full"
            disabled={loading}
          >
            {loading ? <span className="spinner-sm"></span> : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
