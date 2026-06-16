import api from './axios';

export const listQuests = (page = 1, pageSize = 20, isEvent = null) => {
  const params = { page, page_size: pageSize };
  if (isEvent !== null) {
    params.is_event = isEvent;
  }
  return api.get('/admin/quests', { params });
};

export const updateQuest = (questId, payload) =>
  api.patch(`/admin/quests/${questId}`, payload);
