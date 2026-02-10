"""
Utilidades para trabajar con imágenes Sentinel-2
"""

import numpy as np
from pathlib import Path
import rasterio
from rasterio.warp import reproject, Resampling


class Sentinel2Image:
    """Clase para manejar imágenes Sentinel-2"""

    # Bandas Sentinel-2 y sus resoluciones nativas
    BANDS_10M = ["B02", "B03", "B04", "B08"]  # Blue, Green, Red, NIR
    BANDS_20M = ["B05", "B06", "B07", "B8A", "B11", "B12"]
    BANDS_60M = ["B01", "B09", "B10"]

    def __init__(self, image_path):
        """
        Args:
            image_path: Ruta a directorio con bandas .jp2 o .tif
        """
        self.image_path = Path(image_path)
        self.bands_data = {}

    def load_band(self, band_name):
        """
        Carga una banda específica

        Args:
            band_name: 'B02', 'B03', etc.

        Returns:
            numpy array [H, W]
        """
        # Buscar archivo de banda (recursivamente en subdirectorios)
        band_files = list(self.image_path.glob(f"**/*{band_name}*.jp2"))
        if not band_files:
            band_files = list(self.image_path.glob(f"**/*{band_name}*.tif"))

        if not band_files:
            raise FileNotFoundError(
                f"Banda {band_name} no encontrada en {self.image_path}"
            )

        # Priorizar bandas de 10m (mejor resolución)
        # Si hay múltiples, elegir la de mayor resolución (10m > 20m > 60m)
        for resolution in ["10m", "20m", "60m"]:
            matching = [f for f in band_files if resolution in str(f)]
            if matching:
                band_files = [matching[0]]
                break

        with rasterio.open(band_files[0]) as src:
            band_data = src.read(1)
            self.bands_data[band_name] = band_data

        return band_data

    def load_rgb_nir(self):
        """
        Carga bandas RGB + NIR (las 4 principales para agricultura)

        Returns:
            numpy array [H, W, 4] con [R, G, B, NIR]
        """
        b04 = self.load_band("B04")  # Red
        b03 = self.load_band("B03")  # Green
        b02 = self.load_band("B02")  # Blue
        b08 = self.load_band("B08")  # NIR

        # Stack en orden [R, G, B, NIR]
        rgb_nir = np.stack([b04, b03, b02, b08], axis=-1)

        return rgb_nir

    def calculate_ndvi(self):
        """
        Calcula NDVI (Normalized Difference Vegetation Index)

        NDVI = (NIR - Red) / (NIR + Red)

        Returns:
            numpy array [H, W] con valores NDVI [-1, 1]
        """
        if "B04" not in self.bands_data:
            self.load_band("B04")
        if "B08" not in self.bands_data:
            self.load_band("B08")

        red = self.bands_data["B04"].astype(np.float32)
        nir = self.bands_data["B08"].astype(np.float32)

        # Evitar división por cero
        denominator = nir + red
        denominator[denominator == 0] = 1e-8

        ndvi = (nir - red) / denominator

        return ndvi

    def normalize_to_reflectance(self, band_data, quantification_value=10000):
        """
        Convierte valores digitales a reflectancia [0, 1]

        Args:
            band_data: Array con valores digitales
            quantification_value: Valor de cuantificación (10000 para Sentinel-2 L2A)

        Returns:
            Array normalizado [0, 1]
        """
        reflectance = band_data.astype(np.float32) / quantification_value
        reflectance = np.clip(reflectance, 0, 1)

        return reflectance

    @staticmethod
    def resample_band(band_data, target_shape, method="bilinear"):
        """
        Remuestrea banda a resolución objetivo

        Args:
            band_data: Array [H, W]
            target_shape: (H_target, W_target)
            method: 'bilinear', 'cubic', 'nearest'

        Returns:
            Array remuestreado
        """
        from scipy.ndimage import zoom

        zoom_factors = (
            target_shape[0] / band_data.shape[0],
            target_shape[1] / band_data.shape[1],
        )

        order_map = {"nearest": 0, "bilinear": 1, "cubic": 3}
        order = order_map.get(method, 1)

        resampled = zoom(band_data, zoom_factors, order=order)

        return resampled


def save_geotiff(array, output_path, reference_path=None, crs=None, transform=None):
    """
    Guarda array como GeoTIFF

    Args:
        array: numpy array [H, W] o [C, H, W]
        output_path: Ruta de salida
        reference_path: Path a GeoTIFF de referencia (para copiar metadatos)
        crs: Sistema de coordenadas (si no hay reference)
        transform: Transformación afín (si no hay reference)
    """
    if array.ndim == 2:
        array = array[np.newaxis, ...]  # Agregar dimensión de banda

    count, height, width = array.shape

    # Obtener metadatos de referencia
    if reference_path:
        with rasterio.open(reference_path) as ref:
            crs = ref.crs
            transform = ref.transform

    # Escribir GeoTIFF
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=count,
        dtype=array.dtype,
        crs=crs,
        transform=transform,
        compress="lzw",
    ) as dst:
        dst.write(array)


# Test
if __name__ == "__main__":
    # Ejemplo de uso
    print("Sentinel-2 utilities loaded")
    print(f"Bandas 10m: {Sentinel2Image.BANDS_10M}")
    print(f"Bandas 20m: {Sentinel2Image.BANDS_20M}")
