import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 404) {
      console.error('Endpoint not found:', error.config?.url);
    }
    throw error;
  }
);

// Recommendations
export const getClientRecommendations = (clientId: number | string) =>
  api.get(`${API_PREFIX}/recommendations/client/${clientId}`);

export const getProductRecommendations = (productId: number | string) =>
  api.get(`${API_PREFIX}/recommendations/product/${productId}`);

export const getTopRecommendations = () =>
  api.get(`${API_PREFIX}/recommendations/top`);

export const getSimilarCustomers = () =>
  api.get(`${API_PREFIX}/recommendations/clients/similar-all`);

// Customers
export const getSegments = (limit?: number) =>
  api.get(`${API_PREFIX}/customers/segments`, {
    params: limit === undefined ? undefined : { limit },
  });

export const getCustomerSegments = (limit?: number) =>
  api.get(`${API_PREFIX}/customers/segments`, {
    params: limit === undefined ? undefined : { limit },
  });

export const getSegmentCustomers = (segmentId: number | string) =>
  api.get(`${API_PREFIX}/customers/segments/${segmentId}`);

export const getTopCustomers = () =>
  api.get(`${API_PREFIX}/customers/top`);

// Analytics
export const getCategoryAnalytics = () =>
  api.get(`${API_PREFIX}/analytics/categories`);

export const getGraphStats = () =>
  api.get(`${API_PREFIX}/analytics/graph-stats`);

// Algorithms
export const runAllAlgorithms = () =>
  api.post(`${API_PREFIX}/algorithms/run_all`);

export const getAlgorithmsStatus = () =>
  api.get(`${API_PREFIX}/algorithms/status`);

// Diagnostics
export const getDiagnosticCustomers = (limit: number = 100) =>
  api.get(`${API_PREFIX}/algorithms/diagnose/clients`, { params: { limit } });

export const getDiagnosticStats = () =>
  api.get(`${API_PREFIX}/algorithms/diagnose/stats`);

export const getDiagnosticGraphs = () =>
  api.get(`${API_PREFIX}/algorithms/diagnose/graphs`);

export const getDiagnosticClient = (clientId: string) =>
  api.get(`${API_PREFIX}/algorithms/diagnose/client/${clientId}`);

export const getDiagnosticProducts = (limit: number) =>
  api.get(`${API_PREFIX}/algorithms/diagnose/products`, { params: { limit } });

export default api;
