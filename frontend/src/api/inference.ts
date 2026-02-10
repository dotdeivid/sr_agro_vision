import { apiClient } from './client';
import type {
    InferenceRequest,
    InferenceResponse,
    TaskStatusResponse,
    InferenceResult
} from '../types/inference';

export const inferenceApi = {
    /**
     * Start SR inference process
     */
    startInference: async (data: InferenceRequest): Promise<InferenceResponse> => {
        const response = await apiClient.post('/api/v1/inference/process', data);
        return response.data;
    },

    /**
     * Get task status
     */
    getStatus: async (taskId: string): Promise<TaskStatusResponse> => {
        const response = await apiClient.get(`/api/v1/inference/status/${taskId}`);
        return response.data;
    },

    /**
     * Get inference result
     */
    getResult: async (resultId: string): Promise<InferenceResult> => {
        const response = await apiClient.get(`/api/v1/inference/results/${resultId}`);
        return response.data;
    },

    /**
     * List all tasks for current user
     */
    listTasks: async (skip: number = 0, limit: number = 100): Promise<TaskStatusResponse[]> => {
        const response = await apiClient.get('/api/v1/inference/tasks', {
            params: { skip, limit }
        });
        return response.data;
    },
};
