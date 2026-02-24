"""
DataLoader para imágenes satelitales multiespectrales
"""

import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import numpy as np
import random


class SatelliteSRDataset(Dataset):
    """Dataset para super resolución de imágenes satelitales"""

    def __init__(self, lr_dir, hr_dir, augmentation=True, num_channels=4):
        """
        Args:
            lr_dir: Directorio con patches LR (.npy)
            hr_dir: Directorio con patches HR (.npy)
            augmentation: Aplicar data augmentation
            num_channels: Número de canales (4 para RGB+NIR)
        """
        self.lr_dir = Path(lr_dir)
        self.hr_dir = Path(hr_dir)
        self.augmentation = augmentation
        self.num_channels = num_channels

        # Listar patches LR
        all_lr_patches = sorted(list(self.lr_dir.glob("*.npy")))

        if len(all_lr_patches) == 0:
            raise ValueError(f"No se encontraron patches en {lr_dir}")

        # Filtrar patches incompatibles (canales incorrectos o sin HR par)
        # mmap_mode='r' lee solo el header del .npy sin cargar el array completo
        self.lr_patches = []
        self.hr_patches = []
        skipped = 0

        for lr_path in all_lr_patches:
            hr_path = self.hr_dir / lr_path.name
            if not hr_path.exists():
                skipped += 1
                continue

            # Verificar canales sin cargar el array completo
            try:
                lr_meta = np.load(lr_path, mmap_mode="r")
                if lr_meta.shape[0] != self.num_channels:
                    skipped += 1
                    continue
            except Exception:
                skipped += 1
                continue

            self.lr_patches.append(lr_path)
            self.hr_patches.append(hr_path)

        if len(self.lr_patches) == 0:
            raise ValueError(
                f"No hay patches válidos de {self.num_channels} canales en {lr_dir}. "
                f"({skipped} descartados por canales incorrectos o sin par HR)"
            )

        print(
            f"✅ Dataset cargado: {len(self.lr_patches)} patches ({self.num_channels} canales)"
        )
        if skipped:
            print(
                f"   ⚠️  {skipped} patches descartados (canales incorrectos o sin par)"
            )
        print(f"   LR dir: {self.lr_dir}")
        print(f"   HR dir: {self.hr_dir}")

    def __len__(self):
        return len(self.lr_patches)

    def __getitem__(self, idx):
        # Cargar patches
        lr_patch = np.load(self.lr_patches[idx])  # [C, H, W]
        hr_patch = np.load(self.hr_patches[idx])  # [C, H, W]

        # Data augmentation
        if self.augmentation:
            lr_patch, hr_patch = self._augment(lr_patch, hr_patch)

        # Ya están normalizados [0, 1] desde create_satellite_pairs
        # Convertir a tensors
        lr_tensor = torch.from_numpy(lr_patch).float()
        hr_tensor = torch.from_numpy(hr_patch).float()

        return lr_tensor, hr_tensor

    def _augment(self, lr, hr):
        """
        Data augmentation mejorado para imágenes satelitales

        Transformaciones:
        - Flip horizontal/vertical
        - Rotación 90°
        - Ajuste de brillo (solo RGB, no NIR)
        - Ruido gaussiano (simulación de sensores)

        Args:
            lr: Array [C, H, W]
            hr: Array [C, H, W]

        Returns:
            lr_aug, hr_aug
        """
        # Flip horizontal
        if random.random() > 0.5:
            lr = np.flip(lr, axis=2).copy()
            hr = np.flip(hr, axis=2).copy()

        # Flip vertical
        if random.random() > 0.5:
            lr = np.flip(lr, axis=1).copy()
            hr = np.flip(hr, axis=1).copy()

        # Rotación 90° (k veces)
        k = random.randint(0, 3)
        if k > 0:
            lr = np.rot90(lr, k, axes=(1, 2)).copy()
            hr = np.rot90(hr, k, axes=(1, 2)).copy()

        # Ajuste de brillo (solo canales RGB [0:3], no NIR [3])
        # Simula variaciones en condiciones de iluminación
        if random.random() > 0.5:
            factor = 0.9 + 0.2 * random.random()  # 0.9-1.1
            lr[:3] = np.clip(lr[:3] * factor, 0, 1)
            hr[:3] = np.clip(hr[:3] * factor, 0, 1)

        # Ruido gaussiano en LR (simulación de ruido de sensores)
        # Solo en imágenes LR, no en HR (el target debe ser limpio)
        if random.random() > 0.7:  # p=0.3
            noise = np.random.randn(*lr.shape).astype(np.float32) * 0.01
            lr = np.clip(lr + noise, 0, 1)

        return lr, hr


