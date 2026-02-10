import React, { useEffect, useState } from 'react';
import { imagesApi } from '../../api/images';
import { ImageCard } from './ImageCard';
import styles from './ImageList.module.css';
import type { ImageMetadata } from '../../types/image';

interface ImageListProps {
    refreshTrigger?: number;
}

export const ImageList: React.FC<ImageListProps> = ({ refreshTrigger = 0 }) => {
    const [images, setImages] = useState<ImageMetadata[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>('');

    const fetchImages = async () => {
        try {
            setLoading(true);
            setError('');
            const data = await imagesApi.list();
            setImages(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al cargar las imágenes');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchImages();
    }, [refreshTrigger]);

    const handleDelete = async (id: string) => {
        try {
            await imagesApi.delete(id);
            setImages(images.filter(img => img.id !== id));
        } catch (err: any) {
            alert('Error al eliminar la imagen');
        }
    };

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>Cargando imágenes...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.container}>
                <div className={styles.error}>{error}</div>
            </div>
        );
    }

    if (images.length === 0) {
        return (
            <div className={styles.container}>
                <div className={styles.empty}>
                    <div className={styles.emptyIcon}>📷</div>
                    <p>No hay imágenes todavía</p>
                    <p className={styles.emptyHint}>Sube tu primera imagen GeoTIFF arriba</p>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <h2 className={styles.title}>
                Imágenes Subidas ({images.length})
            </h2>

            <div className={styles.grid}>
                {images.map((image) => (
                    <ImageCard
                        key={image.id}
                        image={image}
                        onDelete={handleDelete}
                    />
                ))}
            </div>
        </div>
    );
};
