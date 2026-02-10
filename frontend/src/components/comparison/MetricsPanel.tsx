import React from 'react';
import styles from './MetricsPanel.module.css';
import type { InferenceResult } from '../../types/inference';

interface MetricsPanelProps {
    result: InferenceResult;
    originalSize: number;
    srSize: number;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({
    result,
    originalSize,
    srSize
}) => {
    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    const formatTime = (seconds: number | null): string => {
        if (!seconds) return 'N/A';
        if (seconds < 60) return `${Math.round(seconds)}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        return `${minutes}m ${remainingSeconds}s`;
    };

    const getPSNRQuality = (psnr: number | null): string => {
        if (!psnr) return 'unknown';
        if (psnr >= 40) return 'excellent';
        if (psnr >= 35) return 'good';
        if (psnr >= 30) return 'fair';
        return 'poor';
    };

    const getSSIMQuality = (ssim: number | null): string => {
        if (!ssim) return 'unknown';
        if (ssim >= 0.95) return 'excellent';
        if (ssim >= 0.90) return 'good';
        if (ssim >= 0.85) return 'fair';
        return 'poor';
    };

    return (
        <div className={styles.container}>
            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Métricas de Calidad</h3>
                <div className={styles.metricsGrid}>
                    <div className={`${styles.metric} ${styles[getPSNRQuality(result.psnr)]}`}>
                        <div className={styles.metricIcon}>📊</div>
                        <div className={styles.metricValue}>
                            {result.psnr ? result.psnr.toFixed(2) : 'N/A'}
                            <span className={styles.metricUnit}>dB</span>
                        </div>
                        <div className={styles.metricLabel}>PSNR</div>
                    </div>

                    <div className={`${styles.metric} ${styles[getSSIMQuality(result.ssim)]}`}>
                        <div className={styles.metricIcon}>🎯</div>
                        <div className={styles.metricValue}>
                            {result.ssim ? result.ssim.toFixed(4) : 'N/A'}
                        </div>
                        <div className={styles.metricLabel}>SSIM</div>
                    </div>
                </div>
            </div>

            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Información</h3>
                <div className={styles.infoGrid}>
                    <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Modelo:</span>
                        <span className={styles.infoValue}>{result.model_used.toUpperCase()}</span>
                    </div>
                    <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Escala:</span>
                        <span className={styles.infoValue}>{result.scale_factor}x</span>
                    </div>
                    <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Tiempo:</span>
                        <span className={styles.infoValue}>{formatTime(result.processing_time)}</span>
                    </div>
                    <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Tamaño Original:</span>
                        <span className={styles.infoValue}>{formatFileSize(originalSize)}</span>
                    </div>
                    <div className={styles.infoItem}>
                        <span className={styles.infoLabel}>Tamaño SR:</span>
                        <span className={styles.infoValue}>{formatFileSize(srSize)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
