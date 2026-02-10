import React, { useState, useRef } from 'react';
import styles from './FileUploader.module.css';

interface FileUploaderProps {
    onFileSelect: (file: File) => void;
    accept?: string;
    maxSize?: number; // in bytes
}

export const FileUploader: React.FC<FileUploaderProps> = ({
    onFileSelect,
    accept = '.tif,.tiff',
    maxSize = 500 * 1024 * 1024, // 500 MB default
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string>('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const validateFile = (file: File): boolean => {
        setError('');

        // Check file extension
        const validExtensions = ['.tif', '.tiff'];
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

        if (!validExtensions.includes(extension)) {
            setError('Solo se aceptan archivos .tif o .tiff');
            return false;
        }

        // Check file size
        if (file.size > maxSize) {
            const maxSizeMB = Math.round(maxSize / (1024 * 1024));
            setError(`El archivo no debe superar ${maxSizeMB} MB`);
            return false;
        }

        return true;
    };

    const handleFile = (file: File) => {
        if (validateFile(file)) {
            onFileSelect(file);
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFile(files[0]);
        }
    };

    return (
        <div className={styles.container}>
            <div
                className={`${styles.dropzone} ${isDragging ? styles.dragging : ''} ${error ? styles.error : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={handleClick}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={accept}
                    onChange={handleFileInput}
                    className={styles.fileInput}
                />

                <div className={styles.icon}>📁</div>
                <p className={styles.text}>
                    Arrastra un archivo GeoTIFF aquí
                </p>
                <p className={styles.subtext}>
                    o haz click para seleccionar
                </p>
                <p className={styles.formats}>
                    Formatos: .tif, .tiff (máx. 500 MB)
                </p>
            </div>

            {error && (
                <div className={styles.errorMessage}>{error}</div>
            )}
        </div>
    );
};
