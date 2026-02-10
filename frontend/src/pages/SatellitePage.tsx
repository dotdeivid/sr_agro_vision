import React, { useState } from 'react';
import { copernicusApi } from '../api/copernicus';
import { SearchForm } from '../components/satellite/SearchForm';
import { ImageGrid } from '../components/satellite/ImageGrid';
import styles from './SatellitePage.module.css';
import type { SatelliteImage, SatelliteSearchRequest } from '../types/satellite';

export const SatellitePage: React.FC = () => {

    const [images, setImages] = useState<SatelliteImage[]>([]);
    const [totalResults, setTotalResults] = useState<number>(0);
    const [searching, setSearching] = useState(false);
    const [downloadingId, setDownloadingId] = useState<string | null>(null);
    const [error, setError] = useState<string>('');

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

            alert(`Download iniciado: ${response.message}\nTask ID: ${response.task_id}`);

            // TODO: Implementar seguimiento de tarea de descarga
            // Similar al polling de ProcessPage

        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al descargar imagen');
            console.error(err);
        } finally {
            setDownloadingId(null);
        }
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
                    <li>Descarga las imágenes que necesites</li>
                </ul>
            </div>
        </div>
    );
};
