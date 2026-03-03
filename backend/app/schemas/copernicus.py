from pydantic import BaseModel, Field
from typing import Optional, List


class SatelliteSearchRequest(BaseModel):
    """Request for searching Sentinel-2 images"""

    bbox: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box [lon_min, lat_min, lon_max, lat_max]",
    )
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    max_cloud_cover: int = Field(
        20, ge=0, le=100, description="Maximum cloud cover percentage"
    )
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of results")


class SatelliteImage(BaseModel):
    """Sentinel-2 image metadata"""

    id: str
    title: str
    product_type: str
    platform: str
    # Use str instead of datetime — the CDSE API returns ISO strings that may
    # be empty or have non-standard formats, causing ValidationError with datetime.
    sensing_time: Optional[str] = None
    cloud_cover: float
    footprint: str  # WKT polygon
    thumbnail_url: str
    download_url: str
    size_mb: float
    bands_available: List[str]


class SatelliteSearchResponse(BaseModel):
    """Response from satellite search"""

    total_results: int
    images: List[SatelliteImage]


class SatelliteDownloadRequest(BaseModel):
    """Request to download a Sentinel-2 image"""

    image_id: str
    bands: Optional[List[str]] = None  # If None, download all
    project_id: str = "default"


class SatelliteDownloadResponse(BaseModel):
    """Response after initiating download"""

    task_id: str
    status: str
    message: str
