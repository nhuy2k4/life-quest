import api from './axios';

export const listQuests = (page = 1, pageSize = 20) =>
  api.get('/admin/quests', { params: { page, page_size: pageSize } });

export const updateQuest = (questId, payload) =>
  api.patch(`/admin/quests/${questId}`, payload);
