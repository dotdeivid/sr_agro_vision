import { useEffect } from 'react';
import type { Map as LeafletMap } from 'leaflet';

/**
 * Hook to synchronize zoom and pan between two Leaflet maps
 */
export const useSyncMaps = (
    map1: LeafletMap | null,
    map2: LeafletMap | null
) => {
    useEffect(() => {
        if (!map1 || !map2) return;

        // Sync zoom from map1 to map2
        const syncZoomTo2 = () => {
            const zoom = map1.getZoom();
            if (map2.getZoom() !== zoom) {
                map2.setZoom(zoom);
            }
        };

        // Sync zoom from map2 to map1
        const syncZoomTo1 = () => {
            const zoom = map2.getZoom();
            if (map1.getZoom() !== zoom) {
                map1.setZoom(zoom);
            }
        };

        // Sync center from map1 to map2
        const syncCenterTo2 = () => {
            const center = map1.getCenter();
            map2.setView(center, map2.getZoom(), { animate: false });
        };

        // Sync center from map2 to map1
        const syncCenterTo1 = () => {
            const center = map2.getCenter();
            map1.setView(center, map1.getZoom(), { animate: false });
        };

        // Attach event listeners
        map1.on('zoomend', syncZoomTo2);
        map2.on('zoomend', syncZoomTo1);
        map1.on('moveend', syncCenterTo2);
        map2.on('moveend', syncCenterTo1);

        // Cleanup
        return () => {
            map1.off('zoomend', syncZoomTo2);
            map2.off('zoomend', syncZoomTo1);
            map1.off('moveend', syncCenterTo2);
            map2.off('moveend', syncCenterTo1);
        };
    }, [map1, map2]);
};
