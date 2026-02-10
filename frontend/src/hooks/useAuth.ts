import { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';

export const useAuth = () => {
    const { user, isAuthenticated, setAuth, logout } = useAuthStore();

    useEffect(() => {
        // Load user if token exists but user is not loaded
        if (isAuthenticated && !user) {
            authApi.getMe()
                .then((userData) => {
                    const token = localStorage.getItem('access_token') || '';
                    setAuth(userData, token);
                })
                .catch(() => {
                    logout();
                });
        }
    }, [isAuthenticated, user, setAuth, logout]);

    return { user, isAuthenticated, logout };
};
