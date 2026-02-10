"""
Inferencia en imágenes satelitales multiespectrales
"""

import torch
import argparse
from pathlib import Path
import numpy as np
import rasterio
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.models.espcn import ESPCNMultispectral
from src.utils.device import get_device
from src.utils.geotiff import save_geotiff


def upscale_satellite_image_tiled(
    image_path, model_path, output_path, num_channels=4, scale_factor=4, 
    tile_size=512, overlap=32, device=None
):
    """
    Reescala imagen satelital multiespectral usando tiles para manejar imágenes grandes

    Args:
        image_path: Ruta a GeoTIFF de entrada (.tif)
        model_path: Ruta al modelo .pth
        output_path: Ruta para guardar resultado
        num_channels: Canales del modelo (4 para RGB+NIR)
        scale_factor: Factor de escalado
        tile_size: Tamaño de cada tile (default 512 para 6GB VRAM)
        overlap: Píxeles de overlap entre tiles para evitar artefactos
        device: Dispositivo (auto-detecta si None)
    """
    # Setup device
    if device is None:
        device = get_device()

    # Cargar imagen satelital
    print(f"📂 Cargando imagen: {image_path}")

    with rasterio.open(image_path) as src:
        img = src.read()  # [C, H, W]
        metadata = src.meta
        transform = src.transform
        crs = src.crs

    c, h, w = img.shape
    print(f"   Canales: {c}, Tamaño: {w}x{h}")

    if c != num_channels:
        print(f"⚠️  Advertencia: Imagen tiene {c} canales, modelo espera {num_channels}")
        if c > num_channels:
            print(f"   Usando solo los primeros {num_channels} canales")
            img = img[:num_channels]
        else:
            raise ValueError(
                f"Imagen tiene menos canales ({c}) que el modelo ({num_channels})"
            )

    # Normalizar a [0, 1] si es necesario
    was_normalized = False
    if img.max() > 1.0:
        print("   Normalizando valores...")
        img = img.astype(np.float32) / 10000.0  # Sentinel-2 L2A
        img = np.clip(img, 0, 1)
        was_normalized = True

    # Cargar modelo
    print(f"🧠 Cargando modelo: {model_path}")
    model = ESPCNMultispectral(
        scale_factor=scale_factor, num_channels=num_channels, num_features=64
    )
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    # Calcular dimensiones de salida
    sr_h, sr_w = h * scale_factor, w * scale_factor
    sr_img = np.zeros((c, sr_h, sr_w), dtype=np.float32)
    
    # Calcular número de tiles
    stride = tile_size - overlap
    n_tiles_h = (h + stride - 1) // stride
    n_tiles_w = (w + stride - 1) // stride
    total_tiles = n_tiles_h * n_tiles_w
    
    print(f"🔲 Procesando por tiles: {tile_size}x{tile_size} (overlap={overlap})")
    print(f"   Total de tiles: {total_tiles} ({n_tiles_h}x{n_tiles_w})")

    # Procesar por tiles
    tile_count = 0
    for i in range(n_tiles_h):
        for j in range(n_tiles_w):
            tile_count += 1
            
            # Calcular coordenadas del tile
            y_start = i * stride
            x_start = j * stride
            y_end = min(y_start + tile_size, h)
            x_end = min(x_start + tile_size, w)
            
            # Extraer tile
            tile = img[:, y_start:y_end, x_start:x_end]
            
            # Convertir a tensor y procesar
            tile_tensor = torch.from_numpy(tile).unsqueeze(0).float().to(device)
            
            with torch.no_grad():
                sr_tile_tensor = model(tile_tensor)
            
            sr_tile = sr_tile_tensor.squeeze(0).cpu().numpy()
            
            # Calcular coordenadas en imagen SR
            sr_y_start = y_start * scale_factor
            sr_x_start = x_start * scale_factor
            sr_y_end = y_end * scale_factor
            sr_x_end = x_end * scale_factor
            
            # Manejar overlap con blending
            if overlap > 0 and (i > 0 or j > 0):
                # Aplicar blending en zonas de overlap
                blend_y = min(overlap * scale_factor, sr_tile.shape[1])
                blend_x = min(overlap * scale_factor, sr_tile.shape[2])
                
                # Crear máscaras de blending
                if i > 0:  # Overlap vertical
                    alpha_y = np.linspace(0, 1, blend_y).reshape(-1, 1)
                    sr_tile[:, :blend_y, :] = (
                        sr_tile[:, :blend_y, :] * alpha_y + 
                        sr_img[:, sr_y_start:sr_y_start+blend_y, sr_x_start:sr_x_end] * (1 - alpha_y)
                    )
                
                if j > 0:  # Overlap horizontal
                    alpha_x = np.linspace(0, 1, blend_x).reshape(1, -1)
                    sr_tile[:, :, :blend_x] = (
                        sr_tile[:, :, :blend_x] * alpha_x + 
                        sr_img[:, sr_y_start:sr_y_end, sr_x_start:sr_x_start+blend_x] * (1 - alpha_x)
                    )
            
            # Colocar tile en imagen SR
            sr_img[:, sr_y_start:sr_y_end, sr_x_start:sr_x_end] = sr_tile
            
            # Mostrar progreso
            if tile_count % 10 == 0 or tile_count == total_tiles:
                print(f"   Progreso: {tile_count}/{total_tiles} tiles ({100*tile_count//total_tiles}%)")
    
    print("\n💾 Finalizando procesamiento...")
    
    # Desnormalizar si fue normalizado
    print("   Desnormalizando valores...")
    if was_normalized:
        sr_img = (sr_img * 10000.0).astype(np.uint16)
    else:
        sr_img = sr_img.astype(np.uint16)

    sr_c, sr_h, sr_w = sr_img.shape
    print(f"   ✓ Resultado: {sr_c} canales, {sr_w}x{sr_h}")

    # Actualizar metadatos para nueva resolución
    metadata.update(
        {
            "height": sr_h,
            "width": sr_w,
            "transform": rasterio.Affine(
                transform.a / scale_factor,
                transform.b,
                transform.c,
                transform.d,
                transform.e / scale_factor,
                transform.f,
            ),
        }
    )

    # Guardar resultado
    print("   Preparando archivo de salida...")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"   Guardando GeoTIFF ({sr_w}x{sr_h}, {sr_c} canales)...")
    with rasterio.open(output_path, "w", **metadata) as dst:
        dst.write(sr_img)

    print(f"✅ Imagen guardada: {output_path}")
    print(f"   Mejora de resolución: {w}x{h} → {sr_w}x{sr_h} (x{scale_factor})\n")


