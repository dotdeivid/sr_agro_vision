import numpy as np
import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
from typing import Dict, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class NDVIService:
    """Service for calculating vegetation indices"""
    
    @staticmethod
    def calculate_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
        """
        Calculate NDVI
        NDVI = (NIR - Red) / (NIR + Red)
        """
        # Avoid division by zero
        denominator = nir + red
        denominator[denominator == 0] = 0.0001
        
        ndvi = (nir - red) / denominator
        
        # Clip to valid range [-1, 1]
        ndvi = np.clip(ndvi, -1, 1)
        
        return ndvi
    
    @staticmethod
    def calculate_evi(nir: np.ndarray, red: np.ndarray, blue: np.ndarray) -> np.ndarray:
        """
        Calculate EVI
        EVI = 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))
        """
        denominator = nir + 6 * red - 7.5 * blue + 1
        denominator[denominator == 0] = 0.0001
        
        evi = 2.5 * ((nir - red) / denominator)
        
        # Clip to valid range [-1, 1]
        evi = np.clip(evi, -1, 1)
        
        return evi
    
    @staticmethod
    def calculate_savi(nir: np.ndarray, red: np.ndarray, L: float = 0.5) -> np.ndarray:
        """
        Calculate SAVI
        SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)
        """
        denominator = nir + red + L
        denominator[denominator == 0] = 0.0001
        
        savi = ((nir - red) / denominator) * (1 + L)
        
        # Clip to valid range [-1, 1]
        savi = np.clip(savi, -1, 1)
        
        return savi
    
    @staticmethod
    def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Calculate NDWI
        NDWI = (Green - NIR) / (Green + NIR)
        """
        denominator = green + nir
        denominator[denominator == 0] = 0.0001
        
        ndwi = (green - nir) / denominator
        
        # Clip to valid range [-1, 1]
        ndwi = np.clip(ndwi, -1, 1)
        
        return ndwi
    
    @staticmethod
    def classify_vegetation(index_values: np.ndarray, index_type: str) -> Dict[str, int]:
        """
        Classify vegetation health based on index values
        
        NDVI classification:
        > 0.6: Very dense vegetation
        0.4-0.6: Dense vegetation
        0.2-0.4: Moderate vegetation
        0.0-0.2: Sparse vegetation
        < 0: Water/bare soil
        """
        classification = {
            "very_dense": 0,
            "dense": 0,
            "moderate": 0,
            "sparse": 0,
            "bare_soil": 0,
            "water": 0
        }
        
        # Flatten array and remove NaN
        values = index_values.flatten()
        values = values[~np.isnan(values)]
        
        if index_type in ["ndvi", "evi", "savi"]:
            classification["very_dense"] = int(np.sum(values > 0.6))
            classification["dense"] = int(np.sum((values > 0.4) & (values <= 0.6)))
            classification["moderate"] = int(np.sum((values > 0.2) & (values <= 0.4)))
            classification["sparse"] = int(np.sum((values > 0.0) & (values <= 0.2)))
            classification["bare_soil"] = int(np.sum((values >= -0.2) & (values <= 0.0)))
            classification["water"] = int(np.sum(values < -0.2))
        else:  # NDWI
            classification["water"] = int(np.sum(values > 0.3))
            classification["moderate"] = int(np.sum((values > 0.0) & (values <= 0.3)))
            classification["sparse"] = int(np.sum((values > -0.3) & (values <= 0.0)))
            classification["bare_soil"] = int(np.sum(values <= -0.3))
        
        return classification
    
    @staticmethod
    def calculate_statistics(index_values: np.ndarray, index_type: str) -> Dict:
        """Calculate statistics from index values"""
        # Flatten and remove NaN
        values = index_values.flatten()
        values = values[~np.isnan(values)]
        
        if len(values) == 0:
            return {
                "min_value": 0.0,
                "max_value": 0.0,
                "mean_value": 0.0,
                "median_value": 0.0,
                "std_dev": 0.0,
                "pixel_count": 0,
                "health_distribution": {},
                "percentile_25": 0.0,
                "percentile_75": 0.0
            }
        
        health_dist = NDVIService.classify_vegetation(index_values, index_type)
        
        return {
            "min_value": float(np.min(values)),
            "max_value": float(np.max(values)),
            "mean_value": float(np.mean(values)),
            "median_value": float(np.median(values)),
            "std_dev": float(np.std(values)),
            "pixel_count": int(len(values)),
            "health_distribution": health_dist,
            "percentile_25": float(np.percentile(values, 25)),
            "percentile_75": float(np.percentile(values, 75))
        }
    
    @staticmethod
    def save_colormap_image(
        index_values: np.ndarray,
        output_path: str,
        index_type: str,
        cmap: str = 'RdYlGn'
    ) -> str:
        """
        Save index as PNG with colormap
        """
        plt.figure(figsize=(10, 10))
        plt.imshow(index_values, cmap=cmap, vmin=-1, vmax=1)
        plt.colorbar(label=index_type.upper())
        plt.title(f'{index_type.upper()} Analysis')
        plt.axis('off')
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    @staticmethod
    def process_image(
        image_path: str,
        index_type: str,
        output_dir: str
    ) -> Tuple[str, str, Dict]:
        """
        Process image and calculate vegetation index
        
        Args:
            image_path: Path to input GeoTIFF
            index_type: Type of index (ndvi, evi, savi, ndwi)
            output_dir: Directory to save results
        
        Returns:
            Tuple of (result_tiff_path, colormap_png_path, statistics)
        """
        # Read image
        with rasterio.open(image_path) as src:
            # Assume bands in order: B, G, R, NIR (common for Sentinel-2 subsets)
            # Adjust based on actual band order
            blue = src.read(1).astype(float)
            green = src.read(2).astype(float)
            red = src.read(3).astype(float)
            nir = src.read(4).astype(float) if src.count >= 4 else None
            
            # Normalize to 0-1 if needed
            if np.max(blue) > 1:
                blue = blue / 10000.0
                green = green / 10000.0
                red = red / 10000.0
                if nir is not None:
                    nir = nir / 10000.0
            
            # Calculate index
            if index_type == "ndvi":
                if nir is None:
                    raise ValueError("NIR band required for NDVI")
                index_values = NDVIService.calculate_ndvi(nir, red)
            elif index_type == "evi":
                if nir is None:
                    raise ValueError("NIR band required for EVI")
                index_values = NDVIService.calculate_evi(nir, red, blue)
            elif index_type == "savi":
                if nir is None:
                    raise ValueError("NIR band required for SAVI")
                index_values = NDVIService.calculate_savi(nir, red)
            elif index_type == "ndwi":
                if nir is None:
                    raise ValueError("NIR band required for NDWI")
                index_values = NDVIService.calculate_ndwi(green, nir)
            else:
                raise ValueError(f"Unknown index type: {index_type}")
            
            # Calculate statistics
            stats = NDVIService.calculate_statistics(index_values, index_type)
            
            # Save as GeoTIFF
            output_tiff = str(Path(output_dir) / f"{index_type}_result.tif")
            profile = src.profile.copy()
            profile.update(
                count=1,
                dtype=rasterio.float32,
                nodata=-9999
            )
            
            with rasterio.open(output_tiff, 'w', **profile) as dst:
                dst.write(index_values.astype(rasterio.float32), 1)
            
            # Save colormap PNG
            output_png = str(Path(output_dir) / f"{index_type}_colormap.png")
            cmap = 'RdYlGn' if index_type != 'ndwi' else 'Blues'
            NDVIService.save_colormap_image(index_values, output_png, index_type, cmap)
            
            return output_tiff, output_png, stats


ndvi_service = NDVIService()
