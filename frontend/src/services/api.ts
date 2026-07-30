import axios from 'axios';

// Create a base instance pointing to your FastAPI backend
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
});

// Add an "interceptor" to automatically attach the JWT token to every request
api.interceptors.request.use((config) => {
  // Check if a token exists in the browser's local storage
  const token = localStorage.getItem('token');
  
  if (token && config.headers) {
    // If it exists, attach it as a Bearer token for FastAPI to verify
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;