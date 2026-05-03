import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const key = process.env.NEXT_PUBLIC_API_KEY || 'demo-key';
  if (key !== 'demo-key') {
    config.headers['X-API-Key'] = key;
  }
  return config;
});

// Discovery
export const discovery = {
  start: (data: { reaction: string; type: string; constraints?: any }) => api.post('/discovery/start', data),
  status: (runId: string) => api.get(`/discovery/${runId}/status`),
  results: (runId: string, page = 1) => api.get(`/discovery/${runId}/results?page=${page}`),
};

// Reaction
export const reaction = {
  parse: (text: string) => api.post('/reaction/parse', { natural_language: text }),
};

// Experiment
export const experiment = {
  log: (data: any[]) => api.post('/experiment/log', { data }),
};

// Model
export const model = {
  health: () => api.get('/model/health'),
  retrain: () => api.post('/model/retrain'),
};

// Viz
export const visualization = {
  molecule: (id: string) => api.get(`/visualizations/molecule/${id}`),
  energy: (candidateId: string, reactionId: string) => api.get(`/visualizations/energy/${candidateId}/${reactionId}`),
};

// Project
export const project = {
  create: (name: string) => api.post('/project/create', { name }),
  feed: (id: string) => api.get(`/project/${id}/feed`),
};

export default api;
