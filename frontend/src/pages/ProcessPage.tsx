import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { imagesApi } from '../api/images';
import { inferenceApi } from '../api/inference';
import { ModelSelector } from '../components/process/ModelSelector';
import { ProcessingStatus } from '../components/process/ProcessingStatus';
import { ResultCard } from '../components/process/ResultCard';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { useToast } from '../hooks/useToast';
import styles from './ProcessPage.module.css';
import type { ImageMetadata } from '../types/image';
import type { ModelType, ScaleFactor, TaskStatus, InferenceResult } from '../types/inference';

export const ProcessPage: React.FC = () => {
    const { imageId } = useParams<{ imageId: string }>();
    const navigate = useNavigate();
    const { success, error: showError } = useToast();

    // Image state
    const [image, setImage] = useState<ImageMetadata | null>(null);
    const [loadingImage, setLoadingImage] = useState(true);

    // Processing config
    const [selectedModel, setSelectedModel] = useState<ModelType>('espcn');
    const [selectedScale, setSelectedScale] = useState<ScaleFactor>(4);

    // Processing state
    const [taskId, setTaskId] = useState<string | null>(null);
    const [status, setStatus] = useState<TaskStatus | null>(null);
    const [progress, setProgress] = useState(0);
    const [resultId, setResultId] = useState<string | null>(null);
    const [result, setResult] = useState<InferenceResult | null>(null);

    // UI state
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState<string>('');

    // Load image data
    useEffect(() => {
        if (!imageId) {
            navigate('/upload');
            return;
        }

        const loadImage = async () => {
            try {
                setLoadingImage(true);
                const imageData = await imagesApi.getById(imageId);
                setImage(imageData);
            } catch (err: any) {
                setError('Error al cargar la imagen');
                console.error(err);
            } finally {
                setLoadingImage(false);
            }
        };

        loadImage();
    }, [imageId, navigate]);

    // Start inference
    const handleStartProcessing = async () => {
        if (!imageId) return;

        try {
            setProcessing(true);
            setError('');

            const response = await inferenceApi.startInference({
                image_id: imageId,
                model: selectedModel,
                scale: selectedScale,
            });

            setTaskId(response.task_id);
            setStatus(response.status);
            setProgress(0);
            success('Procesamiento iniciado correctamente');
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || 'Error al iniciar el procesamiento';
            setError(errorMsg);
            showError(errorMsg);
        } finally {
            setProcessing(false);
        }
    };

    // Poll task status
    useEffect(() => {
        if (!taskId || status === 'completed' || status === 'failed') {
            return;
        }

        const pollInterval = setInterval(async () => {
            try {
                const statusData = await inferenceApi.getStatus(taskId);
                setStatus(statusData.status);
                setProgress(statusData.progress);

                if (statusData.status === 'completed') {
                    if (statusData.result_id) {
                        setResultId(statusData.result_id);
                    }
                    clearInterval(pollInterval);
                } else if (statusData.status === 'failed') {
                    setError(statusData.error || 'El procesamiento ha fallado');
                    clearInterval(pollInterval);
                }
            } catch (err: any) {
                console.error('Error polling status:', err);
                clearInterval(pollInterval);
            }
        }, 2000); // Poll every 2 seconds

        return () => clearInterval(pollInterval);
    }, [taskId, status]);

    // Load result when completed
    useEffect(() => {
        if (!resultId) return;

        const loadResult = async () => {
            try {
                const resultData = await inferenceApi.getResult(resultId);
                setResult(resultData);
            } catch (err: any) {
                setError('Error al cargar el resultado');
                console.error(err);
            }
        };

        loadResult();
    }, [resultId]);

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    if (loadingImage) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>Cargando imagen...</div>
            </div>
        );
    }

    if (!image) {
        return (
            <div className={styles.container}>
                <div className={styles.error}>Imagen no encontrada</div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <Button variant="secondary" onClick={() => navigate('/upload')}>
                    ← Volver
                </Button>
                <h1 className={styles.title}>Procesamiento Super-Resolución</h1>
            </div>

            {/* Image Info */}
            <Card className={styles.imageInfo}>
                <div className={styles.imageIcon}>🖼️</div>
                <div className={styles.imageDetails}>
                    <h3 className={styles.imageName}>{image.filename}</h3>
                    <div className={styles.imageMetadata}>
                        <span>{formatFileSize(image.file_size)}</span>
                        {image.width && image.height && (
                            <>
                                <span>•</span>
                                <span>{image.width} × {image.height}</span>
                            </>
                        )}
                        {image.bands && (
                            <>
                                <span>•</span>
                                <span>{image.bands} bandas</span>
                            </>
                        )}
                    </div>
                </div>
            </Card>

            {/* Model Selector */}
            {!taskId && (
                <>
                    <ModelSelector
                        selectedModel={selectedModel}
                        selectedScale={selectedScale}
                        onModelChange={setSelectedModel}
                        onScaleChange={setSelectedScale}
                        disabled={processing}
                    />

                    {error && <div className={styles.errorMessage}>{error}</div>}

                    <Button
                        onClick={handleStartProcessing}
                        loading={processing}
                        disabled={processing}
                        fullWidth
                        size="lg"
                    >
                        {processing ? 'Iniciando...' : '🚀 Iniciar Procesamiento'}
                    </Button>
                </>
            )}

            {/* Processing Status */}
            {taskId && status && status !== 'completed' && (
                <ProcessingStatus status={status} progress={progress} />
            )}

            {/* Result */}
            {result && <ResultCard result={result} />}

            {/* Failed */}
            {status === 'failed' && (
                <div className={styles.failedCard}>
                    <h3>❌ Procesamiento Fallido</h3>
                    <p>{error || 'Ha ocurrido un error desconocido'}</p>
                    <Button onClick={() => window.location.reload()} variant="secondary">
                        Intentar de Nuevo
                    </Button>
                </div>
            )}
        </div>
    );
};
