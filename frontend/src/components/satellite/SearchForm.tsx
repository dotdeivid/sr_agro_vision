import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import styles from './SearchForm.module.css';
import type { SatelliteSearchRequest } from '../../types/satellite';

interface SearchFormProps {
    onSearch: (request: SatelliteSearchRequest) => void;
    loading: boolean;
}

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, loading }) => {
    const [bbox, setBbox] = useState<string>('-74.5,4.0,-73.5,5.0'); // Bogotá area
    const [startDate, setStartDate] = useState<string>('2024-01-01');
    const [endDate, setEndDate] = useState<string>('2024-01-31');
    const [cloudCover, setCloudCover] = useState<number>(20);
    const [maxResults, setMaxResults] = useState<number>(10);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Parse bbox
        const bboxArray = bbox.split(',').map(Number);
        if (bboxArray.length !== 4) {
            alert('Bbox debe tener 4 valores: lon_min,lat_min,lon_max,lat_max');
            return;
        }

        const request: SatelliteSearchRequest = {
            bbox: bboxArray as [number, number, number, number],
            start_date: startDate,
            end_date: endDate,
            max_cloud_cover: cloudCover,
            max_results: maxResults,
        };

        onSearch(request);
    };

    return (
        <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.row}>
                <div className={styles.field}>
                    <label className={styles.label}>Bounding Box</label>
                    <Input
                        type="text"
                        value={bbox}
                        onChange={(e) => setBbox(e.target.value)}
                        placeholder="lon_min,lat_min,lon_max,lat_max"
                        disabled={loading}
                    />
                    <span className={styles.hint}>Ejemplo: -74.5,4.0,-73.5,5.0 (Bogotá)</span>
                </div>
            </div>

            <div className={styles.row}>
                <div className={styles.field}>
                    <label className={styles.label}>Fecha Inicio</label>
                    <Input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        disabled={loading}
                    />
                </div>

                <div className={styles.field}>
                    <label className={styles.label}>Fecha Fin</label>
                    <Input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        disabled={loading}
                    />
                </div>
            </div>

            <div className={styles.row}>
                <div className={styles.field}>
                    <label className={styles.label}>
                        Cobertura de Nubes Máxima: {cloudCover}%
                    </label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={cloudCover}
                        onChange={(e) => setCloudCover(Number(e.target.value))}
                        className={styles.slider}
                        disabled={loading}
                    />
                </div>

                <div className={styles.field}>
                    <label className={styles.label}>Máximo Resultados</label>
                    <Input
                        type="number"
                        min="1"
                        max="100"
                        value={maxResults}
                        onChange={(e) => setMaxResults(Number(e.target.value))}
                        disabled={loading}
                    />
                </div>
            </div>

            <Button type="submit" loading={loading} disabled={loading} fullWidth>
                🛰️ Buscar Imágenes Sentinel-2
            </Button>
        </form>
    );
};
