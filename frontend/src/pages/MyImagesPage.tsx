import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { imagesApi } from '../api/images';
import { projectsApi } from '../api/projects';
import type { Project } from '../api/projects';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { useToastStore } from '../store/toastStore';
import styles from './MyImagesPage.module.css';
import type { ImageMetadata } from '../types/image';

export const MyImagesPage: React.FC = () => {
    const navigate = useNavigate();
    const toast = useToastStore();
    const [images, setImages] = useState<ImageMetadata[]>([]);
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [imgs, projs] = await Promise.all([
                    imagesApi.list(),
                    projectsApi.list(),
                ]);
                setImages(imgs);
                setProjects(projs);
            } catch {
                setError('Error al cargar las imágenes');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return '—';
        return d.toLocaleDateString('es-ES', {
            day: '2-digit', month: 'short', year: 'numeric',
        });
    };

    const formatSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    const handleDelete = async (id: string, filename: string) => {
        if (!window.confirm(`¿Eliminar ${filename}?`)) return;
        try {
            await imagesApi.delete(id);
            setImages(prev => prev.filter(img => img.id !== id));
        } catch {
            setError('Error al eliminar la imagen');
        }
    };

    const handleMoveToProject = async (imageId: string, projectId: string) => {
        try {
            await imagesApi.moveToProject(imageId, projectId);
            setImages(prev =>
                prev.map(img => img.id === imageId ? { ...img, project_id: projectId } : img)
            );
            const proj = projects.find(p => p.id === projectId);
            toast.success(`Imagen movida a "${proj?.name || 'proyecto'}"`);
        } catch {
            toast.error('Error al mover la imagen');
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div>
                    <h1 className={styles.title}>Mis Imágenes</h1>
                    <p className={styles.subtitle}>
                        {loading ? 'Cargando…' : `${images.length} imagen${images.length !== 1 ? 'es' : ''} registrada${images.length !== 1 ? 's' : ''}`}
                    </p>
                </div>
                <Button onClick={() => navigate('/upload')} size="sm">Subir imagen</Button>
            </div>

            {error && <div className={styles.error}>{error}</div>}

            {!loading && images.length === 0 && (
                <div className={styles.empty}>
                    <div className={styles.emptyIcon}>🛰️</div>
                    <p>No tenés imágenes aún</p>
                    <Button onClick={() => navigate('/satellite')}>Buscar Imágenes</Button>
                </div>
            )}

            <div className={styles.grid}>
                {images.map(img => (
                    <Card key={img.id} className={styles.card}>
                        {/* Thumbnail */}
                        <div className={styles.thumbnail}>
                            <div className={styles.icon}>🛰️</div>
                            <div className={styles.badge}>
                                {img.num_channels ?? img.bands ?? '?'} bandas
                            </div>
                        </div>

                        {/* Info */}
                        <div className={styles.info}>
                            <h3 className={styles.filename} title={img.filename}>
                                {img.filename}
                            </h3>

                            <div className={styles.metadata}>
                                <div className={styles.metaItem}>
                                    <span className={styles.metaLabel}>Tamaño:</span>
                                    <span className={styles.metaValue}>{formatSize(img.file_size)}</span>
                                </div>
                                {img.width && img.height && (
                                    <div className={styles.metaItem}>
                                        <span className={styles.metaLabel}>Dimensiones:</span>
                                        <span className={styles.metaValue}>{img.width} × {img.height}</span>
                                    </div>
                                )}
                                <div className={styles.metaItem}>
                                    <span className={styles.metaLabel}>Fecha:</span>
                                    <span className={styles.metaValue}>
                                        {formatDate(img.uploaded_at || img.created_at)}
                                    </span>
                                </div>
                                {img.image_metadata?.crs && (
                                    <div className={styles.metaItem}>
                                        <span className={styles.metaLabel}>CRS:</span>
                                        <span className={styles.metaValue}>{img.image_metadata.crs}</span>
                                    </div>
                                )}
                            </div>

                            {/* Project selector */}
                            <div className={styles.projectSelect}>
                                <label className={styles.metaLabel}>Proyecto:</label>
                                <select
                                    value={img.project_id || ''}
                                    onChange={e => handleMoveToProject(img.id, e.target.value)}
                                    className={styles.select}
                                >
                                    {projects.map(p => (
                                        <option key={p.id} value={p.id}>
                                            {p.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className={styles.actions}>
                            <Button size="sm" onClick={() => navigate(`/process/${img.id}`)}>
                                Procesar
                            </Button>
                            <Button size="sm" variant="secondary" onClick={() => navigate(`/analysis/${img.id}`)}>
                                Análisis
                            </Button>
                            <Button size="sm" variant="danger" onClick={() => handleDelete(img.id, img.filename)}>
                                Eliminar
                            </Button>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
};
