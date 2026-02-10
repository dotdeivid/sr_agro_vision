import React from 'react';
import { SatelliteCard } from './SatelliteCard';
import styles from './ImageGrid.module.css';
import type { SatelliteImage } from '../../types/satellite';

interface ImageGridProps {
    images: SatelliteImage[];
    onDownload: (imageId: string) => void;
    downloadingId?: string | null;
}

export const ImageGrid: React.FC<ImageGridProps> = ({
    images,
    onDownload,
    downloadingId = null
}) => {
    if (images.length === 0) {
        return (
            <div className={styles.empty}>
                <div className={styles.emptyIcon}>🛰️</div>
                <p className={styles.emptyText}>No se encontraron imágenes</p>
                <p className={styles.emptyHint}>Intenta con diferentes fechas o área</p>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2 className={styles.title}>
                    Resultados ({images.length})
                </h2>
            </div>

            <div className={styles.grid}>
                {images.map((image) => (
                    <SatelliteCard
                        key={image.id}
                        image={image}
                        onDownload={onDownload}
                        downloading={downloadingId === image.id}
                    />
                ))}
            </div>
        </div>
    );
};
