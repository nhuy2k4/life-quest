import api from './axios';

export const listBadges = (page = 1, pageSize = 50) =>
  api.get('/admin/badges', { params: { page, page_size: pageSize } });

export const listBadgeConditionTypes = () =>
  api.get('/admin/badges/condition-types');

export const createBadge = (payload) =>
  api.post('/admin/badges', payload);

export const updateBadge = (badgeId, payload) =>
  api.patch(`/admin/badges/${badgeId}`, payload);

export const deleteBadge = (badgeId) =>
  api.delete(`/admin/badges/${badgeId}`);

export const uploadBadgeIcon = (file) => {
  const form = new FormData();
  form.append('file', file);
  form.append('idempotency_key', `badge-${Date.now()}`);
  return api.post('/uploads/image', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
