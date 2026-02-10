"""
Cálculo de índices de vegetación
"""

import numpy as np


def calculate_ndvi(red, nir):
    """
    Normalized Difference Vegetation Index

    Args:
        red: Banda roja [H, W]
        nir: Banda NIR [H, W]

    Returns:
        NDVI [-1, 1], valores típicos vegetación sana: 0.2-0.8
    """
    red = red.astype(np.float32)
    nir = nir.astype(np.float32)

    denominator = nir + red
    denominator[denominator == 0] = 1e-8

    ndvi = (nir - red) / denominator

    return ndvi


def calculate_evi(red, nir, blue, G=2.5, C1=6, C2=7.5, L=1):
    """
    Enhanced Vegetation Index (más robusto que NDVI)

    Args:
        red, nir, blue: Bandas espectrales [H, W]
        G, C1, C2, L: Coeficientes estándar

    Returns:
        EVI [-1, 1]
    """
    red = red.astype(np.float32)
    nir = nir.astype(np.float32)
    blue = blue.astype(np.float32)

    denominator = nir + C1 * red - C2 * blue + L
    denominator[denominator == 0] = 1e-8

    evi = G * (nir - red) / denominator

    return evi


def calculate_savi(red, nir, L=0.5):
    """
    Soil-Adjusted Vegetation Index (útil para baja cobertura)

    Args:
        red, nir: Bandas espectrales [H, W]
        L: Factor de ajuste de suelo (0.5 para cobertura intermedia)

    Returns:
        SAVI
    """
    red = red.astype(np.float32)
    nir = nir.astype(np.float32)

    denominator = nir + red + L
    denominator[denominator == 0] = 1e-8

    savi = ((nir - red) / denominator) * (1 + L)

    return savi


def calculate_ndwi(green, nir):
    """
    Normalized Difference Water Index (detecta agua/humedad)

    Args:
        green: Banda verde [H, W]
        nir: Banda NIR [H, W]

    Returns:
        NDWI [-1, 1], valores altos = agua
    """
    green = green.astype(np.float32)
    nir = nir.astype(np.float32)

    denominator = green + nir
    denominator[denominator == 0] = 1e-8

    ndwi = (green - nir) / denominator

    return ndwi


def classify_vegetation_health(ndvi):
    """
    Clasifica salud de vegetación según NDVI

    Args:
        ndvi: Array NDVI [-1, 1]

    Returns:
        Array con clases: 0=sin_veg, 1=baja, 2=moderada, 3=alta
    """
    classes = np.zeros_like(ndvi, dtype=np.uint8)

    classes[ndvi < 0.2] = 0  # Sin vegetación / suelo desnudo
    classes[(ndvi >= 0.2) & (ndvi < 0.4)] = 1  # Baja
    classes[(ndvi >= 0.4) & (ndvi < 0.6)] = 2  # Moderada
    classes[ndvi >= 0.6] = 3  # Alta

    return classes


# Test
if __name__ == "__main__":
    # Test con datos sintéticos
    red = np.random.rand(100, 100) * 0.3
    nir = np.random.rand(100, 100) * 0.6
    blue = np.random.rand(100, 100) * 0.2
    green = np.random.rand(100, 100) * 0.4

    ndvi = calculate_ndvi(red, nir)
    evi = calculate_evi(red, nir, blue)
    savi = calculate_savi(red, nir)

    print(f"NDVI range: [{ndvi.min():.2f}, {ndvi.max():.2f}]")
    print(f"EVI range: [{evi.min():.2f}, {evi.max():.2f}]")
    print(f"SAVI range: [{savi.min():.2f}, {savi.max():.2f}]")
    print("✅ Vegetation indices test OK")
