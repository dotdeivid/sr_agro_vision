"""
Ensemble de modelos SR para mejorar resultados
Combina predicciones de múltiples modelos entrenados
"""
import torch
import numpy as np
from pathlib import Path
from typing import List

from src.models.espcn import ESPCNMultispectral
from src.utils.device import get_device


class EnsembleSR:
    """
    Ensemble de múltiples modelos SR
    Combina predicciones mediante promedio ponderado
    """
    
    def __init__(self, model_paths: List[str], weights: List[float] = None,
                 num_channels=4, scale_factor=4, device=None):
        """
        Args:
            model_paths: Lista de rutas a modelos .pth
            weights: Pesos para cada modelo (default: promedio simple)
            num_channels: Canales
            scale_factor: Factor de escalado
            device: Dispositivo
        """
        self.device = device or get_device()
        self.scale_factor = scale_factor
        self.num_channels = num_channels
        
        # Cargar modelos
        self.models = []
        for path in model_paths:
            model = ESPCNMultispectral(
                scale_factor=scale_factor,
                num_channels=num_channels,
                num_features=64
            )
            model.load_state_dict(torch.load(path, map_location=self.device))
            model.to(self.device)
            model.eval()
            self.models.append(model)
        
        # Pesos de ensemble
        if weights is None:
            self.weights = [1.0 / len(self.models)] * len(self.models)
        else:
            assert len(weights) == len(self.models)
            # Normalizar
            total = sum(weights)
            self.weights = [w / total for w in weights]
        
        print(f"✅ Ensemble creado con {len(self.models)} modelos")
        print(f"   Pesos: {self.weights}")
    
    def predict(self, lr_image):
        """
        Predicción ensemble
        
        Args:
            lr_image: [B, C, H, W] o [C, H, W]
        
        Returns:
            [B, C, H*scale, W*scale] o [C, H*scale, W*scale]
        """
        was_3d = False
        if lr_image.dim() == 3:
            lr_image = lr_image.unsqueeze(0)
            was_3d = True
        
        lr_image = lr_image.to(self.device)
        
        # Predicciones de cada modelo
        predictions = []
        with torch.no_grad():
            for model in self.models:
                pred = model(lr_image)
                predictions.append(pred)
        
        # Combinar con pesos
        ensemble_pred = torch.zeros_like(predictions[0])
        for pred, weight in zip(predictions, self.weights):
            ensemble_pred += pred * weight
        
        if was_3d:
            ensemble_pred = ensemble_pred.squeeze(0)
        
        return ensemble_pred
    
    def predict_with_variance(self, lr_image):
        """
        Predicción con estimación de incertidumbre
        
        Returns:
            mean: Predicción promedio
            std: Desviación estándar (incertidumbre)
        """
        was_3d = False
        if lr_image.dim() == 3:
            lr_image = lr_image.unsqueeze(0)
            was_3d = True
        
        lr_image = lr_image.to(self.device)
        
        # Predicciones
        predictions = []
        with torch.no_grad():
            for model in self.models:
                pred = model(lr_image)
                predictions.append(pred)
        
        # Stack y calcular estadísticas
        predictions = torch.stack(predictions, dim=0)  # [N_models, B, C, H, W]
        
        mean = predictions.mean(dim=0)
        std = predictions.std(dim=0)
        
        if was_3d:
            mean = mean.squeeze(0)
            std = std.squeeze(0)
        
        return mean, std


def create_ensemble_from_checkpoints(checkpoint_dir, num_models=5, 
                                      num_channels=4, scale_factor=4):
    """
    Crea ensemble seleccionando mejores checkpoints
    
    Args:
        checkpoint_dir: Directorio con checkpoints
        num_models: Número de modelos a incluir
    
    Returns:
        EnsembleSR
    """
    checkpoint_dir = Path(checkpoint_dir)
    
    # Buscar checkpoints
    checkpoints = list(checkpoint_dir.glob('*.pth'))
    
    # Ordenar por nombre (asumiendo best_psnr, best_ndvi, etc.)
    checkpoints = sorted(checkpoints)[:num_models]
    
    if len(checkpoints) < num_models:
        print(f"⚠️ Solo se encontraron {len(checkpoints)} checkpoints")
    
    checkpoint_paths = [str(cp) for cp in checkpoints]
    
    return EnsembleSR(checkpoint_paths, num_channels=num_channels, 
                     scale_factor=scale_factor)


# Test
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Ensemble SR')
    parser.add_argument('--models', nargs='+', required=True,
                       help='Lista de modelos .pth')
    parser.add_argument('--weights', nargs='+', type=float, default=None,
                       help='Pesos para cada modelo (opcional)')
    
    args = parser.parse_args()
    
    # Crear ensemble
    ensemble = EnsembleSR(args.models, weights=args.weights)
    
    # Test con imagen aleatoria
    lr_img = torch.randn(1, 4, 256, 256)
    
    # Predicción ensemble
    sr_img = ensemble.predict(lr_img)
    
    print(f"Input: {lr_img.shape}")
    print(f"Output: {sr_img.shape}")
    print("✅ Ensemble funcionando correctamente")
