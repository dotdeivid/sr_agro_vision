from pydantic import BaseModel
from typing import Dict, List, Optional
from enum import Enum


class IndexType(str, Enum):
    """Available vegetation indices"""
    NDVI = "ndvi"
    EVI = "evi"
    SAVI = "savi"
    NDWI = "ndwi"


class AnalysisRequest(BaseModel):
    """Request to analyze an image"""
    image_id: str
    index_type: IndexType = IndexType.NDVI


class HealthClass(str, Enum):
    """Vegetation health classification"""
    VERY_DENSE = "very_dense"
    DENSE = "dense"
    MODERATE = "moderate"
    SPARSE = "sparse"
    BARE_SOIL = "bare_soil"
    WATER = "water"


class AnalysisStats(BaseModel):
    """Statistics from analysis"""
    min_value: float
    max_value: float
    mean_value: float
    median_value: float
    std_dev: float
    pixel_count: int
    
    # Classification counts
    health_distribution: Dict[str, int]
    
    # Percentiles
    percentile_25: float
    percentile_75: float


class AnalysisResult(BaseModel):
    """Result of vegetation index analysis"""
    id: str
    image_id: str
    index_type: IndexType
    result_filepath: str  # Path to resulting GeoTIFF with index
    colormap_filepath: str  # Path to PNG visualization
    stats: AnalysisStats
    created_at: str
