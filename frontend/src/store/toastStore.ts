import { create } from 'zustand';
import type { ToastType } from '../components/common/Toast';

interface Toast {
    id: string;
    type: ToastType;
    message: string;
}

interface ToastState {
    toasts: Toast[];
    addToast: (type: ToastType, message: string) => void;
    removeToast: (id: string) => void;
    success: (message: string) => void;
    error: (message: string) => void;
    warning: (message: string) => void;
    info: (message: string) => void;
}

export const useToastStore = create<ToastState>((set) => {
    const addToast = (type: ToastType, message: string) => {
        const id = Math.random().toString(36).substr(2, 9);
        set((state) => ({ toasts: [...state.toasts, { id, type, message }] }));
    };

    return {
        toasts: [],
        addToast,
        removeToast: (id) =>
            set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
        success: (message) => addToast('success', message),
        error: (message) => addToast('error', message),
        warning: (message) => addToast('warning', message),
        info: (message) => addToast('info', message),
    };
});
