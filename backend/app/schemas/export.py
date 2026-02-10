from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ExportFormat(str, Enum):
    """Available export formats"""
    GEOTIFF = "geotiff"
    PNG = "png"
    JPEG = "jpeg"
    KML = "kml"


class ExportRequest(BaseModel):
    """Request to export a result"""
    result_id: str
    format: ExportFormat = ExportFormat.PNG
    quality: int = 95  # For JPEG


class ExportResponse(BaseModel):
    """Response after export"""
    download_url: str
    filename: str
    file_size: int
    format: ExportFormat
