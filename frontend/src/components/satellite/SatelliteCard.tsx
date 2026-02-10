import React from 'react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import styles from './SatelliteCard.module.css';
import type { SatelliteImage } from '../../types/satellite';

interface SatelliteCardProps {
    image: SatelliteImage;
    onDownload: (imageId: string) => void;
    downloading?: boolean;
}

export const SatelliteCard: React.FC<SatelliteCardProps> = ({
    image,
    onDownload,
    downloading = false
}) => {
    const formatDate = (dateString: string): string => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    };

    const getCloudCoverColor = (cloudCover: number): string => {
        if (cloudCover < 10) return styles.excellent;
        if (cloudCover < 30) return styles.good;
        if (cloudCover < 50) return styles.fair;
        return styles.poor;
    };

    return (
        <Card className={styles.card}>
            {/* Thumbnail */}
            <div className={styles.thumbnail}>
                {image.thumbnail_url ? (
                    <img src={image.thumbnail_url} alt={image.title} className={styles.image} />
                ) : (
                    <div className={styles.placeholder}>🛰️</div>
                )}

                {/* Cloud Cover Badge */}
                <div className={`${styles.badge} ${getCloudCoverColor(image.cloud_cover)}`}>
                    ☁️ {image.cloud_cover.toFixed(1)}%
                </div>
            </div>

            {/* Info */}
            <div className={styles.info}>
                <h3 className={styles.title} title={image.title}>
                    {image.title}
                </h3>

                <div className={styles.metadata}>
                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Fecha:</span>
                        <span className={styles.metaValue}>{formatDate(image.sensing_time)}</span>
                    </div>

                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Plataforma:</span>
                        <span className={styles.metaValue}>{image.platform}</span>
                    </div>

                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Tamaño:</span>
                        <span className={styles.metaValue}>{image.size_mb.toFixed(0)} MB</span>
                    </div>

                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Bandas:</span>
                        <span className={styles.metaValue}>{image.bands_available.length}</span>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className={styles.actions}>
                <Button
                    onClick={() => onDownload(image.id)}
                    size="sm"
                    loading={downloading}
                    disabled={downloading}
                    fullWidth
                >
                    {downloading ? 'Descargando...' : '📥 Descargar'}
                </Button>
            </div>
        </Card>
    );
};
