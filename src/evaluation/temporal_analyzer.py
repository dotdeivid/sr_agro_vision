"""
Análisis temporal de imágenes satelitales
Evalúa consistencia SR a través del tiempo
"""
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict
import pandas as pd


class TemporalAnalyzer:
    """
    Analiza series temporales de imágenes satelitales
    """
    
    def __init__(self):
        self.temporal_data = []
    
    def add_observation(self, date, sr_img, hr_img, metadata=None):
        """
        Agrega observación temporal
        
        Args:
            date: datetime o string 'YYYY-MM-DD'
            sr_img: Imagen SR [C, H, W]
            hr_img: Imagen HR  [C, H, W]
            metadata: Dict con metadata adicional
        """
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%D')
        
        self.temporal_data.append({
            'date': date,
            'sr_img': sr_img,
            'hr_img': hr_img,
            'metadata': metadata or {}
        })
    
    def calculate_ndvi_timeseries(self):
        """
        Calcula NDVI promedio para cada fecha
        
        Returns:
            DataFrame con series temporales
        """
        dates = []
        ndvi_sr = []
        ndvi_hr = []
        
        for obs in self.temporal_data:
            sr_img = obs['sr_img']
            hr_img = obs['hr_img']
            
            # Calcular NDVI
            ndvi_sr_val = self._calc_mean_ndvi(sr_img)
            ndvi_hr_val = self._calc_mean_ndvi(hr_img)
            
            dates.append(obs['date'])
            ndvi_sr.append(ndvi_sr_val)
            ndvi_hr.append(ndvi_hr_val)
        
        df = pd.DataFrame({
            'date': dates,
            'NDVI_SR': ndvi_sr,
            'NDVI_HR': ndvi_hr,
            'NDVI_diff': np.array(ndvi_sr) - np.array(ndvi_hr)
        })
        
        df = df.sort_values('date')
        
        return df
    
    def _calc_mean_ndvi(self, img):
        """Calcula NDVI promedio de imagen"""
        red = img[0]
        nir = img[3]
        
        denominator = nir + red
        denominator = np.where(denominator == 0, 1e-8, denominator)
        ndvi = (nir - red) / denominator
        
        # Promedio excluyendo valores inválidos
        valid_mask = np.isfinite(ndvi)
        return np.mean(ndvi[valid_mask])
    
    def detect_changes(self, threshold=0.1):
        """
        Detecta cambios significativos entre fechas
        
        Args:
            threshold: Umbral de cambio en NDVI
        
        Returns:
            Lista de eventos de cambio
        """
        df = self.calculate_ndvi_timeseries()
        
        changes = []
        
        for i in range(1, len(df)):
            prev_ndvi = df.iloc[i-1]['NDVI_HR']
            curr_ndvi = df.iloc[i]['NDVI_HR']
            change = curr_ndvi - prev_ndvi
            
            if abs(change) > threshold:
                changes.append({
                    'date_from': df.iloc[i-1]['date'],
                    'date_to': df.iloc[i]['date'],
                    'ndvi_change': change,
                    'change_type': 'increase' if change > 0 else 'decrease'
                })
        
        return changes
    
    def calculate_temporal_consistency(self):
        """
        Calcula consistencia temporal SR vs HR
        
        Returns:
            Dict con métricas de consistencia
        """
        df = self.calculate_ndvi_timeseries()
        
        # Correlación temporal
        corr = df['NDVI_SR'].corr(df['NDVI_HR'])
        
        # Error promedio a través del tiempo
        mae_temporal = df['NDVI_diff'].abs().mean()
        rmse_temporal = np.sqrt((df['NDVI_diff'] ** 2).mean())
        
        # Tendencia
        from scipy.stats import linregress
        
        x = np.arange(len(df))
        slope_sr, _, _, _, _ = linregress(x, df['NDVI_SR'])
        slope_hr, _, _, _, _ = linregress(x, df['NDVI_HR'])
        
        trend_agreement = 1 - abs(slope_sr - slope_hr) / (abs(slope_hr) + 1e-8)
        
        return {
            'temporal_correlation': corr,
            'temporal_mae': mae_temporal,
            'temporal_rmse': rmse_temporal,
            'trend_sr': slope_sr,
            'trend_hr': slope_hr,
            'trend_agreement': trend_agreement
        }
    
    def visualize_timeseries(self, output_path):
        """
        Visualiza series temporales
        """
        df = self.calculate_ndvi_timeseries()
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Plot 1: NDVI temporal
        axes[0].plot(df['date'], df['NDVI_HR'], 'o-', label='HR (Ground Truth)', color='green', linewidth=2)
        axes[0].plot(df['date'], df['NDVI_SR'], 's--', label='SR', color='orange', linewidth=2)
        axes[0].set_ylabel('NDVI')
        axes[0].set_title('NDVI Temporal Evolution')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Error temporal
        axes[1].plot(df['date'], df['NDVI_diff'], 'o-', color='red')
        axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[1].fill_between(df['date'], 0, df['NDVI_diff'], alpha=0.3, color='red')
        axes[1].set_xlabel('Date')
        axes[1].set_ylabel('NDVI Difference (SR - HR)')
        axes[1].set_title('Temporal Consistency')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Visualización guardada: {output_path}")
    
    def generate_report(self, output_dir):
        """
        Genera reporte de análisis temporal
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calcular métricas
        df = self.calculate_ndvi_timeseries()
        consistency = self.calculate_temporal_consistency()
        changes = self.detect_changes()
        
        # Guardar CSV
        df.to_csv(output_dir / 'temporal_ndvi.csv', index=False)
        
        # Visualización
        self.visualize_timeseries(output_dir / 'temporal_analysis.png')
        
        # Resumen JSON
        import json
        summary = {
            'n_observations': len(self.temporal_data),
            'date_range': {
                'start': str(df['date'].min()),
                'end': str(df['date'].max())
            },
            'consistency_metrics': consistency,
            'significant_changes': len(changes)
        }
        
        with open(output_dir / 'temporal_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Imprimir resumen
        print(f"\n{'='*60}")
        print("📅 ANÁLISIS TEMPORAL")
        print(f"{'='*60}\n")
        print(f"Observaciones: {len(self.temporal_data)}")
        print(f"Rango: {df['date'].min()} - {df['date'].max()}")
        print(f"\nConsistencia Temporal:")
        print(f"   Correlación: {consistency['temporal_correlation']:.4f}")
        print(f"   MAE: {consistency['temporal_mae']:.4f}")
        print(f"   RMSE: {consistency['temporal_rmse']:.4f}")
        print(f"   Trend Agreement: {consistency['trend_agreement']:.4f}")
        print(f"\nCambios Detectados: {len(changes)}")
        
        print(f"\n✅ Reporte guardado en: {output_dir}")
        
        return summary


# Test
if __name__ == "__main__":
    print("📅 Temporal Analysis Module")
    print("Usage:")
    print("  1. Create analyzer: analyzer = TemporalAnalyzer()")
    print("  2. Add observations: analyzer.add_observation(date, sr_img, hr_img)")
    print("  3. Generate report: analyzer.generate_report(output_dir)")
