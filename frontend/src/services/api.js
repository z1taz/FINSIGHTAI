import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors (like 401 Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/signup')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (email, password) => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    
    const response = await api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  
  signup: async (email, fullName, password) => {
    const response = await api.post('/auth/signup', {
      email,
      full_name: fullName,
      password,
    });
    return response.data;
  },
  
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateProfile: async (data) => {
    const response = await api.put('/auth/profile', data);
    return response.data;
  },
};

export const casesAPI = {
  listCases: async (params = {}) => {
    const response = await api.get('/cases', { params });
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/cases/stats/overview');
    return response.data;
  },

  getCaseDetail: async (caseId) => {
    const response = await api.get(`/cases/${caseId}`);
    return response.data;
  },

  triggerInvestigation: async (caseId) => {
    const response = await api.post(`/cases/${caseId}/investigate`);
    return response.data;
  },

  submitDecision: async (caseId, decision, notes = '') => {
    const response = await api.post(`/cases/${caseId}/decide`, { decision, notes });
    return response.data;
  },

  getAuditTrail: async (caseId) => {
    const response = await api.get(`/cases/${caseId}/audit-trail`);
    return response.data;
  },
};

export const networkAPI = {
  getGraph: async (limit = 60) => {
    const response = await api.get('/network/graph', { params: { limit } });
    return response.data;
  },

  getClusters: async () => {
    const response = await api.get('/network/clusters');
    return response.data;
  },
};

export const policiesAPI = {
  getAll: async () => {
    const response = await api.get('/policies');
    return response.data;
  },

  simulate: async (data) => {
    const response = await api.post('/policies/simulate', data);
    return response.data;
  },
};

export const governanceAPI = {
  getModels: async () => {
    const response = await api.get('/governance/models');
    return response.data;
  },

  getVersions: async () => {
    const response = await api.get('/governance/versions');
    return response.data;
  },

  getProductMetrics: async () => {
    const response = await api.get('/governance/product-metrics');
    return response.data;
  },
};

export const evaluationAPI = {
  getResults: async () => {
    const response = await api.get('/evaluation/results');
    return response.data;
  },

  runBenchmark: async () => {
    const response = await api.post('/evaluation/run');
    return response.data;
  },
};

export const adminAPI = {
  getUsers: async () => {
    const response = await api.get('/admin/users');
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/admin/stats');
    return response.data;
  },
};

export const transactionsAPI = {
  getTransactions: async (params = {}) => {
    const response = await api.get('/transactions', { params });
    return response.data;
  },
  
  createTransaction: async (data) => {
    const response = await api.post('/transactions', data);
    return response.data;
  },
  
  uploadStatement: async (formData) => {
    const response = await api.post('/transactions/upload-statement', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deleteTransaction: async (id) => {
    const response = await api.delete(`/transactions/${id}`);
    return response.data;
  },
};

export const analyticsAPI = {
  getSpendingSummary: async () => {
    const response = await api.get('/analytics/spending-summary');
    return response.data;
  },
  
  getMonthlyTrend: async () => {
    const response = await api.get('/analytics/monthly-trend');
    return response.data;
  },
  
  getAnomalies: async () => {
    const response = await api.get('/analytics/anomalies');
    return response.data;
  },
  
  trainModel: async () => {
    const response = await api.post('/analytics/train');
    return response.data;
  },
};

export default api;
