import { apiClient } from './client';
import type {
    SatelliteSearchRequest,
    SatelliteSearchResponse,
    SatelliteDownloadRequest,
    SatelliteDownloadResponse
} from '../types/satellite';

export const copernicusApi = {
    /**
     * Search for Sentinel-2 images
     */
    search: async (request: SatelliteSearchRequest): Promise<SatelliteSearchResponse> => {
        const response = await apiClient.post('/api/v1/copernicus/search', request);
        return response.data;
    },

    /**
     * Download a Sentinel-2 image
     */
    download: async (request: SatelliteDownloadRequest): Promise<SatelliteDownloadResponse> => {
        const response = await apiClient.post('/api/v1/copernicus/download', request);
        return response.data;
    },

    /**
     * Get image metadata
     */
    getMetadata: async (imageId: string): Promise<any> => {
        const response = await apiClient.get(`/api/v1/copernicus/metadata/${imageId}`);
        return response.data;
    },
};
