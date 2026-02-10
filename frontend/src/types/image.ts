export interface ImageMetadata {
    id: string;
    filename: string;
    filepath: string;
    file_size: number;
    bands?: number;
    width?: number;
    height?: number;
    created_at: string;
    project_id?: string;
}

export interface UploadProgress {
    loaded: number;
    total: number;
    percentage: number;
}
