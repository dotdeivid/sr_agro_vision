import type { LatLngBoundsExpression } from 'leaflet';

/**
 * Calculate bounds for image overlay
 * For GeoTIFF without real coordinates, we use pixel coordinates
 */
export const calculateBounds = (
    width: number,
    height: number
): LatLngBoundsExpression => {
    // Simple pixel-based bounds
    // In a real app, you would parse actual GeoTIFF coordinates
    return [
        [0, 0],
        [height, width]
    ];
};

/**
 * Format coordinates for display
 */
export const formatCoords = (lat: number, lng: number): string => {
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
};

/**
 * Calculate center point
 */
export const calculateCenter = (
    bounds: LatLngBoundsExpression
): [number, number] => {
    const [[lat1, lng1], [lat2, lng2]] = bounds as [[number, number], [number, number]];
    return [(lat1 + lat2) / 2, (lng1 + lng2) / 2];
};

/**
 * Get image URL for display
 * In production, this would serve the actual GeoTIFF as PNG/JPEG
 */
export const getImageUrl = (filepath: string): string => {
    // For now, return a placeholder or server URL
    // In production: convert GeoTIFF to web-friendly format
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return `${baseUrl}/api/v1/images/view/${filepath.split('/').pop()}`;
};
