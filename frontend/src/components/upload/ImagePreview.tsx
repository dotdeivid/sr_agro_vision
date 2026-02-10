import React from 'react';
import { Button } from '../common/Button';
import styles from './ImagePreview.module.css';

interface ImagePreviewProps {
    file: File;
    onUpload: () => void;
    onCancel: () => void;
    uploading: boolean;
    progress: number;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
    file,
    onUpload,
    onCancel,
    uploading,
    progress,
}) => {
    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    return (
        <div className={styles.container}>
            <div className={styles.preview}>
                <div className={styles.imageIcon}>🖼️</div>
                <div className={styles.info}>
                    <h3 className={styles.filename}>{file.name}</h3>
                    <p className={styles.size}>{formatFileSize(file.size)}</p>
                </div>
            </div>

            {uploading && (
                <div className={styles.progressContainer}>
                    <div className={styles.progressBar}>
                        <div
                            className={styles.progressFill}
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <p className={styles.progressText}>{progress}%</p>
                </div>
            )}

            <div className={styles.actions}>
                <Button
                    variant="secondary"
                    onClick={onCancel}
                    disabled={uploading}
                >
                    Cancelar
                </Button>
                <Button
                    onClick={onUpload}
                    loading={uploading}
                    disabled={uploading}
                >
                    {uploading ? `Subiendo... ${progress}%` : 'Subir Imagen'}
                </Button>
            </div>
        </div>
    );
};
