import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401 errors — clear auth state via the store so Zustand + React Router
// handle the redirect through ProtectedRoute, avoiding a full page reload.
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Use getState() to access the store outside a React component
            useAuthStore.getState().logout();
            // Do NOT call window.location.href — let ProtectedRoute redirect
        }
        return Promise.reject(error);
    }
);

