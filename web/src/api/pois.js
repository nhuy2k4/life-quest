import api from './axios';

export const listPois = (page = 1, pageSize = 500) =>
  api.get('/admin/pois', { params: { page, page_size: pageSize } });

export const createPoi = (payload) =>
  api.post('/admin/pois', payload);

export const updatePoi = (poiId, payload) =>
  api.patch(`/admin/pois/${poiId}`, payload);

export const deletePoi = (poiId) =>
  api.delete(`/admin/pois/${poiId}`);
