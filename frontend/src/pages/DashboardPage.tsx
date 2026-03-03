import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { imagesApi } from '../api/images';
import { inferenceApi } from '../api/inference';
import { useAuth } from '../hooks/useAuth';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import styles from './DashboardPage.module.css';

export const DashboardPage: React.FC = () => {
    const { user } = useAuth();
    const navigate = useNavigate();

    const [imagesCount, setImagesCount] = useState<number | null>(null);
    const [tasksCount, setTasksCount] = useState<number | null>(null);
    const [loadingStats, setLoadingStats] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                setLoadingStats(true);
                const [images, tasks] = await Promise.allSettled([
                    imagesApi.list(),
                    inferenceApi.listTasks()
                ]);
                if (images.status === 'fulfilled') setImagesCount(images.value.length);
                if (tasks.status === 'fulfilled') setTasksCount(tasks.value.length);
            } catch {
                // Stats failing is non-critical
            } finally {
                setLoadingStats(false);
            }
        };
        fetchStats();
    }, []);

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Dashboard</h1>
            <p className={styles.subtitle}>
                Bienvenido, {user?.full_name || user?.email}
            </p>

            <div className={styles.stats}>
                <Card className={styles.statCard}>
                    <div className={styles.statIcon}>📷</div>
                    <div className={styles.statValue}>
                        {loadingStats ? '—' : (imagesCount ?? 0)}
                    </div>
                    <div className={styles.statLabel}>Imágenes</div>
                </Card>

                <Card className={styles.statCard}>
                    <div className={styles.statIcon}>⚙️</div>
                    <div className={styles.statValue}>
                        {loadingStats ? '—' : (tasksCount ?? 0)}
                    </div>
                    <div className={styles.statLabel}>Tareas</div>
                </Card>
            </div>

            <div className={styles.actions}>
                <h2 className={styles.sectionTitle}>Acciones Rápidas</h2>
                <div className={styles.actionGrid}>
                    <Card className={styles.actionCard}>
                        <h3>🛰️ Descargar Sentinel-2</h3>
                        <p>Descarga imágenes satelitales de tu área de interés</p>
                        <Button onClick={() => navigate('/satellite')}>Iniciar</Button>
                    </Card>

                    <Card className={styles.actionCard}>
                        <h3>📤 Subir Imagen</h3>
                        <p>Sube tus propias imágenes GeoTIFF para procesar</p>
                        <Button onClick={() => navigate('/upload')}>Subir</Button>
                    </Card>

                    <Card className={styles.actionCard}>
                        <h3>🔍 Procesar SR</h3>
                        <p>Mejora la resolución de tus imágenes existentes</p>
                        <Button onClick={() => navigate('/upload')}>Procesar</Button>
                    </Card>
                </div>
            </div>
        </div>
    );
};
