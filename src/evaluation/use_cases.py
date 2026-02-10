"""
Casos de uso específicos para agricultura
Evalúa SR en aplicaciones reales
"""
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, Tuple


class WaterStressDetector:
    """
    Detecta estrés hídrico usando índices de vegetación
    """
    
    def __init__(self):
        # Umbrales NDVI para estrés (ajustar según cultivo)
        self.stress_thresholds = {
            'severe': 0.3,
            'moderate': 0.5,
            'mild': 0.6,
            'healthy': 0.7
        }
    
    def detect_stress(self, image):
        """
        Detecta niveles de estrés hídrico
        
        Args:
            image: [C, H, W] con [R, G, B, NIR]
        
        Returns:
            stress_map, statistics
        """
        # Calcular NDVI
        red = image[0]
        nir = image[3]
        
        denominator = nir + red
        denominator = np.where(denominator == 0, 1e-8, denominator)
        ndvi = (nir - red) / denominator
        
        # Clasificar estrés
        stress_map = np.zeros_like(ndvi, dtype=np.uint8)
        stress_map[ndvi < self.stress_thresholds['severe']] = 3  # Severo
        stress_map[(ndvi >= self.stress_thresholds['severe']) & (ndvi < self.stress_thresholds['moderate'])] = 2  # Moderado
        stress_map[(ndvi >= self.stress_thresholds['moderate']) & (ndvi < self.stress_thresholds['mild'])] = 1  # Leve
        stress_map[ndvi >= self.stress_thresholds['healthy']] = 0  # Saludable
        
        # Estadísticas
        total_pixels = np.prod(stress_map.shape)
        stats = {
            'healthy_percent': np.sum(stress_map == 0) / total_pixels * 100,
            'mild_stress_percent': np.sum(stress_map == 1) / total_pixels * 100,
            'moderate_stress_percent': np.sum(stress_map == 2) / total_pixels * 100,
            'severe_stress_percent': np.sum(stress_map == 3) / total_pixels * 100
        }
        
        return stress_map, stats
    
    def compare_detection(self, sr_img, hr_img):
        """
        Compara detección de estrés en SR vs HR
        
        Returns:
            Dict con métricas de comparación
        """
        stress_sr, stats_sr = self.detect_stress(sr_img)
        stress_hr, stats_hr = self.detect_stress(hr_img)
        
        # Accuracy
        accuracy = np.mean(stress_sr == stress_hr)
        
        # Per-class accuracy
        from sklearn.metrics import classification_report
        
        report = classification_report(
            stress_hr.flatten(),
            stress_sr.flatten(),
            target_names=['Healthy', 'Mild', 'Moderate', 'Severe'],
            output_dict=True,
            zero_division=0
        )
        
        return {
            'accuracy': accuracy,
            'stats_sr': stats_sr,
            'stats_hr': stats_hr,
            'classification_report': report,
            'stress_map_sr': stress_sr,
            'stress_map_hr': stress_hr
        }


class CropHealthMonitor:
    """
    Monitorea salud general de cultivos
    """
    
    def assess_health(self, image):
        """
        Evalúa salud del cultivo usando múltiples índices
        
        Args:
            image: [C, H, W] con [R, G, B, NIR]
        
        Returns:
            health_score, components
        """
        red = image[0]
        green = image[1]
        blue = image[2]
        nir = image[3]
        
        # NDVI
        ndvi = self._safe_divide(nir - red, nir + red)
        
        # EVI
        evi = 2.5 * self._safe_divide(nir - red, nir + 6*red - 7.5*blue + 1)
        
        # GNDVI (Green NDVI)
        gndvi = self._safe_divide(nir - green, nir + green)
        
        # Score compuesto (normalizado 0-1)
        ndvi_norm = np.clip((ndvi + 1) / 2, 0, 1)
        evi_norm = np.clip((evi + 1) / 2, 0, 1)
        gndvi_norm = np.clip((gndvi + 1) / 2, 0, 1)
        
        health_score = (ndvi_norm * 0.5 + evi_norm * 0.3 + gndvi_norm * 0.2)
        
        components = {
            'ndvi': ndvi,
            'evi': evi,
            'gndvi': gndvi,
            'ndvi_mean': np.mean(ndvi[np.isfinite(ndvi)]),
            'evi_mean': np.mean(evi[np.isfinite(evi)]),
            'gndvi_mean': np.mean(gndvi[np.isfinite(gndvi)])
        }
        
        return health_score, components
    
    def _safe_divide(self, num, denom):
        """División segura"""
        return np.divide(num, denom, out=np.zeros_like(num), where=denom!=0)


