import React, { useState } from 'react';
import { FileUploader } from '../components/upload/FileUploader';
import { ImagePreview } from '../components/upload/ImagePreview';
import { ImageList } from '../components/upload/ImageList';
import { imagesApi } from '../api/images';
import { useToast } from '../hooks/useToast';
import styles from './UploadPage.module.css';

export const UploadPage: React.FC = () => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string>('');
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    // Batch upload preparation (for future implementation)
    const [selectedFiles] = useState<File[]>([]);
    const [batchMode] = useState(false);
    const { success, error: showError } = useToast();

    const handleFileSelect = (file: File) => {
        setSelectedFile(file);
        setError('');
        setProgress(0);
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        try {
            setUploading(true);
            setError('');

            await imagesApi.upload(selectedFile, 'default', (percent) => {
                setProgress(percent);
            });

            // Success!
            success(`Imagen "${selectedFile.name}" subida correctamente`);
            setSelectedFile(null);
            setProgress(0);
            setRefreshTrigger(prev => prev + 1); // Trigger image list refresh

        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || 'Error al subir la imagen';
            setError(errorMsg);
            showError(errorMsg);
        } finally {
            setUploading(false);
        }
    };

    const handleCancel = () => {
        setSelectedFile(null);
        setProgress(0);
        setError('');
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1 className={styles.title}>Subir Imagen GeoTIFF</h1>
                <p className={styles.subtitle}>
                    Sube tus imágenes satelitales para procesarlas con Super-Resolución
                </p>
            </div>

            <div className={styles.uploadSection}>
                {!selectedFile ? (
                    <FileUploader onFileSelect={handleFileSelect} />
                ) : (
                    <ImagePreview
                        file={selectedFile}
                        onUpload={handleUpload}
                        onCancel={handleCancel}
                        uploading={uploading}
                        progress={progress}
                    />
                )}

                {error && (
                    <div className={styles.error}>{error}</div>
                )}
            </div>

            <div className={styles.separator} />

            <ImageList refreshTrigger={refreshTrigger} />
        </div>
    );
};
