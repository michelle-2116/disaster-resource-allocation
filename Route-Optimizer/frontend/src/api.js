import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
});

export const getMapData = () => api.get('/map-data');
export const getIncidents = () => api.get('/incidents');
export const ingestNews = (text) => api.post('/ingest', { text });
export const approveNeed = (id) => api.post(`/allocate/approve/${id}`);
export const addBlockedRoad = (data) => api.post('/blocked-roads', data);

export default api;
