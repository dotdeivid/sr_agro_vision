import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../common/Button';
import { exportApi } from '../../api/export';
import styles from './ResultCard.module.css';
import type { InferenceResult } from '../../types/inference';
import type { ExportFormat } from '../../types/export';

interface ResultCardProps {
    result: InferenceResult;
}

export const ResultCard: React.FC<ResultCardProps> = ({ result }) => {
    const navigate = useNavigate();
    const [exporting, setExporting] = useState(false);
    const [exportFormat, setExportFormat] = useState<ExportFormat | null>(null);

    const formatDate = (dateString: string): string => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatProcessingTime = (seconds: number | null): string => {
        if (!seconds) return 'N/A';
        if (seconds < 60) return `${Math.round(seconds)}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        return `${minutes}m ${remainingSeconds}s`;
    };

    const handleExport = async (format: ExportFormat) => {
        try {
            setExporting(true);
            setExportFormat(format);

            const response = await exportApi.export({
                result_id: result.id,
                format,
                quality: 95
            });

            // Download file
            window.open(exportApi.download(response.filename), '_blank');

            alert(`Exportación completada: ${response.filename}`);
        } catch (error) {
            console.error('Export error:', error);
            alert('Error al exportar');
        } finally {
            setExporting(false);
            setExportFormat(null);
        }
    };

    const handleViewComparison = () => {
        navigate(`/comparison/${result.id}`);
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.icon}>✨</div>
                <h2 className={styles.title}>Resultado del Procesamiento</h2>
            </div>

            {/* Metrics */}
            <div className={styles.metrics}>
                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>PSNR</div>
                    <div className={styles.metricValue}>
                        {result.psnr ? result.psnr.toFixed(2) : 'N/A'}
                        <span className={styles.metricUnit}>dB</span>
                    </div>
                    <div className={styles.metricDesc}>Peak Signal-to-Noise Ratio</div>
                </div>

                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>SSIM</div>
                    <div className={styles.metricValue}>
                        {result.ssim ? result.ssim.toFixed(4) : 'N/A'}
                    </div>
                    <div className={styles.metricDesc}>Structural Similarity Index</div>
                </div>

                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>Modelo</div>
                    <div className={styles.metricValue}>{result.model_used.toUpperCase()}</div>
                    <div className={styles.metricDesc}>Factor: {result.scale_factor}x</div>
                </div>

                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>Tiempo</div>
                    <div className={styles.metricValue}>
                        {formatProcessingTime(result.processing_time)}
                    </div>
                    <div className={styles.metricDesc}>Procesamiento</div>
                </div>
            </div>

            {/* Info */}
            <div className={styles.info}>
                <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Fecha:</span>
                    <span className={styles.infoValue}>{formatDate(result.created_at)}</span>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Archivo:</span>
                    <span className={styles.infoValue}>
                        {result.result_filepath.split('/').pop()}
                    </span>
                </div>
            </div>

            {/* Actions */}
            <div className={styles.actions}>
                <Button onClick={handleViewComparison} variant="secondary">
                    👁️ Ver Comparación
                </Button>
            </div>

            {/* Export buttons */}
            <div className={styles.exportSection}>
                <h4 className={styles.exportTitle}>Exportar resultado:</h4>
                <div className={styles.exportButtons}>
                    <Button
                        onClick={() => handleExport('png')}
                        size="sm"
                        variant="secondary"
                        disabled={exporting}
                    >
                        {exportFormat === 'png' ? '⏳' : '📸'} PNG
                    </Button>
                    <Button
                        onClick={() => handleExport('jpeg')}
                        size="sm"
                        variant="secondary"
                        disabled={exporting}
                    >
                        {exportFormat === 'jpeg' ? '⏳' : '🖼️'} JPEG
                    </Button>
                    <Button
                        onClick={() => handleExport('geotiff')}
                        size="sm"
                        variant="secondary"
                        disabled={exporting}
                    >
                        {exportFormat === 'geotiff' ? '⏳' : '🗺️'} GeoTIFF
                    </Button>
                </div>
            </div>
        </div>
    );
};
