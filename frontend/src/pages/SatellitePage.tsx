import React, { useState, useEffect, useRef } from 'react';
import { copernicusApi } from '../api/copernicus';
import { inferenceApi } from '../api/inference';
import { SearchForm } from '../components/satellite/SearchForm';
import { ImageGrid } from '../components/satellite/ImageGrid';
import styles from './SatellitePage.module.css';
import type { SatelliteImage, SatelliteSearchRequest } from '../types/satellite';

interface DownloadTask {
    taskId: string;
    imageId: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    progress: number;
    error?: string;
}

export const SatellitePage: React.FC = () => {

    const [images, setImages] = useState<SatelliteImage[]>([]);
    const [totalResults, setTotalResults] = useState<number>(0);
    const [searching, setSearching] = useState(false);
    const [downloadingId, setDownloadingId] = useState<string | null>(null);
    const [error, setError] = useState<string>('');
    const [downloadTasks, setDownloadTasks] = useState<DownloadTask[]>([]);
    const pollRefs = useRef<Record<string, ReturnType<typeof setInterval>>>({});

    // Clean up polling on unmount
    useEffect(() => {
        return () => {
            Object.values(pollRefs.current).forEach(clearInterval);
        };
    }, []);

    const startPolling = (task: DownloadTask) => {
        const interval = setInterval(async () => {
            try {
                const statusData = await inferenceApi.getStatus(task.taskId);
                setDownloadTasks(prev =>
                    prev.map(t =>
                        t.taskId === task.taskId
                            ? {
                                ...t,
                                status: statusData.status as DownloadTask['status'],
                                progress: statusData.progress,
                                error: statusData.error
                            }
                            : t
                    )
                );

                if (statusData.status === 'completed' || statusData.status === 'failed') {
                    clearInterval(interval);
                    delete pollRefs.current[task.taskId];
                }
            } catch {
                clearInterval(interval);
                delete pollRefs.current[task.taskId];
            }
        }, 3000);

        pollRefs.current[task.taskId] = interval;
    };

    const handleSearch = async (request: SatelliteSearchRequest) => {
        try {
            setSearching(true);
            setError('');

            const response = await copernicusApi.search(request);

            setImages(response.images);
            setTotalResults(response.total_results);

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

            const newTask: DownloadTask = {
                taskId: response.task_id,
                imageId,
                status: 'queued',
                progress: 0
            };

            setDownloadTasks(prev => [...prev, newTask]);
            startPolling(newTask);

        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al descargar imagen');
            console.error(err);
        } finally {
            setDownloadingId(null);
        }
    };

    const statusLabel = (t: DownloadTask) => {
        if (t.status === 'queued') return '🕐 En cola…';
        if (t.status === 'processing') return `⚙️ Descargando… ${t.progress}%`;
        if (t.status === 'completed') return '✅ Descarga completada';
        if (t.status === 'failed') return `❌ Error: ${t.error || 'Descarga fallida'}`;
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
                    <h3 className={styles.downloadTasksTitle}>🛰️ Descargas en curso</h3>
                    {downloadTasks.map(t => (
                        <div key={t.taskId} className={styles.downloadTask}>
                            <span className={styles.downloadTaskId}>
                                ID: {t.imageId.slice(0, 12)}…
                            </span>
                            <span className={styles.downloadTaskStatus}>
                                {statusLabel(t)}
                            </span>
                            {t.status === 'processing' && (
                                <div className={styles.progressBar}>
                                    <div
                                        className={styles.progressFill}
                                        style={{ width: `${t.progress}%` }}
                                    />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Info */}
            {totalResults > 0 && (
                <div className={styles.info}>
                    <p className={styles.infoText}>
                        📊 Se encontraron {totalResults} imágenes en total. Mostrando las primeras {images.length}.
                    </p>
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
