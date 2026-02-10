import React, { useRef, useEffect } from 'react';
import { MapContainer, ImageOverlay, useMap } from 'react-leaflet';
import type { LatLngBoundsExpression, Map as LeafletMap } from 'leaflet';
import styles from './MapViewer.module.css';

interface MapViewerProps {
    imageUrl: string;
    bounds: LatLngBoundsExpression;
    title: string;
    onMapReady?: (map: LeafletMap) => void;
}

// Component to get map instance
const MapInstance: React.FC<{ onReady: (map: LeafletMap) => void }> = ({ onReady }) => {
    const map = useMap();

    useEffect(() => {
        onReady(map);
    }, [map, onReady]);

    return null;
};

export const MapViewer: React.FC<MapViewerProps> = ({
    imageUrl,
    bounds,
    title,
    onMapReady
}) => {
    const mapRef = useRef<LeafletMap | null>(null);

    const handleMapReady = (map: LeafletMap) => {
        mapRef.current = map;
        if (onMapReady) {
            onMapReady(map);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.title}>{title}</div>
            <div className={styles.mapWrapper}>
                <MapContainer
                    bounds={bounds}
                    style={{ height: '100%', width: '100%' }}
                    scrollWheelZoom={true}
                    zoomControl={true}
                >
                    <MapInstance onReady={handleMapReady} />
                    <ImageOverlay
                        url={imageUrl}
                        bounds={bounds}
                        opacity={1}
                    />
                </MapContainer>
            </div>
        </div>
    );
};
