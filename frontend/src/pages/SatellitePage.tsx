import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { copernicusApi } from '../api/copernicus';
import { SearchForm } from '../components/satellite/SearchForm';
import { ImageGrid } from '../components/satellite/ImageGrid';
import { Button } from '../components/common/Button';
import { useDownloadStore } from '../store/downloadStore';
import type { DownloadTask } from '../store/downloadStore';
import styles from './SatellitePage.module.css';
import type { SatelliteImage, SatelliteSearchRequest } from '../types/satellite';

export const SatellitePage: React.FC = () => {
    const navigate = useNavigate();

    const [images, setImages] = useState<SatelliteImage[]>([]);
    const [searching, setSearching] = useState(false);
    const [downloadingId, setDownloadingId] = useState<string | null>(null);
    const [error, setError] = useState<string>('');

    // Global download store — persists across navigation
    const downloadTasks = useDownloadStore((s) => s.tasks);
    const addTask = useDownloadStore((s) => s.addTask);
    const dismissTask = useDownloadStore((s) => s.dismissTask);

    const handleSearch = async (request: SatelliteSearchRequest) => {
        try {
            setSearching(true);
            setError('');

            const response = await copernicusApi.search(request);

            setImages(response.images);

            if (response.images.length === 0) {
                setError('No se encontraron imágenes para los criterios especificados');
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al buscar imágenes');
            console.error(err);
        } finally {
            setSearching(false);
        }
    };

    const handleDownload = async (imageId: string) => {
        try {
            setDownloadingId(imageId);
            setError('');

            const response = await copernicusApi.download({
                image_id: imageId,
                project_id: 'default'
            });

            // Add to global store — polling starts automatically
            addTask(response.task_id, imageId);

        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al descargar imagen');
            console.error(err);
        } finally {
            setDownloadingId(null);
        }
    };

    const statusLabel = (t: DownloadTask) => {
        if (t.status === 'queued') return 'En cola…';
        if (t.status === 'processing') {
            if (t.progress <= 30) return `📥 Descargando ${t.progress}%`;
            if (t.progress <= 50) return `📦 Extrayendo ${t.progress}%`;
            if (t.progress <= 70) return `🔬 Procesando bandas ${t.progress}%`;
            if (t.progress <= 90) return `💾 Registrando ${t.progress}%`;
            return `🧹 Limpiando ${t.progress}%`;
        }
        if (t.status === 'completed') return '✅ Completada';
        if (t.status === 'failed') return `❌ ${t.error || 'Error'}`;
        return '';
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <h1 className={styles.title}>Búsqueda de Imágenes Satelitales</h1>
                <p className={styles.subtitle}>
                    Busca y descarga imágenes Sentinel-2 de Copernicus Data Space
                </p>
            </div>

            {/* Search Form */}
            <SearchForm onSearch={handleSearch} loading={searching} />

            {/* Error */}
            {error && (
                <div className={styles.error}>{error}</div>
            )}

            {/* Download tasks panel */}
            {downloadTasks.length > 0 && (
                <div className={styles.downloadTasks}>
                    <h3 className={styles.downloadTasksTitle}>Descargas y procesamiento</h3>
                    {downloadTasks.map(t => (
                        <div key={t.taskId} className={styles.downloadTask}>
                            <span className={styles.downloadTaskId}>
                                ID: {t.imageId.slice(0, 12)}…
                            </span>
                            <span className={styles.downloadTaskStatus}>
                                {statusLabel(t)}
                            </span>
                            {(t.status === 'processing' || t.status === 'queued') && (
                                <div className={styles.progressBar}>
                                    <div
                                        className={styles.progressFill}
                                        style={{ width: `${t.progress}%` }}
                                    />
                                </div>
                            )}
                            {t.status === 'completed' && t.imageDbId && (
                                <div className={styles.completedActions}>
                                    <Button size="sm" onClick={() => navigate(`/process/${t.imageDbId}`)}>
                                        Ver / Procesar
                                    </Button>
                                    <Button size="sm" variant="secondary" onClick={() => navigate(`/analysis/${t.imageDbId}`)}>
                                        Analizar NDVI
                                    </Button>
                                    <Button size="sm" variant="danger" onClick={() => dismissTask(t.taskId)}>
                                        ✕
                                    </Button>
                                </div>
                            )}
                            {t.status === 'failed' && (
                                <Button size="sm" variant="danger" onClick={() => dismissTask(t.taskId)}>
                                    ✕ Cerrar
                                </Button>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Results */}
            {images.length > 0 && (
                <ImageGrid
                    images={images}
                    onDownload={handleDownload}
                    downloadingId={downloadingId}
                />
            )}

            {/* Help */}
            <div className={styles.help}>
                <h3 className={styles.helpTitle}>💡 ¿Cómo usar?</h3>
                <ul className={styles.helpList}>
                    <li>Define un área de interés con el bounding box (coordenadas)</li>
                    <li>Selecciona un rango de fechas</li>
                    <li>Ajusta la cobertura de nubes máxima (recomendado: {'<'}20%)</li>
                    <li>Haz click en "Buscar" para ver resultados</li>
                    <li>Descarga las imágenes que necesites — el progreso se muestra arriba</li>
                </ul>
            </div>
        </div>
    );
};
