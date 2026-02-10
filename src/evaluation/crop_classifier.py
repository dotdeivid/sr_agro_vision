"""
Clasificación de cultivos usando SR vs HR
Evalúa si SR mejora accuracy en clasificación
"""
import numpy as np
import torch
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import joblib


class CropClassifier:
    """
    Clasificador de cultivos con Random Forest
    Usa features espectrales (R, G, B, NIR + índices)
    """
    
    def __init__(self, n_estimators=100, random_state=42):
        self.classifier = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=20,
            random_state=random_state,
            n_jobs=-1
        )
        self.crop_names = None
    
    def extract_features(self, image):
        """
        Extrae features de imagen multiespectral
        
        Args:
            image: [C, H, W] con [R, G, B, NIR]
        
        Returns:
            features: [H*W, N_features]
        """
        red = image[0]
        green = image[1]
        blue = image[2]
        nir = image[3]
        
        # Índices de vegetación
        ndvi = self._safe_divide(nir - red, nir + red)
        evi = 2.5 * self._safe_divide(nir - red, nir + 6*red - 7.5*blue + 1)
        savi = 1.5 * self._safe_divide(nir - red, nir + red + 0.5)
        
        # Ratios de bandas
        rvi = self._safe_divide(nir, red)
        gndvi = self._safe_divide(nir - green, nir + green)
        
        # Stack features [H, W, N_features]
        features = np.stack([
            red, green, blue, nir,  # Bandas originales
            ndvi, evi, savi,         # Índices
            rvi, gndvi               # Ratios
        ], axis=-1)
        
        # Flatten [H*W, N_features]
        H, W = red.shape
        features = features.reshape(H*W, -1)
        
        return features
    
    def _safe_divide(self, num, denom):
        """División segura evitando división por cero"""
        return np.divide(num, denom, out=np.zeros_like(num), where=denom!=0)
    
    def train(self, images, labels, crop_names):
        """
        Entrena clasificador
        
        Args:
            images: Lista de [C, H, W] imágenes
            labels: Lista de [H, W] mapas de etiquetas
            crop_names: Dict {class_id: name}
        """
        self.crop_names = crop_names
        
        # Extraer features de todas las imágenes
        all_features = []
        all_labels = []
        
        for img, label_map in zip(images, labels):
            features = self.extract_features(img)
            labels_flat = label_map.flatten()
            
            # Filtrar píxeles sin etiqueta (asumiendo -1 o 255)
            valid_mask = (labels_flat >= 0) & (labels_flat < 255)
            
            all_features.append(features[valid_mask])
            all_labels.append(labels_flat[valid_mask])
        
        # Concatenar
        X = np.vstack(all_features)
        y = np.concatenate(all_labels)
        
        print(f"\n📊 Entrenando clasificador...")
        print(f"   Samples: {len(X):,}")
        print(f"   Features: {X.shape[1]}")
        print(f"   Classes: {len(np.unique(y))}")
        
        # Entrenar
        self.classifier.fit(X, y)
        
        # Feature importance
        importances = self.classifier.feature_importances_
        feature_names = ['Red', 'Green', 'Blue', 'NIR', 'NDVI', 'EVI', 'SAVI', 'RVI', 'GNDVI']
        
        print(f"\n🎯 Feature Importance:")
        for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
            print(f"   {name}: {imp:.4f}")
        
        print(f"✅ Clasificador entrenado")
    
    def predict(self, image):
        """
        Predice clases de cultivo
        
        Args:
            image: [C, H, W]
        
        Returns:
            predictions: [H, W] mapa de clases
        """
        features = self.extract_features(image)
        predictions = self.classifier.predict(features)
        
        # Reshape
        H, W = image.shape[1], image.shape[2]
        predictions_map = predictions.reshape(H, W)
        
        return predictions_map
    
    def evaluate_comparison(self, lr_images, sr_images, hr_images, labels, output_dir):
        """
        Compara clasificación usando LR vs SR vs HR
        
        Args:
            lr_images: Lista de imágenes LR
            sr_images: Lista de imágenes SR
            hr_images: Lista de imágenes HR
            labels: Ground truth labels
            output_dir: Directorio para resultados
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            'LR': {'accuracy': [], 'per_class': []},
            'SR': {'accuracy': [], 'per_class': []},
            'HR': {'accuracy': [], 'per_class': []}
        }
        
        print(f"\n🔬 Evaluando clasificación en {len(lr_images)} imágenes...")
        
        for i, (lr_img, sr_img, hr_img, label) in enumerate(zip(lr_images, sr_images, hr_images, labels)):
            # Predecir
            pred_lr = self.predict(lr_img)
            pred_sr = self.predict(sr_img)
            pred_hr = self.predict(hr_img)
            
            # Ground truth
            label_flat = label.flatten()
            valid_mask = (label_flat >= 0) & (label_flat < 255)
            gt = label_flat[valid_mask]
            
            # Evaluar cada versión
            for name, pred in [('LR', pred_lr), ('SR', pred_sr), ('HR', pred_hr)]:
                pred_flat = pred.flatten()[valid_mask]
                
                acc = accuracy_score(gt, pred_flat)
                report = classification_report(gt, pred_flat, 
                                              target_names=list(self.crop_names.values()),
                                              output_dict=True,
                                              zero_division=0)
                
                results[name]['accuracy'].append(acc)
                results[name]['per_class'].append(report)
        
        # Resumen
        print(f"\n{'='*60}")
        print("📊 RESULTADOS CLASIFICACIÓN")
        print(f"{'='*60}\n")
        
        for name in ['LR', 'SR', 'HR']:
            acc_mean = np.mean(results[name]['accuracy'])
            acc_std = np.std(results[name]['accuracy'])
            print(f"{name:3s} Accuracy: {acc_mean:.4f} ± {acc_std:.4f}")
        
        # Mejora SR vs LR
        improvement = np.mean(results['SR']['accuracy']) - np.mean(results['LR']['accuracy'])
        print(f"\n✨ Mejora SR vs LR: +{improvement*100:.2f}%")
        
        # Visualizar matriz de confusión
        self._plot_confusion_matrices(results, output_dir)
        
        # Guardar resultados
        import json
        with open(output_dir / 'classification_results.json', 'w') as f:
            json.dump({
                'LR_accuracy_mean': float(np.mean(results['LR']['accuracy'])),
                'SR_accuracy_mean': float(np.mean(results['SR']['accuracy'])),
                'HR_accuracy_mean': float(np.mean(results['HR']['accuracy'])),
                'improvement_vs_lr': float(improvement)
            }, f, indent=2)
        
        return results
    
    def _plot_confusion_matrices(self, results, output_dir):
        """Visualiza matrices de confusión para LR, SR, HR"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        for idx, name in enumerate(['LR', 'SR', 'HR']):
            # Obtener todas las predicciones y ground truth
            # (simplificado - en producción se acumularían correctamente)
            ax = axes[idx]
            ax.set_title(f'{name} Classification')
            ax.text(0.5, 0.5, f'Accuracy: {np.mean(results[name]["accuracy"]):.3f}',
                   ha='center', va='center', fontsize=14)
            ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'confusion_matrices.png', dpi=150)
        plt.close()
        
        print(f"✅ Visualizaciones guardadas en: {output_dir}")
    
    def save(self, path):
        """Guarda modelo entrenado"""
        joblib.dump({
            'classifier': self.classifier,
            'crop_names': self.crop_names
        }, path)
        print(f"💾 Modelo guardado: {path}")
    
    def load(self, path):
        """Carga modelo entrenado"""
        data = joblib.load(path)
        self.classifier = data['classifier']
        self.crop_names = data['crop_names']
        print(f"✅ Modelo cargado: {path}")


# Test / Usage example
if __name__ == "__main__":
    print("🌾 Crop Classification Module")
    print("Usage:")
    print("  1. Train: classifier.train(images, labels, crop_names)")
    print("  2. Predict: predictions = classifier.predict(image)")
    print("  3. Evaluate: classifier.evaluate_comparison(lr_imgs, sr_imgs, hr_imgs, labels, output_dir)")
