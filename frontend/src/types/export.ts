export type ExportFormat = 'geotiff' | 'png' | 'jpeg' | 'kml';

export interface ExportRequest {
    result_id: string;
    format: ExportFormat;
    quality?: number;
}

export interface ExportResponse {
    download_url: string;
    filename: string;
    file_size: number;
    format: ExportFormat;
}
