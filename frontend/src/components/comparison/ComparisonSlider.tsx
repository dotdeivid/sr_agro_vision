import React from 'react';
import styles from './ComparisonSlider.module.css';

interface ComparisonSliderProps {
    value: number;
    onChange: (value: number) => void;
}

export const ComparisonSlider: React.FC<ComparisonSliderProps> = ({
    value,
    onChange
}) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onChange(Number(e.target.value));
    };

    return (
        <div className={styles.container}>
            <div className={styles.labels}>
                <span className={styles.label}>
                    Original: {value}%
                </span>
                <span className={styles.label}>
                    SR: {100 - value}%
                </span>
            </div>

            <div className={styles.sliderWrapper}>
                <input
                    type="range"
                    min="0"
                    max="100"
                    value={value}
                    onChange={handleChange}
                    className={styles.slider}
                />
                <div className={styles.track}>
                    <div
                        className={styles.fill}
                        style={{ width: `${value}%` }}
                    />
                </div>
            </div>

            <div className={styles.hint}>
                ← Arrastra para comparar →
            </div>
        </div>
    );
};
