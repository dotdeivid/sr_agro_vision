"""
Genera pares de imágenes LR-HR para entrenamiento
Soporta GeoTIFF (Sentinel-2) y PNG/JPG (DIV2K)
"""

import numpy as np
from pathlib import Path
from PIL import Image
import rasterio
from tqdm import tqdm
import sys

# Corregir sys.path para que encuentre 'src' en Colab y local
# Colab: /content/colab_training/scripts/.. = /content/colab_training/
# Local: ~/proyecto/scripts/.. = ~/proyecto/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.geotiff import save_geotiff


def create_lr_from_hr(hr_image, scale_factor=4, method="bicubic"):
    """
    Crea versión LR desde HR mediante downsampling

    Args:
        hr_image: Array [C, H, W] o [H, W, C]
        scale_factor: Factor de reducción (2, 4, 8)
        method: 'bicubic', 'bilinear', 'nearest'

    Returns:
        lr_image: Array con mismas dimensiones pero menor resolución
    """
    # Determinar si es [C, H, W] o [H, W, C]
    if hr_image.shape[0] in [1, 3, 4, 6, 10]:  # Probablemente [C, H, W]
        is_channels_first = True
        c, h, w = hr_image.shape
        hr_image_hwc = hr_image.transpose(1, 2, 0)  # [H, W, C]
    else:
        is_channels_first = False
        h, w, c = hr_image.shape
        hr_image_hwc = hr_image

    # Nuevo tamaño
    lr_h, lr_w = h // scale_factor, w // scale_factor

    # Downsample cada canal
    lr_channels = []
    for i in range(c):
        channel = hr_image_hwc[:, :, i]

        # Convertir a PIL para resize
        channel_uint16 = (channel * 65535).astype(np.uint16)
        pil_img = Image.fromarray(channel_uint16, mode="I;16")

        # Resize
        resample_map = {
            "bicubic": Image.BICUBIC,
            "bilinear": Image.BILINEAR,
            "nearest": Image.NEAREST,
        }
        pil_lr = pil_img.resize((lr_w, lr_h), resample_map.get(method, Image.BICUBIC))

        # De vuelta a array normalizado
        lr_channel = np.array(pil_lr).astype(np.float32) / 65535.0
        lr_channels.append(lr_channel)

    lr_image_hwc = np.stack(lr_channels, axis=-1)

    # Volver al formato original
    if is_channels_first:
        lr_image = lr_image_hwc.transpose(2, 0, 1)  # [C, H, W]
    else:
        lr_image = lr_image_hwc

    return lr_image


def create_patches(image, patch_size=256, stride=128, min_patch_size=None):
    """
    Divide imagen en patches para entrenamiento

    Args:
        image: Array [C, H, W]
        patch_size: Tamaño de patch (debe ser múltiplo del scale_factor)
        stride: Paso entre patches (overlap si stride < patch_size)
        min_patch_size: Tamaño mínimo aceptable (default: patch_size)

    Returns:
        List of patches [C, patch_size, patch_size]
    """
    c, h, w = image.shape
    patches = []

    if min_patch_size is None:
        min_patch_size = patch_size

    # La imagen es demasiado pequeña para extraer ningún patch
    if h < min_patch_size or w < min_patch_size:
        return patches

    for i in range(0, h - patch_size + 1, stride):
        for j in range(0, w - patch_size + 1, stride):
            patch = image[:, i : i + patch_size, j : j + patch_size]

            # Verificar que el patch no tenga muchos valores nulos
            if np.sum(patch == 0) / patch.size < 0.1:  # <10% píxeles nulos
                patches.append(patch)

    return patches


