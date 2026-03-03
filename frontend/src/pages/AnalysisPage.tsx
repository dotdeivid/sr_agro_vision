import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { imagesApi } from '../api/images';
import { analysisApi } from '../api/analysis';
import { IndexSelector } from '../components/analysis/IndexSelector';
import { StatsPanel } from '../components/analysis/StatsPanel';
import { Button } from '../components/common/Button';
import { getImageUrl } from '../utils/geoUtils';
import styles from './AnalysisPage.module.css';
import type { ImageMetadata } from '../types/image';
import type { IndexType, AnalysisResult } from '../types/analysis';

export const AnalysisPage: React.FC = () => {
    const { imageId } = useParams<{ imageId: string }>();
    const navigate = useNavigate();

    const [image, setImage] = useState<ImageMetadata | null>(null);
    const [selectedIndex, setSelectedIndex] = useState<IndexType>('ndvi');
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string>('');

    useEffect(() => {
        if (!imageId) {
            navigate('/upload');
            return;
        }

        const loadImage = async () => {
            try {
                const imageData = await imagesApi.getById(imageId);
                setImage(imageData);
            } catch (err: any) {
                setError('Error al cargar la imagen');
            } finally {
                setLoading(false);
            }
        };

        loadImage();
    }, [imageId, navigate]);

    const handleAnalyze = async () => {
        if (!imageId) return;

        try {
            setAnalyzing(true);
            setError('');
            setResult(null);

            const analysisResult = await analysisApi.analyze({
                image_id: imageId,
                index_type: selectedIndex
            });

            setResult(analysisResult);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al analizar imagen');
        } finally {
            setAnalyzing(false);
        }
    };

    if (loading) {
        return <div className={styles.loading}>Cargando...</div>;
    }

    if (!image) {
        return <div className={styles.error}>Imagen no encontrada</div>;
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <Button variant="secondary" onClick={() => navigate(-1)}>← Volver</Button>
                <h1 className={styles.title}>Análisis de Vegetación</h1>
            </div>

            <div className={styles.imageInfo}>
                <h3>{image.filename}</h3>
                <p>{image.width} × {image.height} px</p>
            </div>

            <IndexSelector
                selectedIndex={selectedIndex}
                onIndexChange={setSelectedIndex}
                disabled={analyzing}
            />

            {error && <div className={styles.errorMsg}>{error}</div>}

            <Button onClick={handleAnalyze} loading={analyzing} disabled={analyzing} fullWidth size="lg">
                {analyzing ? 'Analizando...' : '🌿 Analizar Vegetación'}
            </Button>

            {result && (
                <>
                    <div className={styles.resultImage}>
                        {/* getImageUrl converts the server filepath to /api/v1/images/view/{filename} */}
                        <img src={getImageUrl(result.colormap_filepath)} alt={`${result.index_type.toUpperCase()} Map`} />
                    </div>
                    <StatsPanel stats={result.stats} indexType={result.index_type} />
                </>
            )}
        </div>
    );
};
