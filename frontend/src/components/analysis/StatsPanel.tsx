import React from 'react';
import styles from './StatsPanel.module.css';
import type { AnalysisStats } from '../../types/analysis';

interface StatsPanelProps {
    stats: AnalysisStats;
    indexType: string;
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ stats, indexType }) => {
    const getHealthColor = (key: string): string => {
        const colors: Record<string, string> = {
            very_dense: '#059669',
            dense: '#10b981',
            moderate: '#fbbf24',
            sparse: '#f59e0b',
            bare_soil: '#8b5cf6',
            water: '#3b82f6'
        };
        return colors[key] || '#6b7280';
    };

    const totalPixels = Object.values(stats.health_distribution).reduce((a, b) => a + b, 0);

    return (
        <div className={styles.container}>
            <div className={styles.section}>
                <h3 className={styles.title}>Estadísticas {indexType.toUpperCase()}</h3>
                <div className={styles.statsGrid}>
                    <div className={styles.stat}>
                        <span className={styles.statLabel}>Mínimo:</span>
                        <span className={styles.statValue}>{stats.min_value.toFixed(3)}</span>
                    </div>
                    <div className={styles.stat}>
                        <span className={styles.statLabel}>Máximo:</span>
                        <span className={styles.statValue}>{stats.max_value.toFixed(3)}</span>
                    </div>
                    <div className={styles.stat}>
                        <span className={styles.statLabel}>Promedio:</span>
                        <span className={styles.statValue}>{stats.mean_value.toFixed(3)}</span>
                    </div>
                    <div className={styles.stat}>
                        <span className={styles.statLabel}>Desv. Est.:</span>
                        <span className={styles.statValue}>{stats.std_dev.toFixed(3)}</span>
                    </div>
                </div>
            </div>

            <div className={styles.section}>
                <h3 className={styles.title}>Distribución de Salud</h3>
                <div className={styles.distribution}>
                    {Object.entries(stats.health_distribution).map(([key, value]) => {
                        const percentage = totalPixels > 0 ? (value / totalPixels) * 100 : 0;
                        return (
                            <div key={key} className={styles.distItem}>
                                <div className={styles.distLabel}>
                                    <span className={styles.distDot} style={{ backgroundColor: getHealthColor(key) }} />
                                    {key.replace('_', ' ')}
                                </div>
                                <div className={styles.distBar}>
                                    <div className={styles.distFill} style={{ width: `${percentage}%`, backgroundColor: getHealthColor(key) }} />
                                </div>
                                <div className={styles.distValue}>{percentage.toFixed(1)}%</div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};
