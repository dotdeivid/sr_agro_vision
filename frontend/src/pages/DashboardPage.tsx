import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import styles from './DashboardPage.module.css';

export const DashboardPage: React.FC = () => {
    const { user } = useAuth();

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Dashboard</h1>
            <p className={styles.subtitle}>
                Bienvenido, {user?.full_name || user?.email}
            </p>

            <div className={styles.stats}>
                <Card className={styles.statCard}>
                    <div className={styles.statIcon}>📊</div>
                    <div className={styles.statValue}>5</div>
                    <div className={styles.statLabel}>Proyectos</div>
                </Card>

                <Card className={styles.statCard}>
                    <div className={styles.statIcon}>📷</div>
                    <div className={styles.statValue}>23</div>
                    <div className={styles.statLabel}>Imágenes</div>
                </Card>

                <Card className={styles.statCard}>
                    <div className={styles.statIcon}>🌾</div>
                    <div className={styles.statValue}>156</div>
                    <div className={styles.statLabel}>Hectáreas</div>
                </Card>
            </div>

            <div className={styles.actions}>
                <h2 className={styles.sectionTitle}>Acciones Rápidas</h2>
                <div className={styles.actionGrid}>
                    <Card className={styles.actionCard}>
                        <h3>🛰️ Descargar Sentinel-2</h3>
                        <p>Descarga imágenes satelitales de tu área de interés</p>
                        <Button>Iniciar</Button>
                    </Card>

                    <Card className={styles.actionCard}>
                        <h3>📤 Subir Imagen</h3>
                        <p>Sube tus propias imágenes GeoTIFF para procesar</p>
                        <Button>Subir</Button>
                    </Card>

                    <Card className={styles.actionCard}>
                        <h3>🔍 Procesar SR</h3>
                        <p>Mejora la resolución de tus imágenes existentes</p>
                        <Button>Procesar</Button>
                    </Card>
                </div>
            </div>
        </div>
    );
};
