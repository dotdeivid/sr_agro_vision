import { create } from 'zustand';
import { inferenceApi } from '../api/inference';
import { useToastStore } from './toastStore';

export interface DownloadTask {
    taskId: string;
    imageId: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    progress: number;
    error?: string;
    imageDbId?: string;
}

interface DownloadState {
    tasks: DownloadTask[];
    addTask: (taskId: string, imageId: string) => void;
    dismissTask: (taskId: string) => void;
    activeCount: () => number;
}

// Polling intervals keyed by taskId
const pollIntervals: Record<string, ReturnType<typeof setInterval>> = {};

export const useDownloadStore = create<DownloadState>((set, get) => ({
    tasks: [],

    addTask: (taskId, imageId) => {
        set((s) => ({
            tasks: [...s.tasks, { taskId, imageId, status: 'queued', progress: 0 }],
        }));

        // Start polling
        const interval = setInterval(async () => {
            try {
                const statusData = await inferenceApi.getStatus(taskId);
                const prev = get().tasks.find((t) => t.taskId === taskId);
                const wasActive = prev && (prev.status === 'queued' || prev.status === 'processing');

                set((s) => ({
                    tasks: s.tasks.map((t) =>
                        t.taskId === taskId
                            ? {
                                ...t,
                                status: statusData.status as DownloadTask['status'],
                                progress: statusData.progress,
                                error: statusData.error ?? undefined,
                                imageDbId: statusData.image_db_id ?? undefined,
                            }
                            : t,
                    ),
                }));

                if (statusData.status === 'completed' || statusData.status === 'failed') {
                    clearInterval(interval);
                    delete pollIntervals[taskId];

                    // Trigger global toast
                    if (wasActive) {
                        const toast = useToastStore.getState();
                        if (statusData.status === 'completed') {
                            toast.success('Descarga completada — la imagen está disponible en Mis Imágenes');
                        } else {
                            toast.error(`Descarga fallida: ${statusData.error || 'Error desconocido'}`);
                        }
                    }
                }
            } catch {
                // Network error — keep polling
            }
        }, 3000);

        pollIntervals[taskId] = interval;
    },

    dismissTask: (taskId) => {
        if (pollIntervals[taskId]) {
            clearInterval(pollIntervals[taskId]);
            delete pollIntervals[taskId];
        }
        set((s) => ({ tasks: s.tasks.filter((t) => t.taskId !== taskId) }));
    },

    activeCount: () => {
        return get().tasks.filter(
            (t) => t.status === 'queued' || t.status === 'processing',
        ).length;
    },
}));
