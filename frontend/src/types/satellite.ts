export interface SatelliteSearchRequest {
    bbox: [number, number, number, number]; // [lon_min, lat_min, lon_max, lat_max]
    start_date: string; // YYYY-MM-DD
    end_date: string; // YYYY-MM-DD
    max_cloud_cover: number; // 0-100
    max_results: number; // 1-100
}

export interface SatelliteImage {
    id: string;
    title: string;
    product_type: string;
    platform: string;
    sensing_time: string;
    cloud_cover: number;
    footprint: string; // WKT polygon
    thumbnail_url: string;
    download_url: string;
    size_mb: number;
    bands_available: string[];
}

export interface SatelliteSearchResponse {
    total_results: number;
    images: SatelliteImage[];
}

export interface SatelliteDownloadRequest {
    image_id: string;
    bands?: string[];
    project_id?: string;
}

export interface SatelliteDownloadResponse {
    task_id: string;
    status: string;
    message: string;
}
