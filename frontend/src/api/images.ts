import { apiClient } from './client';
import type { ImageMetadata } from '../types/image';

export const imagesApi = {
    /**
     * Upload a GeoTIFF image
     */
    upload: async (
        file: File,
        projectId: string = 'default',
        onProgress?: (progress: number) => void
    ): Promise<ImageMetadata> => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_id', projectId);

        const response = await apiClient.post('/api/v1/images/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                if (progressEvent.total && onProgress) {
                    const percentage = Math.round(
                        (progressEvent.loaded * 100) / progressEvent.total
                    );
                    onProgress(percentage);
                }
            },
        });

        return response.data;
    },

    /**
     * Get all images
     */
    list: async (): Promise<ImageMetadata[]> => {
        const response = await apiClient.get('/api/v1/images/');
        return response.data;
    },

    /**
     * Get image by ID
     */
    getById: async (id: string): Promise<ImageMetadata> => {
        const response = await apiClient.get(`/api/v1/images/${id}`);
        return response.data;
    },

    /**
     * Delete image
     */
    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/api/v1/images/${id}`);
    },

    /**
     * Move image to a different project
     */
    moveToProject: async (imageId: string, projectId: string): Promise<ImageMetadata> => {
        const response = await apiClient.patch(
            `/api/v1/images/${imageId}/move?project_id=${projectId}`
        );
        return response.data;
    },
};
