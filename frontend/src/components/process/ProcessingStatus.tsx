import React from 'react';
import styles from './ProcessingStatus.module.css';
import type { TaskStatus } from '../../types/inference';

interface ProcessingStatusProps {
    status: TaskStatus;
    progress: number;
}

const STATUS_INFO = {
    queued: {
        label: 'En Cola',
        description: 'Esperando a ser procesado...',
        icon: '⏳',
        color: 'var(--gray-500)'
    },
    processing: {
        label: 'Procesando',
        description: 'Mejorando la resolución de la imagen...',
        icon: '🔄',
        color: 'var(--primary)'
    },
    completed: {
        label: 'Completado',
        description: '¡Procesamiento exitoso!',
        icon: '✅',
        color: 'var(--success)'
    },
    failed: {
        label: 'Error',
        description: 'Ha ocurrido un error en el procesamiento',
        icon: '❌',
        color: 'var(--danger)'
    }
};

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
    status,
    progress
}) => {
    const info = STATUS_INFO[status];

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.icon} style={{ color: info.color }}>
                    {info.icon}
                </div>
                <div className={styles.info}>
                    <h3 className={styles.label}>{info.label}</h3>
                    <p className={styles.description}>{info.description}</p>
                </div>
            </div>

            {(status === 'queued' || status === 'processing') && (
                <div className={styles.progressSection}>
                    <div className={styles.progressBar}>
                        <div
                            className={styles.progressFill}
                            style={{
                                width: `${progress}%`,
                                backgroundColor: info.color
                            }}
                        />
                    </div>
                    <div className={styles.progressText}>
                        {progress}%
                    </div>
                </div>
            )}

            {status === 'processing' && (
                <div className={styles.tips}>
                    <p className={styles.tipText}>
                        💡 Este proceso puede tomar varios minutos dependiendo del tamaño de la imagen
                    </p>
                </div>
            )}
        </div>
    );
};