def create_satellite_dataloaders(
    lr_train_dir,
    hr_train_dir,
    lr_val_dir,
    hr_val_dir,
    batch_size=8,
    num_channels=4,
    num_workers=None,  # Auto-detect óptimo
    device=None,
):
    """
    Crea dataloaders para entrenamiento satelital

    Args:
        lr_train_dir, hr_train_dir: Directorios train
        lr_val_dir, hr_val_dir: Directorios val
        batch_size: Tamaño de batch
        num_channels: Canales (4 para RGB+NIR)
        num_workers: Workers para DataLoader (None = auto)
        device: Para determinar num_workers óptimo

    Returns:
        train_loader, val_loader
    """
    train_dataset = SatelliteSRDataset(
        lr_dir=lr_train_dir,
        hr_dir=hr_train_dir,
        augmentation=True,
        num_channels=num_channels,
    )

    val_dataset = SatelliteSRDataset(
        lr_dir=lr_val_dir,
        hr_dir=hr_val_dir,
        augmentation=False,  # Sin augmentation en validación
        num_channels=num_channels,
    )

    # num_workers óptimo según plataforma
    if num_workers is None:
        if device and device.type == "cuda":
            num_workers = 8  # Aumentado para mejor rendimiento en GPU
        elif device and device.type == "mps":
            num_workers = 0  # MPS tiene problemas con multiprocessing
        else:
            num_workers = 4

    # persistent_workers reduce overhead en CUDA
    use_persistent = device and device.type == "cuda" and num_workers > 0
    use_pin_memory = device and device.type == "cuda"

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=use_pin_memory,
        persistent_workers=use_persistent,
        prefetch_factor=2 if num_workers > 0 else None,  # Prefetch 2 batches por worker
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=1,  # Batch size 1 para validación
        shuffle=False,
        num_workers=num_workers,
        pin_memory=use_pin_memory,
        persistent_workers=use_persistent,
        prefetch_factor=2 if num_workers > 0 else None,
    )

    return train_loader, val_loader


# Test
if __name__ == "__main__":
    # Test con datos sintéticos
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        lr_dir = Path(tmpdir) / "LR"
        hr_dir = Path(tmpdir) / "HR"
        lr_dir.mkdir()
        hr_dir.mkdir()

        # Crear patches de prueba
        for i in range(5):
            lr_patch = np.random.rand(4, 64, 64).astype(np.float32)
            hr_patch = np.random.rand(4, 256, 256).astype(np.float32)

            np.save(lr_dir / f"patch_{i:04d}.npy", lr_patch)
            np.save(hr_dir / f"patch_{i:04d}.npy", hr_patch)

        # Test dataset
        dataset = SatelliteSRDataset(lr_dir, hr_dir)

        lr, hr = dataset[0]
        print(f"LR shape: {lr.shape}")  # [4, 64, 64]
        print(f"HR shape: {hr.shape}")  # [4, 256, 256]

        # Test dataloader
        loader = DataLoader(dataset, batch_size=2)
        lr_batch, hr_batch = next(iter(loader))

        print(f"LR batch shape: {lr_batch.shape}")  # [2, 4, 64, 64]
        print(f"HR batch shape: {hr_batch.shape}")  # [2, 4, 256, 256]

        print("✅ Satellite dataset test OK")
