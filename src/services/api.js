import axios from 'axios';
import { 
  processTelemetryClient, 
  processVideoClient, 
  analyzeWitnessClient,
  deleteEvidenceFromCase
} from './investigationStore';

// Base API configuration from environment or default
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Accept': 'application/json',
  },
});

// Centralized error interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An unexpected error occurred.';
    if (error.response) {
      // Backend returned HTTP error
      message = error.response.data?.detail || error.response.data?.message || `Server Error (${error.response.status})`;
    } else if (error.request) {
      // Backend is unreachable
      message = `Cannot connect to TRACE AI backend at ${BASE_URL}. Ensure the FastAPI server is running.`;
    } else {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);

export const api = {
  // System Health & AI Status
  getHealth: () => apiClient.get('/api/health').then(r => r.data),
  getAIStatus: () => apiClient.get('/api/ai/status').then(r => r.data),
  configureAI: (apiKey, model) => apiClient.post('/api/ai/configure', { api_key: apiKey, model }).then(r => r.data),

  // Incidents
  getIncidents: (params) => apiClient.get('/api/incidents', { params }).then(r => r.data),
  getIncident: (id) => apiClient.get(`/api/incidents/${id}`).then(r => r.data),
  createIncident: (data) => apiClient.post('/api/incidents', data).then(r => r.data),
  updateIncident: (id, data) => apiClient.put(`/api/incidents/${id}`, data).then(r => r.data),
  deleteIncident: (id, confirm = true) => apiClient.delete(`/api/incidents/${id}`, { params: { confirm } }).then(r => r.data),

  // Evidence
  getIncidentEvidence: (incidentId) => apiClient.get(`/api/incidents/${incidentId}/evidence`).then(r => r.data),
  getEvidenceDetail: (evidenceId) => apiClient.get(`/api/evidence/${evidenceId}`).then(r => r.data),
  deleteEvidence: async (evidenceId, incidentId) => {
    try {
      const res = await apiClient.delete(`/api/evidence/${evidenceId}`);
      if (incidentId) deleteEvidenceFromCase(incidentId, evidenceId);
      return res.data;
    } catch (err) {
      if (incidentId) deleteEvidenceFromCase(incidentId, evidenceId);
      return { success: true, deleted: evidenceId, mode: 'local' };
    }
  },
  uploadEvidence: (incidentId, formData, onUploadProgress) => {
    return apiClient.post(`/api/incidents/${incidentId}/evidence`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    }).then(r => r.data);
  },

  // Processing & Kinematics with seamless offline fallbacks
  processTelemetry: async (incidentId, evidenceId) => {
    try {
      const res = await apiClient.post(`/api/incidents/${incidentId}/telemetry/process`, { evidence_id: evidenceId });
      return res.data;
    } catch (err) {
      console.warn('Backend offline, running client-side kinematic parser:', err.message);
      return processTelemetryClient(incidentId, evidenceId);
    }
  },
  processVideo: async (incidentId, evidenceId, sampleRate = 5) => {
    try {
      const res = await apiClient.post(`/api/incidents/${incidentId}/video/process`, {
        evidence_id: evidenceId,
        sample_rate_frames: sampleRate,
      });
      return res.data;
    } catch (err) {
      console.warn('Backend offline, running client-side CV simulation:', err.message);
      return processVideoClient(incidentId, evidenceId);
    }
  },
  analyzeWitness: async (incidentId, evidenceId) => {
    try {
      const res = await apiClient.post(`/api/incidents/${incidentId}/analyze-witness`, { evidence_id: evidenceId });
      return res.data;
    } catch (err) {
      console.warn('Backend offline, running client-side heuristic witness extractor:', err.message);
      return analyzeWitnessClient(incidentId, evidenceId);
    }
  },

  // Timeline & Contradictions
  getTimeline: (incidentId, params) => apiClient.get(`/api/incidents/${incidentId}/timeline`, { params }).then(r => r.data),
  getContradictions: (incidentId) => apiClient.get(`/api/incidents/${incidentId}/contradictions`).then(r => r.data),

  // Reports & AI Summary
  generateAISummary: (incidentId) => apiClient.post(`/api/incidents/${incidentId}/ai-summary`, { incident_id: incidentId }).then(r => r.data),
  getIncidentReport: (incidentId) => apiClient.get(`/api/incidents/${incidentId}/report`).then(r => r.data),
};

export default api;
