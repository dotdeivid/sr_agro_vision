import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { Map as LeafletMap } from 'leaflet';
import { inferenceApi } from '../api/inference';
import { imagesApi } from '../api/images';
import { MapViewer } from '../components/comparison/MapViewer';
import { ComparisonSlider } from '../components/comparison/ComparisonSlider';
import { MetricsPanel } from '../components/comparison/MetricsPanel';
import { DownloadButton } from '../components/comparison/DownloadButton';
import { Button } from '../components/common/Button';
import { useSyncMaps } from '../hooks/useSyncMaps';
import { calculateBounds, calculateBoundsFromGeo, getImageUrl } from '../utils/geoUtils';
import styles from './ComparisonPage.module.css';
import type { InferenceResult } from '../types/inference';
import type { ImageMetadata } from '../types/image';


export const ComparisonPage: React.FC = () => {
    const { resultId } = useParams<{ resultId: string }>();
    const navigate = useNavigate();

    // Data state
    const [result, setResult] = useState<InferenceResult | null>(null);
    const [originalImage, setOriginalImage] = useState<ImageMetadata | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>('');

    // Maps state
    const [map1, setMap1] = useState<LeafletMap | null>(null);
    const [map2, setMap2] = useState<LeafletMap | null>(null);
    const [sliderValue, setSliderValue] = useState(50);

    // Sync maps
    useSyncMaps(map1, map2);

    // Load data
    useEffect(() => {
        if (!resultId) {
            navigate('/upload');
            return;
        }

        const loadData = async () => {
            try {
                setLoading(true);
                setError('');

                // Load result
                const resultData = await inferenceApi.getResult(resultId);
                setResult(resultData);

                // Load original image
                const imageData = await imagesApi.getById(resultData.original_image_id);
                setOriginalImage(imageData);
            } catch (err: any) {
                setError(err.response?.data?.detail || 'Error al cargar los datos');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, [resultId, navigate]);

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>Cargando comparación...</div>
            </div>
        );
    }

    if (error || !result || !originalImage) {
        return (
            <div className={styles.container}>
                <div className={styles.error}>
                    {error || 'No se pudo cargar la comparación'}
                </div>
                <Button onClick={() => navigate('/upload')}>
                    Volver a Imágenes
                </Button>
            </div>
        );
    }

    // Calculate bounds — use real geo bounds when available, fall back to pixel coords
    const geoBounds = originalImage.image_metadata?.bounds as
        [number, number, number, number] | null | undefined;
    const bounds = geoBounds
        ? calculateBoundsFromGeo(geoBounds)
        : calculateBounds(originalImage.width || 512, originalImage.height || 512);

    // Get image URLs
    const originalUrl = getImageUrl(originalImage.filepath);
    const srUrl = getImageUrl(result.result_filepath);

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <Button variant="secondary" onClick={() => navigate(-1)}>
                    ← Volver
                </Button>
                <h1 className={styles.title}>Comparación de Resultados</h1>
            </div>

            {/* Metrics Panel */}
            <MetricsPanel
                result={result}
                originalSize={originalImage.file_size}
                srSize={originalImage.file_size * result.scale_factor * result.scale_factor}
            />

            {/* Comparison Slider */}
            <ComparisonSlider
                value={sliderValue}
                onChange={setSliderValue}
            />

            {/* Maps Grid */}
            <div className={styles.mapsGrid}>
                <div
                    className={styles.mapContainer}
                    style={{
                        width: `${sliderValue}%`,
                        opacity: sliderValue > 0 ? 1 : 0
                    }}
                >
                    <MapViewer
                        imageUrl={originalUrl}
                        bounds={bounds}
                        title="Imagen Original"
                        onMapReady={setMap1}
                    />
                </div>

                <div
                    className={styles.mapContainer}
                    style={{
                        width: `${100 - sliderValue}%`,
                        opacity: (100 - sliderValue) > 0 ? 1 : 0
                    }}
                >
                    <MapViewer
                        imageUrl={srUrl}
                        bounds={bounds}
                        title={`Super-Resolución (${result.model_used.toUpperCase()} ${result.scale_factor}x)`}
                        onMapReady={setMap2}
                    />
                </div>
            </div>

            {/* Download Button */}
            <DownloadButton
                resultFilepath={result.result_filepath}
                filename={result.result_filepath.split('/').pop() || 'result.tif'}
            />

            {/* Info */}
            <div className={styles.info}>
                <p className={styles.infoText}>
                    💡 <strong>Tip:</strong> Usa la rueda del mouse para hacer zoom. Los mapas están sincronizados.
                </p>
            </div>
        </div>
    );
};
