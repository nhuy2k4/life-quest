import api from './axios';

export const listEvents = (status) =>
  api.get('/events', { params: status ? { status } : {} });

export const getEvent = (eventId) => api.get(`/events/${eventId}`);

export const createEvent = (payload) => api.post('/events', payload);

export const updateEvent = (eventId, payload) => api.patch(`/events/${eventId}`, payload);

export const endEvent = (eventId) => api.post(`/events/${eventId}/end`);