class YieldPredictionHelper:
    """
    Ayuda a preparar datos para predicción de rendimiento
    """
    
    def extract_yield_features(self, images_timeseries):
        """
        Extrae features temporales para predicción de rendimiento
        
        Args:
            images_timeseries: Lista de [C, H, W] imágenes en diferentes fechas
        
        Returns:
            feature_array
        """
        features = []
        
        for img in images_timeseries:
            red = img[0]
            nir = img[3]
            
            # NDVI
            ndvi = self._safe_divide(nir - red, nir + red)
            
            # Estadísticas espaciales
            ndvi_mean = np.mean(ndvi[np.isfinite(ndvi)])
            ndvi_std = np.std(ndvi[np.isfinite(ndvi)])
            ndvi_max = np.max(ndvi[np.isfinite(ndvi)])
            
            features.extend([ndvi_mean, ndvi_std, ndvi_max])
        
        return np.array(features)
    
    def _safe_divide(self, num, denom):
        """División segura"""
        return np.divide(num, denom, out=np.zeros_like(num), where=denom!=0)


def evaluate_use_cases(sr_dir, hr_dir, output_dir):
    """
    Evalúa todos los casos de uso
    
    Args:
        sr_dir: Directorio con imágenes SR
        hr_dir: Directorio con imágenes HR
        output_dir: Directorio para resultados
    """
    from pathlib import Path
    
    sr_dir = Path(sr_dir)
    hr_dir = Path(hr_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Buscar imágenes
    sr_files = sorted(list(sr_dir.glob('*.npy')))
    
    # Inicializar detectores
    water_stress_detector = WaterStressDetector()
    health_monitor = CropHealthMonitor()
    
    results = {
        'water_stress': [],
        'crop_health': []
    }
    
    print(f"\n🌾 Evaluando casos de uso en {len(sr_files)} imágenes...")
    
    for sr_file in sr_files:
        hr_file = hr_dir / sr_file.name
        
        if not hr_file.exists():
            continue
        
        # Cargar
        sr_img = np.load(sr_file)
        hr_img = np.load(hr_file)
        
        # Estrés hídrico
        stress_result = water_stress_detector.compare_detection(sr_img, hr_img)
        results['water_stress'].append(stress_result)
        
        # Salud de cultivos
        health_sr, comp_sr = health_monitor.assess_health(sr_img)
        health_hr, comp_hr = health_monitor.assess_health(hr_img)
        
        health_result = {
            'components_sr': comp_sr,
            'components_hr': comp_hr,
            'health_correlation': np.corrcoef(health_sr.flatten(), health_hr.flatten())[0, 1]
        }
        results['crop_health'].append(health_result)
    
    # Resumen
    print(f"\n{'='*60}")
    print("🌾 RESULTADOS CASOS DE USO")
    print(f"{'='*60}\n")
    
    # Estrés hídrico
    stress_accuracies = [r['accuracy'] for r in results['water_stress']]
    print(f"Estrés Hídrico:")
    print(f"   Accuracy promedio: {np.mean(stress_accuracies):.4f}")
    
    # Salud de cultivos
    health_corrs = [r['health_correlation'] for r in results['crop_health']]
    print(f"\nSalud de Cultivos:")
    print(f"   Correlación promedio: {np.mean(health_corrs):.4f}")
    
    # Guardar
    import json
    summary = {
        'water_stress_accuracy_mean': float(np.mean(stress_accuracies)),
        'crop_health_correlation_mean': float(np.mean(health_corrs))
    }
    
    with open(output_dir / 'use_cases_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Resultados guardados en: {output_dir}")
    
    return results


# Test
if __name__ == "__main__":
    print("🌾 Use Cases Module")
    print("Available:")
    print("  - WaterStressDetector")
    print("  - CropHealthMonitor")
    print("  - YieldPredictionHelper")
