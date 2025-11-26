import axios from 'axios';

export const APIURL = "http://127.0.0.1:8000";

// Create axios instance with default configuration
const api = axios.create({
  baseURL: APIURL,
  withCredentials: true, // Enable sending cookies with requests
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add response interceptor to handle 401 errors (expired token)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only redirect to login on 401 if it's NOT the verify endpoint
    if (error.response?.status === 401 && !error.config?.url?.includes('/api/auth/verify')) {
      // Token expired or invalid - redirect to login
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('token_expiry');
      localStorage.removeItem('role');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
