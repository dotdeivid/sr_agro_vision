import { apiClient } from './client';
import type { ExportRequest, ExportResponse } from '../types/export';

export const exportApi = {
    /**
     * Export result in specified format
     */
    export: async (request: ExportRequest): Promise<ExportResponse> => {
        const response = await apiClient.post('/api/v1/export/export', request);
        return response.data;
    },

    /**
     * Download exported file
     */
    download: (filename: string): string => {
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        return `${baseUrl}/api/v1/export/download/${filename}`;
    },
};
