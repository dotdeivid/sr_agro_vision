import type { LatLngBoundsExpression } from 'leaflet';

/**
 * Calculate pixel-based bounds for images without georeferencing.
 * Used as a fallback when no CRS/bounds metadata is available.
 */
export const calculateBounds = (
    width: number,
    height: number
): LatLngBoundsExpression => {
    return [
        [0, 0],
        [height, width]
    ];
};

/**
 * Build Leaflet bounds from real WGS84 coordinates returned by the backend.
 * Backend stores bounds as [west, south, east, north] (standard bbox order).
 */
export const calculateBoundsFromGeo = (
    bounds: [number, number, number, number]
): LatLngBoundsExpression => {
    const [west, south, east, north] = bounds;
    return [
        [south, west],  // SW corner → Leaflet [lat, lng]
        [north, east]   // NE corner → Leaflet [lat, lng]
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
 * Get the URL for viewing an image from the backend.
 * Resolves server-side file paths via GET /api/v1/images/view/{filename}
 */
export const getImageUrl = (filepath: string): string => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return `${baseUrl}/api/v1/images/view/${filepath.split('/').pop()}`;
};
