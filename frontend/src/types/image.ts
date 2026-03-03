export interface ImageMetadata {
    id: string;
    filename: string;
    filepath: string;
    file_size: number;
    bands?: number;
    /** Number of raster bands (same as bands, exposed by new ImageResponse) */
    num_channels?: number;
    width?: number;
    height?: number;
    created_at?: string;
    uploaded_at?: string;
    project_id?: string;
    /**
     * GeoTIFF spatial metadata extracted by rasterio on upload.
     * bounds: [west, south, east, north] in WGS84
     */
    image_metadata?: {
        bounds?: [number, number, number, number] | null;
        crs?: string | null;
        dtype?: string | null;
    } | null;
}

export interface UploadProgress {
    loaded: number;
    total: number;
    percentage: number;
}
