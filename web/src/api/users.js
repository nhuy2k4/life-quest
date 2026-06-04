import api from './axios';

export const listUsers = (page = 1, pageSize = 20) =>
  api.get('/admin/users', { params: { page, page_size: pageSize } });

export const banUser = (userId, is_banned) =>
  api.patch(`/admin/users/${userId}/ban`, { is_banned });

export const updateUser = (userId, data) =>
  api.patch(`/admin/users/${userId}`, data);
