import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import styles from './ImageCard.module.css';
import type { ImageMetadata } from '../../types/image';

interface ImageCardProps {
    image: ImageMetadata;
    onDelete: (id: string) => void;
}

export const ImageCard: React.FC<ImageCardProps> = ({ image, onDelete }) => {
    const navigate = useNavigate();

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    const formatDate = (dateString: string): string => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const handleProcessSR = () => {
        navigate(`/process/${image.id}`);
    };

    const handleDelete = () => {
        if (window.confirm(`¿Eliminar ${image.filename}?`)) {
            onDelete(image.id);
        }
    };

    return (
        <Card className={styles.card}>
            <div className={styles.thumbnail}>
                <div className={styles.icon}>🖼️</div>
            </div>

            <div className={styles.info}>
                <h3 className={styles.filename} title={image.filename}>
                    {image.filename}
                </h3>

                <div className={styles.metadata}>
                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Tamaño:</span>
                        <span className={styles.metaValue}>{formatFileSize(image.file_size)}</span>
                    </div>

                    {image.width && image.height && (
                        <div className={styles.metaItem}>
                            <span className={styles.metaLabel}>Dimensiones:</span>
                            <span className={styles.metaValue}>{image.width} × {image.height}</span>
                        </div>
                    )}

                    {image.bands && (
                        <div className={styles.metaItem}>
                            <span className={styles.metaLabel}>Bandas:</span>
                            <span className={styles.metaValue}>{image.bands}</span>
                        </div>
                    )}

                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Fecha:</span>
                        <span className={styles.metaValue}>{formatDate(image.created_at)}</span>
                    </div>
                </div>
            </div>

            <div className={styles.actions}>
                <Button onClick={handleProcessSR} size="sm">
                    🔍 Procesar SR
                </Button>
                <Button onClick={() => navigate(`/analysis/${image.id}`)} size="sm" variant="secondary">
                    🌿 Análisis
                </Button>
                <Button onClick={handleDelete} variant="danger" size="sm">
                    🗑️ Eliminar
                </Button>
            </div>
        </Card>
    );
};
