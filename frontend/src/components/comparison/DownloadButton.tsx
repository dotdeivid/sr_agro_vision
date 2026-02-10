import React, { useState } from 'react';
import { Button } from '../common/Button';
import styles from './DownloadButton.module.css';

interface DownloadButtonProps {
    resultFilepath: string;
    filename: string;
}

export const DownloadButton: React.FC<DownloadButtonProps> = ({
    resultFilepath,
    filename
}) => {
    const [downloading, setDownloading] = useState(false);

    const handleDownload = async () => {
        try {
            setDownloading(true);

            // TODO: Implement actual download from backend
            // For now, just show alert
            const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const downloadUrl = `${baseUrl}/api/v1/images/download/${resultFilepath.split('/').pop()}`;

            // Open in new tab (browser will handle download)
            window.open(downloadUrl, '_blank');

        } catch (error) {
            console.error('Download error:', error);
            alert('Error al descargar el archivo');
        } finally {
            setDownloading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Button
                onClick={handleDownload}
                loading={downloading}
                disabled={downloading}
                size="lg"
            >
                📥 Descargar Resultado
            </Button>
            <p className={styles.filename}>{filename}</p>
        </div>
    );
};
