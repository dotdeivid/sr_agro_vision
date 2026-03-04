import { apiClient } from './client';

export interface Project {
    id: string;
    name: string;
    description: string;
    user_id: string;
    created_at: string;
    updated_at: string;
    image_count: number;
}

export interface ProjectCreate {
    name: string;
    description?: string;
}

export interface ProjectUpdate {
    name?: string;
    description?: string;
}

export const projectsApi = {
    list: async (): Promise<Project[]> => {
        const response = await apiClient.get('/api/v1/projects/');
        return response.data;
    },

    getById: async (id: string): Promise<Project> => {
        const response = await apiClient.get(`/api/v1/projects/${id}`);
        return response.data;
    },

    create: async (data: ProjectCreate): Promise<Project> => {
        const response = await apiClient.post('/api/v1/projects/', data);
        return response.data;
    },

    update: async (id: string, data: ProjectUpdate): Promise<Project> => {
        const response = await apiClient.put(`/api/v1/projects/${id}`, data);
        return response.data;
    },

    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/api/v1/projects/${id}`);
    },

    getImages: async (id: string) => {
        const response = await apiClient.get(`/api/v1/projects/${id}/images`);
        return response.data;
    },
};
