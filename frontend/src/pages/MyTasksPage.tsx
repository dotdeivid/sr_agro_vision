import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { inferenceApi } from '../api/inference';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import styles from './MyTasksPage.module.css';
import type { TaskStatusResponse } from '../types/inference';

export const MyTasksPage: React.FC = () => {
    const navigate = useNavigate();
    const [tasks, setTasks] = useState<TaskStatusResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                setLoading(true);
                const data = await inferenceApi.listTasks();
                setTasks(data);
            } catch {
                setError('Error al cargar las tareas');
            } finally {
                setLoading(false);
            }
        };
        fetchTasks();
    }, []);

    const statusBadge = (status: string) => {
        const map: Record<string, { label: string; className: string }> = {
            queued: { label: '🕐 En cola', className: styles.badgeQueued },
            processing: { label: '⚙️ Procesando', className: styles.badgeProcessing },
            completed: { label: '✅ Completada', className: styles.badgeCompleted },
            failed: { label: '❌ Error', className: styles.badgeFailed },
        };
        const info = map[status] || { label: status, className: '' };
        return <span className={`${styles.badge} ${info.className}`}>{info.label}</span>;
    };

    const grouped = {
        active: tasks.filter(t => t.status === 'queued' || t.status === 'processing'),
        completed: tasks.filter(t => t.status === 'completed'),
        failed: tasks.filter(t => t.status === 'failed'),
    };

    const renderTaskCard = (task: TaskStatusResponse) => (
        <Card key={task.task_id} className={styles.card}>
            <div className={styles.cardTop}>
                {statusBadge(task.status)}
                {task.progress > 0 && task.status === 'processing' && (
                    <span className={styles.progress}>{task.progress}%</span>
                )}
            </div>

            <div className={styles.taskId}>
                {task.task_id.slice(0, 8)}…
            </div>

            {task.status === 'processing' && (
                <div className={styles.progressBar}>
                    <div
                        className={styles.progressFill}
                        style={{ width: `${task.progress}%` }}
                    />
                </div>
            )}

            {task.error && (
                <p className={styles.errorText}>{task.error}</p>
            )}

            {/* Actions — using unified Button component */}
            {task.status === 'completed' && task.image_db_id && (
                <div className={styles.actions}>
                    <Button size="sm" onClick={() => navigate(`/process/${task.image_db_id}`)}>
                        Ver imagen
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => navigate(`/analysis/${task.image_db_id}`)}>
                        Análisis
                    </Button>
                </div>
            )}

            {task.status === 'completed' && task.result_id && (
                <div className={styles.actions}>
                    <Button size="sm" onClick={() => navigate(`/comparison/${task.result_id}`)}>
                        Ver resultado
                    </Button>
                </div>
            )}
        </Card>
    );

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div>
                    <h1 className={styles.title}>Mis Tareas</h1>
                    <p className={styles.subtitle}>
                        {loading ? 'Cargando…' : `${tasks.length} tarea${tasks.length !== 1 ? 's' : ''} en total`}
                    </p>
                </div>
            </div>

            {error && <div className={styles.error}>{error}</div>}

            {!loading && tasks.length === 0 && (
                <div className={styles.empty}>
                    <div className={styles.emptyIcon}>⚙️</div>
                    <p>No tenés tareas registradas</p>
                </div>
            )}

            {grouped.active.length > 0 && (
                <section>
                    <h2 className={styles.sectionTitle}>
                        En ejecución ({grouped.active.length})
                    </h2>
                    <div className={styles.grid}>
                        {grouped.active.map(renderTaskCard)}
                    </div>
                </section>
            )}

            {grouped.completed.length > 0 && (
                <section>
                    <h2 className={styles.sectionTitle}>
                        Finalizadas ({grouped.completed.length})
                    </h2>
                    <div className={styles.grid}>
                        {grouped.completed.map(renderTaskCard)}
                    </div>
                </section>
            )}

            {grouped.failed.length > 0 && (
                <section>
                    <h2 className={styles.sectionTitle}>
                        Con errores ({grouped.failed.length})
                    </h2>
                    <div className={styles.grid}>
                        {grouped.failed.map(renderTaskCard)}
                    </div>
                </section>
            )}
        </div>
    );
};
