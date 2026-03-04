export type ModelType = 'espcn' | 'swinir' | 'gan';
export type ScaleFactor = 2 | 4;
export type TaskStatus = 'queued' | 'processing' | 'completed' | 'failed';

export interface InferenceRequest {
    image_id: string;
    model: ModelType;
    scale: ScaleFactor;
    device?: string | null;
}

export interface InferenceResponse {
    task_id: string;
    status: TaskStatus;
    message: string;
}

export interface TaskStatusResponse {
    task_id: string;
    status: TaskStatus;
    progress: number;
    result_id: string | null;
    image_db_id: string | null;
    error: string | null;
}

export interface InferenceResult {
    id: string;
    task_id: string;
    original_image_id: string;
    result_filepath: string;
    model_used: ModelType;
    scale_factor: ScaleFactor;
    psnr: number | null;
    ssim: number | null;
    processing_time: number | null;
    created_at: string;
}

export interface ModelInfo {
    id: ModelType;
    name: string;
    description: string;
    icon: string;
}
