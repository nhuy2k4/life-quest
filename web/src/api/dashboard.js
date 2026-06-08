import api from './axios';

export const getDashboardStats = () => api.get('/admin/dashboard-stats');
