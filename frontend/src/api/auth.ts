import { apiClient } from './client';
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '../types/api';

export const authApi = {
    login: async (data: LoginRequest): Promise<AuthResponse> => {
        // FastAPI OAuth2 expects form data
        const formData = new URLSearchParams();
        formData.append('username', data.email);
        formData.append('password', data.password);

        const response = await apiClient.post('/api/v1/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });

        return response.data;
    },

    register: async (data: RegisterRequest): Promise<User> => {
        const response = await apiClient.post('/api/v1/auth/register', data);
        return response.data;
    },

    getMe: async (): Promise<User> => {
        const response = await apiClient.get('/api/v1/users/me');
        return response.data;
    },
};
