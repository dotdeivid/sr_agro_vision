from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.copernicus import (
    SatelliteSearchRequest,
    SatelliteSearchResponse,
    SatelliteDownloadRequest,
    SatelliteDownloadResponse
)
from app.services.copernicus_service import copernicus_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search", response_model=SatelliteSearchResponse)
async def search_satellite_images(
    request: SatelliteSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for Sentinel-2 images
    
    - **bbox**: Bounding box [lon_min, lat_min, lon_max, lat_max]
    - **start_date**: Start date (YYYY-MM-DD)
    - **end_date**: End date (YYYY-MM-DD)
    - **max_cloud_cover**: Maximum cloud cover percentage (0-100)
    - **max_results**: Maximum number of results (1-100)
    """
    try:
        results = copernicus_service.search_images(
            bbox=request.bbox,
            start_date=request.start_date,
            end_date=request.end_date,
            max_cloud_cover=request.max_cloud_cover,
            max_results=request.max_results
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching satellite images: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching satellite images: {str(e)}"
        )


@router.post("/download", response_model=SatelliteDownloadResponse)
async def download_satellite_image(
    request: SatelliteDownloadRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a Sentinel-2 image
    
    This initiates a background download task.
    Use the returned task_id to check download status.
    """
    try:
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # TODO: Implement background task for download
        # For now, return task initiated
        
        return {
            "task_id": task_id,
            "status": "queued",
            "message": "Download task initiated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error initiating download: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error initiating download: {str(e)}"
        )


@router.get("/metadata/{image_id}")
async def get_image_metadata(
    image_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed metadata for a specific image"""
    try:
        # TODO: Implement metadata retrieval
        return {
            "id": image_id,
            "message": "Metadata retrieval not yet implemented"
        }
    except Exception as e:
        logger.error(f"Error getting metadata: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting metadata: {str(e)}"
        )
