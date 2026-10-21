import axios from 'axios';
import { AuthResponse, AuditListResponse, ComplianceReport, SearchResultItem } from './types';

// Use environment variable if provided, fallback to direct node backend URL or relative proxy
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minutes for long AI evaluations
});

// Request interceptor to automatically attach JWT Bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiry / unauthenticated
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // If unauthorized, clear storage so user can re-login
      if (window.location.pathname !== '/login') {
        // Optional dispatch or handling
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },

  register: async (name: string, email: string, password: string): Promise<AuthResponse> => {
    const res = await api.post('/auth/register', { name, email, password });
    return res.data;
  },

  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data;
  },
};

export const complianceApi = {
  uploadDocument: async (file: File): Promise<{ success: boolean; filename: string; extracted_text: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/upload/policy', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 45000,
    });
    return res.data;
  },

  checkCompliance: async (payload: {
    question: string;
    company_evidence: string;
    compliance_area: string;
    facility_description?: string | null;
    product_name?: string;
    top_k?: number;
  }): Promise<{ success: boolean; data: ComplianceReport }> => {
    const res = await api.post('/compliance/check', payload, {
      timeout: 120000,
    });
    return res.data;
  },

  getAuditHistory: async (limit = 50, offset = 0): Promise<AuditListResponse> => {
    const res = await api.get(`/audit?limit=${limit}&offset=${offset}`, {
      timeout: 15000,
    });
    return res.data;
  },

  getAuditDetail: async (id: string | number): Promise<{ success: boolean; data: ComplianceReport }> => {
    const res = await api.get(`/audit/${id}`, {
      timeout: 15000,
    });
    return res.data;
  },

  searchRegulations: async (
    query: string,
    top_k = 5
  ): Promise<{ success: boolean; data: { results: SearchResultItem[] } }> => {
    const res = await api.post(
      '/compliance/search',
      { query, top_k },
      { timeout: 30000 }
    );
    return res.data;
  },
};

export default api;