def process_image_to_pairs(
    hr_image_path, output_dir, scale_factor=4, patch_size=256, stride=128
):
    """
    Procesa una imagen HR: crea LR, extrae patches, guarda pares
    Soporta GeoTIFF (.tif) y PNG/JPG (.png, .jpg)

    Args:
        hr_image_path: Path a imagen HR (GeoTIFF, PNG o JPG)
        output_dir: Directorio de salida
        scale_factor: Factor de reducción
        patch_size: Tamaño de patches HR
        stride: Paso entre patches

    Returns:
        Number of patches created
    """
    hr_image_path = Path(hr_image_path)
    output_dir = Path(output_dir)

    lr_dir = output_dir / "LR"
    hr_dir = output_dir / "HR"
    lr_dir.mkdir(parents=True, exist_ok=True)
    hr_dir.mkdir(parents=True, exist_ok=True)

    # Cargar imagen según el tipo de archivo
    if hr_image_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
        # Para PNG/JPG (DIV2K y datasets genéricos)
        hr_pil = Image.open(hr_image_path).convert("RGB")
        hr_image = np.array(hr_pil).astype(np.float32) / 255.0  # [H, W, C]
        hr_image = hr_image.transpose(2, 0, 1)  # Convertir a [C, H, W]
    else:
        # Para GeoTIFF (Sentinel-2)
        with rasterio.open(hr_image_path) as src:
            hr_image = src.read()  # [C, H, W]

        # Normalizar si es necesario
        if hr_image.max() > 1.0:
            hr_image = hr_image.astype(np.float32) / 10000.0  # Sentinel-2 L2A
            hr_image = np.clip(hr_image, 0, 1)

    # Verificar que la imagen sea lo suficientemente grande
    _, h, w = hr_image.shape
    if h < patch_size or w < patch_size:
        print(
            f"⚠️  Imagen muy pequeña ({h}×{w}px < {patch_size}px), saltando: {hr_image_path.name}"
        )
        return 0

    # Crear versión LR
    lr_image = create_lr_from_hr(hr_image, scale_factor=scale_factor)

    # Extraer patches HR
    hr_patches = create_patches(hr_image, patch_size=patch_size, stride=stride)

    if len(hr_patches) == 0:
        print(f"⚠️  No se pudieron extraer patches de {hr_image_path.name}")
        return 0

    # Extraer patches LR correspondientes
    lr_patch_size = patch_size // scale_factor
    lr_stride = max(
        1, stride // scale_factor
    )  # Evitar stride=0 si stride < scale_factor
    lr_patches = create_patches(lr_image, patch_size=lr_patch_size, stride=lr_stride)

    # Asegurar mismo número de patches
    num_patches = min(len(hr_patches), len(lr_patches))

    # Guardar patches
    image_name = hr_image_path.stem

    for i in range(num_patches):
        patch_id = f"{image_name}_patch_{i:04d}"

        # Guardar HR patch
        hr_patch_path = hr_dir / f"{patch_id}.npy"
        np.save(hr_patch_path, hr_patches[i])

        # Guardar LR patch
        lr_patch_path = lr_dir / f"{patch_id}.npy"
        np.save(lr_patch_path, lr_patches[i])

    return num_patches


