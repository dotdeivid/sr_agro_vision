import React from 'react';
import styles from './IndexSelector.module.css';
import type { IndexType } from '../../types/analysis';

interface IndexSelectorProps {
    selectedIndex: IndexType;
    onIndexChange: (index: IndexType) => void;
    disabled?: boolean;
}

const INDICES = [
    {
        id: 'ndvi' as IndexType,
        name: 'NDVI',
        description: 'Normalized Difference Vegetation Index',
        formula: '(NIR - Red) / (NIR + Red)',
        range: '-1 a 1'
    },
    {
        id: 'evi' as IndexType,
        name: 'EVI',
        description: 'Enhanced Vegetation Index',
        formula: '2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))',
        range: '-1 a 1'
    },
    {
        id: 'savi' as IndexType,
        name: 'SAVI',
        description: 'Soil Adjusted Vegetation Index',
        formula: '((NIR - Red) / (NIR + Red + 0.5)) * 1.5',
        range: '-1 a 1'
    },
    {
        id: 'ndwi' as IndexType,
        name: 'NDWI',
        description: 'Normalized Difference Water Index',
        formula: '(Green - NIR) / (Green + NIR)',
        range: '-1 a 1'
    }
];

export const IndexSelector: React.FC<IndexSelectorProps> = ({
    selectedIndex,
    onIndexChange,
    disabled = false
}) => {
    return (
        <div className={styles.container}>
            <h3 className={styles.title}>Seleccionar Índice</h3>

            <div className={styles.grid}>
                {INDICES.map((index) => (
                    <label
                        key={index.id}
                        className={`${styles.card} ${selectedIndex === index.id ? styles.selected : ''
                            } ${disabled ? styles.disabled : ''}`}
                    >
                        <input
                            type="radio"
                            name="index"
                            value={index.id}
                            checked={selectedIndex === index.id}
                            onChange={() => onIndexChange(index.id)}
                            disabled={disabled}
                            className={styles.radio}
                        />

                        <div className={styles.indexName}>{index.name}</div>
                        <div className={styles.indexDesc}>{index.description}</div>
                        <div className={styles.indexFormula}>{index.formula}</div>
                        <div className={styles.indexRange}>Rango: {index.range}</div>
                    </label>
                ))}
            </div>
        </div>
    );
};
