"""
Métricas agrícolas avanzadas para evaluación SR
Calcula precisión en índices de vegetación y compara con ground truth
"""
import numpy as np
import torch
from pathlib import Path
from typing import Dict, Tuple
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class AgriculturalMetrics:
    """
    Métricas específicas para evaluación agrícola de SR
    """
    
    def __init__(self, sr_img, hr_img):
        """
        Args:
            sr_img: Imagen SR [C, H, W] con canales [R, G, B, NIR]
            hr_img: Ground truth HR [C, H, W]
        """
        self.sr_img = self._to_numpy(sr_img)
        self.hr_img = self._to_numpy(hr_img)
        
        # Extraer bandas (asumiendo orden R, G, B, NIR)
        self.sr_red = self.sr_img[0]
        self.sr_green = self.sr_img[1]
        self.sr_blue = self.sr_img[2]
        self.sr_nir = self.sr_img[3]
        
        self.hr_red = self.hr_img[0]
        self.hr_green = self.hr_img[1]
        self.hr_blue = self.hr_img[2]
        self.hr_nir = self.hr_img[3]
    
    def _to_numpy(self, img):
        """Convierte tensor a numpy si es necesario"""
        if isinstance(img, torch.Tensor):
            return img.detach().cpu().numpy()
        return img
    
    def calculate_ndvi(self, red, nir):
        """Normalized Difference Vegetation Index"""
        denominator = nir + red
        denominator = np.where(denominator == 0, 1e-8, denominator)
        return (nir - red) / denominator
    
    def calculate_evi(self, red, nir, blue, G=2.5, C1=6, C2=7.5, L=1):
        """Enhanced Vegetation Index"""
        denominator = nir + C1 * red - C2 * blue + L
        denominator = np.where(denominator == 0, 1e-8, denominator)
        return G * (nir - red) / denominator
    
    def calculate_savi(self, red, nir, L=0.5):
        """Soil-Adjusted Vegetation Index"""
        denominator = nir + red + L
        denominator = np.where(denominator == 0, 1e-8, denominator)
        return ((nir - red) / denominator) * (1 + L)
    
    def evaluate_vegetation_indices(self) -> Dict[str, Dict[str, float]]:
        """
        Evalúa precisión en índices de vegetación
        
        Returns:
            Dict con métricas para cada índice
        """
        results = {}
        
        # NDVI
        ndvi_sr = self.calculate_ndvi(self.sr_red, self.sr_nir)
        ndvi_hr = self.calculate_ndvi(self.hr_red, self.hr_nir)
        
        results['NDVI'] = self._calculate_index_metrics(ndvi_sr, ndvi_hr, 'NDVI')
        
        # EVI
        evi_sr = self.calculate_evi(self.sr_red, self.sr_nir, self.sr_blue)
        evi_hr = self.calculate_evi(self.hr_red, self.hr_nir, self.hr_blue)
        
        results['EVI'] = self._calculate_index_metrics(evi_sr, evi_hr, 'EVI')
        
        # SAVI
        savi_sr = self.calculate_savi(self.sr_red, self.sr_nir)
        savi_hr = self.calculate_savi(self.hr_red, self.hr_nir)
        
        results['SAVI'] = self._calculate_index_metrics(savi_sr, savi_hr, 'SAVI')
        
        return results
    
    def _calculate_index_metrics(self, index_sr, index_hr, name) -> Dict[str, float]:
        """
        Calcula métricas de error para un índice
        
        Returns:
            Dict con MAE, RMSE, R², Pearson
        """
        # Flatten para cálculos
        sr_flat = index_sr.flatten()
        hr_flat = index_hr.flatten()
        
        # Remover NaN/Inf
        valid_mask = np.isfinite(sr_flat) & np.isfinite(hr_flat)
        sr_valid = sr_flat[valid_mask]
        hr_valid = hr_flat[valid_mask]
        
        # Métricas
        mae = mean_absolute_error(hr_valid, sr_valid)
        rmse = np.sqrt(mean_squared_error(hr_valid, sr_valid))
        r2 = r2_score(hr_valid, sr_valid)
        pearson_r, pearson_p = pearsonr(sr_valid, hr_valid)
        
        # Bias (sesgo sistemático)
        bias = np.mean(sr_valid - hr_valid)
        
        return {
            'MAE': mae,
            'RMSE': rmse,
            'R2': r2,
            'Pearson_r': pearson_r,
            'Pearson_p': pearson_p,
            'Bias': bias,
            'name': name
        }
    
    def classify_vegetation_health(self, index_type='NDVI') -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Clasifica salud de vegetación en categorías
        
        Args:
            index_type: 'NDVI', 'EVI', o 'SAVI'
        
        Returns:
            classes_sr, classes_hr, metrics_dict
        """
        if index_type == 'NDVI':
            index_sr = self.calculate_ndvi(self.sr_red, self.sr_nir)
            index_hr = self.calculate_ndvi(self.hr_red, self.hr_nir)
            thresholds = [0.2, 0.4, 0.6]  # Sin vegetación, Baja, Moderada, Alta
        elif index_type == 'EVI':
            index_sr = self.calculate_evi(self.sr_red, self.sr_nir, self.sr_blue)
            index_hr = self.calculate_evi(self.hr_red, self.hr_nir, self.hr_blue)
            thresholds = [0.2, 0.4, 0.6]
        elif index_type == 'SAVI':
            index_sr = self.calculate_savi(self.sr_red, self.sr_nir)
            index_hr = self.calculate_savi(self.hr_red, self.hr_nir)
            thresholds = [0.2, 0.4, 0.6]
        
        # Clasificar
        classes_sr = self._classify_with_thresholds(index_sr, thresholds)
        classes_hr = self._classify_with_thresholds(index_hr, thresholds)
        
        # Calcular accuracy
        from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
        
        sr_flat = classes_sr.flatten()
        hr_flat = classes_hr.flatten()
        
        accuracy = accuracy_score(hr_flat, sr_flat)
        conf_matrix = confusion_matrix(hr_flat, sr_flat)
        
        # Per-class accuracy
        class_names = ['Sin Veg', 'Baja', 'Moderada', 'Alta']
        report = classification_report(hr_flat, sr_flat, 
                                       target_names=class_names, 
                                       output_dict=True)
        
        metrics = {
            'overall_accuracy': accuracy,
            'confusion_matrix': conf_matrix,
            'classification_report': report,
            'class_names': class_names
        }
        
        return classes_sr, classes_hr, metrics
    
    def _classify_with_thresholds(self, index, thresholds):
        """Clasifica índice con umbrales"""
        classes = np.zeros_like(index, dtype=np.uint8)
        
        classes[index < thresholds[0]] = 0  # Sin vegetación
        classes[(index >= thresholds[0]) & (index < thresholds[1])] = 1  # Baja
        classes[(index >= thresholds[1]) & (index < thresholds[2])] = 2  # Moderada
        classes[index >= thresholds[2]] = 3  # Alta
        
        return classes
    
    def visualize_comparison(self, output_path):
        """
        Visualiza comparación SR vs HR para todos los índices
        """
        fig, axes = plt.subplots(3, 3, figsize=(18, 18))
        
        indices = ['NDVI', 'EVI', 'SAVI']
        
        for i, idx_name in enumerate(indices):
            if idx_name == 'NDVI':
                sr_idx = self.calculate_ndvi(self.sr_red, self.sr_nir)
                hr_idx = self.calculate_ndvi(self.hr_red, self.hr_nir)
            elif idx_name == 'EVI':
                sr_idx = self.calculate_evi(self.sr_red, self.sr_nir, self.sr_blue)
                hr_idx = self.calculate_evi(self.hr_red, self.hr_nir, self.hr_blue)
            else:  # SAVI
                sr_idx = self.calculate_savi(self.sr_red, self.sr_nir)
                hr_idx = self.calculate_savi(self.hr_red, self.hr_nir)
            
            # SR
            im0 = axes[i, 0].imshow(sr_idx, cmap='RdYlGn', vmin=-1, vmax=1)
            axes[i, 0].set_title(f'{idx_name} - SR')
            axes[i, 0].axis('off')
            plt.colorbar(im0, ax=axes[i, 0])
            
            # HR
            im1 = axes[i, 1].imshow(hr_idx, cmap='RdYlGn', vmin=-1, vmax=1)
            axes[i, 1].set_title(f'{idx_name} - HR (Ground Truth)')
            axes[i, 1].axis('off')
            plt.colorbar(im1, ax=axes[i, 1])
            
            # Diferencia
            diff = np.abs(sr_idx - hr_idx)
            im2 = axes[i, 2].imshow(diff, cmap='hot', vmin=0, vmax=0.2)
            axes[i, 2].set_title(f'{idx_name} - Error Absoluto')
            axes[i, 2].axis('off')
            plt.colorbar(im2, ax=axes[i, 2])
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Visualización guardada: {output_path}")


def evaluate_batch(sr_dir, hr_dir, output_dir):
    """
    Evalúa batch completo de imágenes
    
    Args:
        sr_dir: Directorio con imágenes SR (.npy)
        hr_dir: Directorio con imágenes HR (.npy)
        output_dir: Directorio para resultados
    """
    sr_dir = Path(sr_dir)
    hr_dir = Path(hr_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Buscar imágenes
    sr_files = sorted(list(sr_dir.glob('*.npy')))
    
    all_results = {
        'NDVI': {'MAE': [], 'RMSE': [], 'R2': [], 'Pearson_r': []},
        'EVI': {'MAE': [], 'RMSE': [], 'R2': [], 'Pearson_r': []},
        'SAVI': {'MAE': [], 'RMSE': [], 'R2': [], 'Pearson_r': []}
    }
    
    print(f"\n📊 Evaluando {len(sr_files)} imágenes...")
    
    for sr_file in sr_files:
        hr_file = hr_dir / sr_file.name
        
        if not hr_file.exists():
            continue
        
        # Cargar imágenes
        sr_img = np.load(sr_file)
        hr_img = np.load(hr_file)
        
        # Evaluar
        metrics_eval = AgriculturalMetrics(sr_img, hr_img)
        results = metrics_eval.evaluate_vegetation_indices()
        
        # Acumular resultados
        for idx_name in ['NDVI', 'EVI', 'SAVI']:
            for metric in ['MAE', 'RMSE', 'R2', 'Pearson_r']:
                all_results[idx_name][metric].append(results[idx_name][metric])
    
    # Calcular promedios
    print("\n" + "="*60)
    print("📈 RESULTADOS MÉTRICAS AGRÍCOLAS")
    print("="*60)
    
    summary = {}
    for idx_name in ['NDVI', 'EVI', 'SAVI']:
        print(f"\n🌱 {idx_name}:")
        summary[idx_name] = {}
        
        for metric in ['MAE', 'RMSE', 'R2', 'Pearson_r']:
            values = all_results[idx_name][metric]
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            summary[idx_name][f'{metric}_mean'] = mean_val
            summary[idx_name][f'{metric}_std'] = std_val
            
            print(f"   {metric}: {mean_val:.4f} ± {std_val:.4f}")
    
    # Guardar resultados
    import json
    with open(output_dir / 'agricultural_metrics_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Resultados guardados en: {output_dir}")
    
    return summary


# Test
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Agricultural Metrics')
    parser.add_argument('--sr-dir', type=str, required=True,
                       help='Directory with SR images')
    parser.add_argument('--hr-dir', type=str, required=True,
                       help='Directory with HR ground truth')
    parser.add_argument('--output-dir', type=str, default='results/phase4/metrics',
                       help='Output directory')
    
    args = parser.parse_args()
    
    summary = evaluate_batch(args.sr_dir, args.hr_dir, args.output_dir)