def batch_create_pairs(
    input_dir, output_dir, scale_factor=4, patch_size=256, stride=128, train_split=0.8
):
    """
    Procesa múltiples imágenes y crea dataset train/val

    Args:
        input_dir: Directorio con imágenes (GeoTIFF, PNG o JPG)
        output_dir: Directorio de salida
        scale_factor: Factor de escalado
        patch_size: Tamaño de patches HR
        stride: Paso entre patches
        train_split: Proporción de train (0.8 = 80% train, 20% val)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Buscar imágenes (GeoTIFF, PNG, JPG)
    image_files = list(input_dir.glob("*.tif"))

    if len(image_files) == 0:
        image_files = list(input_dir.glob("*.png"))

    if len(image_files) == 0:
        image_files = list(input_dir.glob("*.jpg"))

    if len(image_files) == 0:
        image_files = list(input_dir.glob("*.jpeg"))

    if len(image_files) == 0:
        print(f"❌ No se encontraron imágenes (.tif, .png, .jpg) en {input_dir}")
        return

    print(f"📂 Encontradas {len(image_files)} imágenes")
    print(f"🔪 Extrayendo patches (size={patch_size}, stride={stride})...")

    all_patches_info = []

    for img_path in tqdm(image_files, desc="Procesando imágenes"):
        num_patches = process_image_to_pairs(
            img_path,
            output_dir / "temp",
            scale_factor=scale_factor,
            patch_size=patch_size,
            stride=stride,
        )

        all_patches_info.append({"image": img_path.name, "patches": num_patches})

    # Listar todos los patches creados
    temp_lr_dir = output_dir / "temp" / "LR"
    temp_hr_dir = output_dir / "temp" / "HR"

    all_lr_patches = sorted(list(temp_lr_dir.glob("*.npy")))
    all_hr_patches = sorted(list(temp_hr_dir.glob("*.npy")))

    total_patches = len(all_lr_patches)

    if total_patches == 0:
        print("❌ No se crearon patches")
        return

    print(f"✅ Total patches extraídos: {total_patches}")

    # Split train/val
    split_idx = int(total_patches * train_split)

    train_lr_patches = all_lr_patches[:split_idx]
    train_hr_patches = all_hr_patches[:split_idx]
    val_lr_patches = all_lr_patches[split_idx:]
    val_hr_patches = all_hr_patches[split_idx:]

    print(f"📊 Split: {len(train_lr_patches)} train, {len(val_lr_patches)} val")

    # Crear directorios finales
    train_lr_dir = output_dir / "train" / "LR"
    train_hr_dir = output_dir / "train" / "HR"
    val_lr_dir = output_dir / "val" / "LR"
    val_hr_dir = output_dir / "val" / "HR"

    for d in [train_lr_dir, train_hr_dir, val_lr_dir, val_hr_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Mover patches a train/val (usar rename en vez de copy - más eficiente)
    print("📦 Organizando dataset...")

    for src, dst_dir in zip(train_lr_patches, [train_lr_dir] * len(train_lr_patches)):
        src.rename(dst_dir / src.name)

    for src, dst_dir in zip(train_hr_patches, [train_hr_dir] * len(train_hr_patches)):
        src.rename(dst_dir / src.name)

    for src, dst_dir in zip(val_lr_patches, [val_lr_dir] * len(val_lr_patches)):
        src.rename(dst_dir / src.name)

    for src, dst_dir in zip(val_hr_patches, [val_hr_dir] * len(val_hr_patches)):
        src.rename(dst_dir / src.name)

    # Limpiar directorio temporal
    import shutil

    shutil.rmtree(output_dir / "temp")

    # Resumen
    print(f"\n{'='*60}")
    print("DATASET CREADO")
    print(f"{'='*60}")
    print(f"Imágenes procesadas: {len(image_files)}")
    print(f"Total patches: {total_patches}")
    print(f"Train patches: {len(train_lr_patches)}")
    print(f"Val patches: {len(val_lr_patches)}")
    print(f"\nDirectorios:")
    print(f"  Train LR: {train_lr_dir}")
    print(f"  Train HR: {train_hr_dir}")
    print(f"  Val LR: {val_lr_dir}")
    print(f"  Val HR: {val_hr_dir}")
    print(f"{'='*60}")

    # Guardar info del dataset
    import json

    dataset_info = {
        "total_images": len(image_files),
        "total_patches": total_patches,
        "train_patches": len(train_lr_patches),
        "val_patches": len(val_lr_patches),
        "scale_factor": scale_factor,
        "patch_size": patch_size,
        "stride": stride,
        "images_info": all_patches_info,
    }

    with open(output_dir / "dataset_info.json", "w") as f:
        json.dump(dataset_info, f, indent=2)


def main(args=None):
    """
    Función main para ser llamada desde main.py o directamente

    Args:
        args: Argumentos parseados (opcional, si None se parsean desde consola)
    """
    import argparse

    if args is None:
        # Si se llama directamente desde consola, parsear argumentos
        parser = argparse.ArgumentParser(
            description="Crear pares LR-HR para entrenamiento"
        )
        parser.add_argument(
            "--input",
            type=str,
            required=True,
            help="Directorio con imágenes (GeoTIFF, PNG o JPG)",
        )
        parser.add_argument(
            "--output", type=str, required=True, help="Directorio de salida"
        )
        parser.add_argument(
            "--scale", type=int, default=4, choices=[2, 4, 8], help="Factor de escalado"
        )
        parser.add_argument(
            "--patch-size", type=int, default=256, help="Tamaño de patches HR"
        )
        parser.add_argument(
            "--stride", type=int, default=128, help="Paso entre patches"
        )
        parser.add_argument(
            "--train-split",
            type=float,
            default=0.8,
            help="Proporción de train (0.8 = 80%)",
        )

        args = parser.parse_args()

    # Ejecutar función principal
    batch_create_pairs(
        input_dir=args.input,
        output_dir=args.output,
        scale_factor=args.scale,
        patch_size=args.patch_size,
        stride=args.stride,
        train_split=args.train_split,
    )


if __name__ == "__main__":
    main()
