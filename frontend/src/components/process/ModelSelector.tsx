import React from 'react';
import styles from './ModelSelector.module.css';
import type { ModelType, ScaleFactor } from '../../types/inference';

interface ModelSelectorProps {
    selectedModel: ModelType;
    selectedScale: ScaleFactor;
    onModelChange: (model: ModelType) => void;
    onScaleChange: (scale: ScaleFactor) => void;
    disabled?: boolean;
}

const MODELS = [
    {
        id: 'espcn' as ModelType,
        name: 'ESPCN',
        description: 'Efficient Sub-Pixel CNN - Rápido y eficiente',
        icon: '⚡'
    },
    {
        id: 'swinir' as ModelType,
        name: 'SwinIR',
        description: 'Swin Transformer - Alta calidad',
        icon: '🌟'
    },
    {
        id: 'gan' as ModelType,
        name: 'GAN',
        description: 'Generative Adversarial Network - Realismo',
        icon: '🎨'
    }
];

const SCALES = [
    { value: 2 as ScaleFactor, label: '2x' },
    { value: 4 as ScaleFactor, label: '4x' }
];

export const ModelSelector: React.FC<ModelSelectorProps> = ({
    selectedModel,
    selectedScale,
    onModelChange,
    onScaleChange,
    disabled = false
}) => {
    return (
        <div className={styles.container}>
            {/* Model Selection */}
            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Seleccionar Modelo</h3>
                <div className={styles.modelGrid}>
                    {MODELS.map((model) => (
                        <label
                            key={model.id}
                            className={`${styles.modelCard} ${selectedModel === model.id ? styles.selected : ''
                                } ${disabled ? styles.disabled : ''}`}
                        >
                            <input
                                type="radio"
                                name="model"
                                value={model.id}
                                checked={selectedModel === model.id}
                                onChange={() => onModelChange(model.id)}
                                disabled={disabled}
                                className={styles.radio}
                            />
                            <div className={styles.modelIcon}>{model.icon}</div>
                            <div className={styles.modelName}>{model.name}</div>
                            <div className={styles.modelDesc}>{model.description}</div>
                        </label>
                    ))}
                </div>
            </div>

            {/* Scale Selection */}
            <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Factor de Escala</h3>
                <div className={styles.scaleButtons}>
                    {SCALES.map((scale) => (
                        <button
                            key={scale.value}
                            type="button"
                            className={`${styles.scaleButton} ${selectedScale === scale.value ? styles.active : ''
                                }`}
                            onClick={() => onScaleChange(scale.value)}
                            disabled={disabled}
                        >
                            {scale.label}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};