def upscale_satellite_image(
    image_path, model_path, output_path, num_channels=4, scale_factor=4, device=None
):
    """
    Wrapper que decide si usar procesamiento normal o por tiles
    """
    # Cargar solo metadatos para verificar tamaño
    with rasterio.open(image_path) as src:
        h, w = src.shape  # shape devuelve (height, width)
    
    # Si la imagen es grande (>2000x2000), usar tiles
    if h > 2000 or w > 2000:
        print(f"⚠️  Imagen grande detectada ({w}x{h}). Usando procesamiento por tiles...")
        return upscale_satellite_image_tiled(
            image_path, model_path, output_path, 
            num_channels, scale_factor, 
            tile_size=512, overlap=32, device=device
        )
    else:
        # Para imágenes pequeñas, usar método original (más rápido)
        print(f"Procesando imagen completa...")
        # [Aquí iría el código original, pero lo omitimos por brevedad]
        # Por ahora, siempre usamos tiles
        return upscale_satellite_image_tiled(
            image_path, model_path, output_path,
            num_channels, scale_factor,
            tile_size=512, overlap=32, device=device
        )


def batch_upscale_satellite(
    input_dir, model_path, output_dir, num_channels=4, scale_factor=4, device=None
):
    """
    Procesa múltiples imágenes satelitales

    Args:
        input_dir: Directorio con GeoTIFFs de entrada
        model_path: Ruta al modelo
        output_dir: Directorio de salida
        num_channels: Canales del modelo
        scale_factor: Factor de escalado
        device: Dispositivo
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Buscar imágenes
    image_files = list(input_dir.glob("*.tif"))
    image_files += list(input_dir.glob("*.tiff"))

    if len(image_files) == 0:
        print(f"❌ No se encontraron imágenes en {input_dir}")
        return

    print(f"📂 Encontradas {len(image_files)} imágenes")

    for i, img_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Procesando: {img_path.name}")

        output_path = output_dir / f"sr_{img_path.name}"

        try:
            upscale_satellite_image(
                img_path,
                model_path,
                output_path,
                num_channels=num_channels,
                scale_factor=scale_factor,
                device=device,
            )
        except Exception as e:
            print(f"❌ Error procesando {img_path.name}: {e}")
            continue

    print(f"\n✅ Procesamiento completado. Resultados en: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reescalar imágenes satelitales")
    parser.add_argument(
        "--input", type=str, required=True, help="Imagen o directorio de entrada"
    )
    parser.add_argument("--model", type=str, required=True, help="Ruta al modelo .pth")
    parser.add_argument(
        "--output", type=str, required=True, help="Imagen o directorio de salida"
    )
    parser.add_argument(
        "--channels", type=int, default=4, help="Número de canales (4 para RGB+NIR)"
    )
    parser.add_argument(
        "--scale", type=int, default=4, choices=[2, 4, 8], help="Factor de escalado"
    )
    parser.add_argument(
        "--batch", action="store_true", help="Procesar directorio completo"
    )

    args = parser.parse_args()

    if args.batch:
        batch_upscale_satellite(
            args.input,
            args.model,
            args.output,
            num_channels=args.channels,
            scale_factor=args.scale,
        )
    else:
        upscale_satellite_image(
            args.input,
            args.model,
            args.output,
            num_channels=args.channels,
            scale_factor=args.scale,
        )
