import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import styles from './SearchForm.module.css';
import type { SatelliteSearchRequest } from '../../types/satellite';

interface SearchFormProps {
    onSearch: (request: SatelliteSearchRequest) => void;
    loading: boolean;
}

/** Regiones predefinidas extraídas de scripts/download_sentinel.py */
const PRESET_REGIONS = [
    { label: 'Corrientes, Argentina (arroz)', bbox: '-58.5,-30.0,-56.5,-28.0' },
    { label: 'Pampa Húmeda (soja/trigo)', bbox: '-62.0,-34.5,-59.5,-32.0' },
    { label: 'Mendoza (viñedos)', bbox: '-69.3,-33.5,-68.5,-32.9' },
    { label: 'Valle Central Chile (viñedos/frutales)', bbox: '-71.8,-36.0,-70.5,-34.5' },
    { label: 'Llanos Orientales Colombia (arroz/palma)', bbox: '-73.5,4.0,-71.0,6.0' },
    { label: 'Mato Grosso, Brasil (soja)', bbox: '-58.0,-14.0,-54.0,-11.0' },
    { label: 'São Paulo, Brasil (caña de azúcar)', bbox: '-49.0,-22.8,-47.0,-20.8' },
    { label: 'Río Grande do Sul (soja/trigo)', bbox: '-53.5,-29.0,-52.0,-27.5' },
    { label: 'Ica, Perú (espárragos/uvas)', bbox: '-76.0,-14.5,-75.0,-13.5' },
    { label: 'Valencia, España (arrozales/huerta)', bbox: '-0.5,39.1,0.1,39.5' },
];

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, loading }) => {
    const [bbox, setBbox] = useState<string>('-74.5,4.0,-73.5,5.0'); // Bogotá area
    const [startDate, setStartDate] = useState<string>('2024-01-01');
    const [endDate, setEndDate] = useState<string>('2024-01-31');
    const [cloudCover, setCloudCover] = useState<number>(20);
    const [maxResults, setMaxResults] = useState<number>(10);
    const [showRegions, setShowRegions] = useState(false);

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
                    <span className={styles.hint}>
                        Ejemplo: -74.5,4.0,-73.5,5.0 (Bogotá) —{' '}
                        <button
                            type="button"
                            className={styles.hintLink}
                            onClick={() => setShowRegions(!showRegions)}
                        >
                            {showRegions ? 'Ocultar regiones ▲' : 'Ver regiones de ejemplo ▼'}
                        </button>
                    </span>

                    {/* Preset regions panel */}
                    {showRegions && (
                        <div className={styles.regionList}>
                            {PRESET_REGIONS.map((r) => (
                                <button
                                    key={r.bbox}
                                    type="button"
                                    className={`${styles.regionBtn} ${bbox === r.bbox ? styles.regionBtnActive : ''}`}
                                    onClick={() => {
                                        setBbox(r.bbox);
                                        setShowRegions(false);
                                    }}
                                    disabled={loading}
                                >
                                    <span className={styles.regionLabel}>{r.label}</span>
                                    <span className={styles.regionCoords}>{r.bbox}</span>
                                </button>
                            ))}
                        </div>
                    )}
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
                Buscar Imágenes
            </Button>
        </form>
    );
};
