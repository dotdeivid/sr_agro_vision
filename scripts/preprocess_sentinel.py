"""
Preprocesamiento de imágenes Sentinel-2
"""

import numpy as np
from pathlib import Path
import sys
import zipfile

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.geotiff import Sentinel2Image, save_geotiff
from src.utils.ndvi import calculate_ndvi
from tqdm import tqdm


def extract_safe_zip(zip_path, output_dir=None):
    """
    Extrae archivo .SAFE.zip

    Args:
        zip_path: Path al archivo .SAFE.zip
        output_dir: Directorio de salida (default: mismo directorio que el zip)

    Returns:
        Path al directorio .SAFE extraído
    """
    zip_path = Path(zip_path)

    if output_dir is None:
        output_dir = zip_path.parent
    else:
        output_dir = Path(output_dir)

    # Nombre del directorio .SAFE (sin .zip)
    safe_name = zip_path.name.replace(".zip", "")
    safe_dir = output_dir / safe_name

    # Si ya existe, no extraer de nuevo
    if safe_dir.exists():
        print(f"✓ Ya extraído: {safe_name}")
        return safe_dir

    print(f"📦 Extrayendo: {safe_name}")

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)
        print(f"✅ Extraído: {safe_name}")
        return safe_dir
    except Exception as e:
        print(f"❌ Error extrayendo {zip_path}: {e}")
        return None


def filter_clouds(image_path, cloud_threshold=0.3):
    """
    Filtra imágenes con mucha nubosidad

    Args:
        image_path: Path a imagen Sentinel-2
        cloud_threshold: Umbral de nubosidad (0-1)

    Returns:
        bool: True si la imagen es válida
    """
    # Sentinel-2 Level-2A incluye máscara de nubes
    cloud_mask_files = list(Path(image_path).glob("**/MSK_CLDPRB_20m.jp2"))

    if not cloud_mask_files:
        print(f"⚠️  Máscara de nubes no encontrada en {image_path}")
        return True  # Asumir válida si no hay máscara

    import rasterio

    with rasterio.open(cloud_mask_files[0]) as src:
        cloud_prob = src.read(1)

    # Porcentaje de píxeles con probabilidad > 50% de ser nube
    cloud_percentage = np.sum(cloud_prob > 50) / cloud_prob.size

    is_valid = cloud_percentage < cloud_threshold

    if not is_valid:
        print(f"❌ Imagen rechazada: {cloud_percentage*100:.1f}% nubes")

    return is_valid


def preprocess_image(image_path, output_dir, target_bands=["B04", "B03", "B02", "B08"]):
    """
    Preprocesa imagen Sentinel-2

    Pasos:
    1. Cargar bandas especificadas
    2. Normalizar a reflectancia [0, 1]
    3. Recortar a área común
    4. Guardar como GeoTIFF de 4 canales

    Args:
        image_path: Path a directorio .SAFE
        output_dir: Directorio de salida
        target_bands: Bandas a extraer (default: RGB + NIR)

    Returns:
        Path al archivo procesado o None si falla
    """
    try:
        sentinel_img = Sentinel2Image(image_path)

        # Cargar bandas RGB + NIR
        rgb_nir = sentinel_img.load_rgb_nir()

        # Normalizar a reflectancia
        rgb_nir_norm = sentinel_img.normalize_to_reflectance(rgb_nir)

        # Obtener metadatos
        image_name = Path(image_path).name.split(".")[0]
        output_path = Path(output_dir) / f"{image_name}_RGBNIR.tif"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Guardar como GeoTIFF [C, H, W]
        rgb_nir_transposed = rgb_nir_norm.transpose(2, 0, 1)

        # Obtener referencia geográfica de una banda (buscar recursivamente)
        reference_bands = list(Path(image_path).glob("**/IMG_DATA/**/*B04*10m.jp2"))
        if not reference_bands:
            # Intentar con cualquier B04
            reference_bands = list(Path(image_path).glob("**/IMG_DATA/**/*B04*.jp2"))

        if not reference_bands:
            raise FileNotFoundError(
                f"No se encontró banda de referencia B04 en {image_path}"
            )

        reference_band = reference_bands[0]

        save_geotiff(rgb_nir_transposed, output_path, reference_path=reference_band)

        print(f"✅ Procesada: {output_path.name}")
        print(f"   Shape: {rgb_nir_transposed.shape}")

        return output_path

    except Exception as e:
        print(f"❌ Error procesando {image_path}: {e}")
        return None


def batch_preprocess(input_dir, output_dir, filter_by_clouds=True, cloud_threshold=0.2):
    """
    Preprocesa múltiples imágenes Sentinel-2

    Args:
        input_dir: Directorio con imágenes .SAFE descargadas
        output_dir: Directorio de salida
        filter_by_clouds: Filtrar imágenes nubladas
        cloud_threshold: Umbral de nubosidad
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Primero, extraer archivos .SAFE.zip si existen
    zip_files = list(input_dir.glob("*.SAFE.zip"))

    if zip_files:
        print(f"📦 Encontrados {len(zip_files)} archivos ZIP")
        print(f"🔓 Extrayendo archivos...")
        for zip_file in tqdm(zip_files, desc="Extrayendo"):
            extract_safe_zip(zip_file, input_dir)
        print()

    # Buscar directorios .SAFE
    safe_dirs = list(input_dir.glob("*.SAFE"))

    if len(safe_dirs) == 0:
        print(f"⚠️  No se encontraron imágenes .SAFE en {input_dir}")
        print(
            f"💡 Tip: Verifica que los archivos .SAFE.zip se hayan extraído correctamente"
        )
        return

    print(f"📂 Encontradas {len(safe_dirs)} imágenes")
    print(f"🔍 Preprocesando...")

    processed = []
    skipped = []

    for safe_dir in tqdm(safe_dirs, desc="Procesando"):
        # Filtrar nubes
        if filter_by_clouds and not filter_clouds(safe_dir, cloud_threshold):
            skipped.append(safe_dir.name)
            continue

        # Preprocesar
        output_path = preprocess_image(safe_dir, output_dir)

        if output_path:
            processed.append(output_path)
        else:
            skipped.append(safe_dir.name)

    print(f"\n{'='*60}")
    print(f"✅ Procesadas: {len(processed)} imágenes")
    print(f"⏭️  Omitidas: {len(skipped)} imágenes")
    print(f"📁 Salida: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocesar imágenes Sentinel-2")
    parser.add_argument(
        "--input", type=str, required=True, help="Directorio con imágenes .SAFE"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Directorio de salida"
    )
    parser.add_argument(
        "--cloud-threshold", type=float, default=0.2, help="Umbral de nubosidad (0-1)"
    )
    parser.add_argument(
        "--no-filter-clouds", action="store_true", help="No filtrar por nubes"
    )

    args = parser.parse_args()

    batch_preprocess(
        args.input,
        args.output,
        filter_by_clouds=not args.no_filter_clouds,
        cloud_threshold=args.cloud_threshold,
    )
