"""
Métricas específicas para evaluación agrícola
"""

import torch
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.training.metrics import calculate_psnr, calculate_ssim
from src.utils.ndvi import calculate_ndvi


def calculate_ndvi_error(sr_img, hr_img, dataset_type="multiespectral"):
    """
    Calcula error en NDVI (solo para imágenes multiespectrales)

    Args:
        sr_img: [C, H, W] o [B, C, H, W]
        hr_img: [C, H, W] o [B, C, H, W]
        dataset_type: Tipo de dataset ('multiespectral' o 'rgb')

    Returns:
        MAE del NDVI (0.0 si es RGB o menos de 4 canales)
    """
    # Hacer squeeze del batch ANTES de verificar canales
    # (shape[0] debe ser C, no B)
    if sr_img.dim() == 4:
        sr_img = sr_img[0]
        hr_img = hr_img[0]

    if dataset_type != "multiespectral" or sr_img.shape[0] < 4:
        return 0.0  # No hay NIR, no se puede calcular NDVI

    # Convertir a numpy
    if isinstance(sr_img, torch.Tensor):
        sr_img = sr_img.detach().cpu().numpy()
    if isinstance(hr_img, torch.Tensor):
        hr_img = hr_img.detach().cpu().numpy()

    # Extraer bandas Red (canal 0) y NIR (canal 3)
    sr_red = sr_img[0]
    sr_nir = sr_img[3]
    hr_red = hr_img[0]
    hr_nir = hr_img[3]

    # Calcular NDVI
    ndvi_sr = calculate_ndvi(sr_red, sr_nir)
    ndvi_hr = calculate_ndvi(hr_red, hr_nir)

    # MAE (Mean Absolute Error)
    mae = np.mean(np.abs(ndvi_sr - ndvi_hr))

    return mae


def calculate_spectral_angle(sr_img, hr_img):
    """
    Spectral Angle Mapper (SAM) - mide similitud espectral

    Ángulo entre vectores espectrales (todos los canales)
    SAM bajo = espectro similar

    Args:
        sr_img: [C, H, W]
        hr_img: [C, H, W]

    Returns:
        SAM promedio en grados
    """
    if isinstance(sr_img, torch.Tensor):
        sr_img = sr_img.detach().cpu().numpy()
    if isinstance(hr_img, torch.Tensor):
        hr_img = hr_img.detach().cpu().numpy()

    # Reshape a [H*W, C]
    c, h, w = sr_img.shape
    sr_vectors = sr_img.reshape(c, -1).T  # [H*W, C]
    hr_vectors = hr_img.reshape(c, -1).T

    # Producto punto
    dot_product = np.sum(sr_vectors * hr_vectors, axis=1)

    # Normas
    sr_norm = np.linalg.norm(sr_vectors, axis=1)
    hr_norm = np.linalg.norm(hr_vectors, axis=1)

    # Evitar división por cero
    denominator = sr_norm * hr_norm
    denominator[denominator == 0] = 1e-8

    # Ángulo espectral en radianes
    cos_angle = np.clip(dot_product / denominator, -1, 1)
    angle_rad = np.arccos(cos_angle)

    # Convertir a grados
    angle_deg = np.rad2deg(angle_rad)

    # Promedio
    sam = np.mean(angle_deg)

    return sam


def evaluate_satellite_metrics(sr_img, hr_img, dataset_type="multiespectral"):
    """
    Calcula todas las métricas relevantes para imágenes

    Args:
        sr_img: Imagen SR [B, C, H, W] o [C, H, W]
        hr_img: Imagen HR
        dataset_type: Tipo de dataset ('multiespectral' o 'rgb')

    Returns:
        dict con métricas
    """
    # Agregar dimensión de batch si es necesario
    if sr_img.dim() == 3:
        sr_img = sr_img.unsqueeze(0)
        hr_img = hr_img.unsqueeze(0)

    # Métricas estándar (PSNR, SSIM)
    psnr = calculate_psnr(sr_img, hr_img, max_value=1.0)
    ssim = calculate_ssim(sr_img, hr_img, max_value=1.0)

    # Métricas específicas de agricultura (solo si es multiespectral)
    if dataset_type == "multiespectral":
        ndvi_mae = calculate_ndvi_error(sr_img, hr_img, dataset_type="multiespectral")
        sam = calculate_spectral_angle(
            sr_img[0], hr_img[0]
        )  # Tomar primer elemento del batch
    else:
        ndvi_mae = 0.0
        sam = 0.0

    metrics = {"psnr": psnr, "ssim": ssim, "ndvi_mae": ndvi_mae, "sam": sam}

    return metrics


class AgricultureMetricsTracker:
    """Clase para trackear métricas durante entrenamiento"""

    def __init__(self, dataset_type="multiespectral"):
        """
        Args:
            dataset_type: Tipo de dataset ('multiespectral' o 'rgb')
        """
        self.dataset_type = dataset_type
        self.reset()

    def reset(self):
        self.psnr_sum = 0
        self.ssim_sum = 0
        self.ndvi_mae_sum = 0
        self.sam_sum = 0
        self.count = 0

    def update(self, sr_batch, hr_batch):
        """
        Actualiza métricas con un batch

        Args:
            sr_batch: [B, C, H, W]
            hr_batch: [B, C, H, W]
        """
        batch_size = sr_batch.size(0)

        for i in range(batch_size):
            metrics = evaluate_satellite_metrics(
                sr_batch[i : i + 1], hr_batch[i : i + 1], dataset_type=self.dataset_type
            )

            self.psnr_sum += metrics["psnr"]
            self.ssim_sum += metrics["ssim"]
            self.ndvi_mae_sum += metrics["ndvi_mae"]
            self.sam_sum += metrics["sam"]
            self.count += 1

    def get_averages(self):
        """Retorna métricas promedio"""
        if self.count == 0:
            return {"psnr": 0.0, "ssim": 0.0, "ndvi_mae": 0.0, "sam": 0.0}

        return {
            "psnr": self.psnr_sum / self.count,
            "ssim": self.ssim_sum / self.count,
            "ndvi_mae": self.ndvi_mae_sum / self.count,
            "sam": self.sam_sum / self.count,
        }


# Test
if __name__ == "__main__":
    # Test con datos sintéticos (4 canales)
    sr_img = torch.rand(1, 4, 128, 128)
    hr_img = torch.rand(1, 4, 128, 128)

    metrics = evaluate_satellite_metrics(sr_img, hr_img)

    print("Métricas calculadas:")
    print(f"  PSNR: {metrics['psnr']:.2f} dB")
    print(f"  SSIM: {metrics['ssim']:.4f}")
    print(f"  NDVI MAE: {metrics['ndvi_mae']:.6f}")
    print(f"  SAM: {metrics['sam']:.2f}°")

    # Test tracker
    tracker = AgricultureMetricsTracker()

    for _ in range(5):
        sr_batch = torch.rand(4, 4, 64, 64)
        hr_batch = torch.rand(4, 4, 64, 64)
        tracker.update(sr_batch, hr_batch)

    avg_metrics = tracker.get_averages()
    print("\nMétricas promedio (5 batches):")
    print(f"  PSNR: {avg_metrics['psnr']:.2f} dB")
    print(f"  SSIM: {avg_metrics['ssim']:.4f}")

    print("\n✅ Agriculture metrics test OK")
