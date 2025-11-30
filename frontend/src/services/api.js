/**
 * API Service for communicating with backend.
 */

import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Parse natural language text to structured JSON.
 */
export const parseText = async (text) => {
  const response = await api.post('/parse', { text });
  return response.data;
};

/**
 * Generate SVG from structured JSON.
 */
export const generateSVG = async (jsonData) => {
  const response = await api.post('/generate', { json: jsonData });
  return response.data;
};

/**
 * Edit existing SVG.
 */
export const editSVG = async (svg, changes) => {
  const response = await api.post('/edit', { svg, changes });
  return response.data;
};

/**
 * Export SVG to different format.
 */
export const exportSVG = async (svg, format, width = 1920, height = 1080) => {
  const response = await api.post('/export', 
    { svg, format, width, height },
    { responseType: format === 'svg' ? 'text' : 'blob' }
  );
  return response.data;
};

/**
 * Health check.
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;

