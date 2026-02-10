import { apiClient } from './client';
import type { AnalysisRequest, AnalysisResult } from '../types/analysis';

export const analysisApi = {
    /**
     * Analyze image and calculate vegetation index
     */
    analyze: async (request: AnalysisRequest): Promise<AnalysisResult> => {
        const response = await apiClient.post('/api/v1/analysis/analyze', request);
        return response.data;
    },

    /**
     * Get analysis result
     */
    getResult: async (resultId: string): Promise<AnalysisResult> => {
        const response = await apiClient.get(`/api/v1/analysis/results/${resultId}`);
        return response.data;
    },
};
