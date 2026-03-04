import React, { useState } from 'react';
import { Button } from '../common/Button';
import { apiClient } from '../../api/client';
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
    const [error, setError] = useState<string>('');

    const handleDownload = async () => {
        try {
            setDownloading(true);
            setError('');

            const dlFilename = resultFilepath.split('/').pop() || filename;

            // Fetch as blob so the browser triggers a real file download
            const response = await apiClient.get(
                `/api/v1/images/download/${dlFilename}`,
                { responseType: 'blob' }
            );

            const url = URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

        } catch (err: any) {
            console.error('Download error:', err);
            setError('Error al descargar el archivo');
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
                Descargar Resultado
            </Button>
            <p className={styles.filename}>{filename}</p>
            {error && <p className={styles.error}>{error}</p>}
        </div>
    );
};
