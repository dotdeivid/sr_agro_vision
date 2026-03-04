from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import logging
import uuid
from datetime import datetime

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.task import Task
from app.schemas.copernicus import (
    SatelliteSearchRequest,
    SatelliteSearchResponse,
    SatelliteDownloadRequest,
    SatelliteDownloadResponse,
)
from app.services.copernicus_service import copernicus_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/search", response_model=SatelliteSearchResponse)
async def search_satellite_images(
    request: SatelliteSearchRequest,
    current_user: User = Depends(get_current_active_user),
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
            max_results=request.max_results,
        )
        return results
    except Exception as e:
        logger.error(f"Error searching satellite images: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error searching satellite images: {str(e)}"
        )


@router.post("/download", response_model=SatelliteDownloadResponse)
async def download_satellite_image(
    request: SatelliteDownloadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Download a Sentinel-2 image, process it to RGBNIR format, and register
    it in the DB so it appears in the frontend via GET /api/v1/images/.
    """
    try:
        from app.tasks.processing_tasks import run_copernicus_download_and_process
        from app.core.config import settings
        from pathlib import Path

        task_id = str(uuid.uuid4())
        download_dir = Path(settings.DOWNLOAD_DIR)
        download_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(download_dir / f"temp_sentinel_{request.image_id}.zip")

        # Create Task record in DB
        db_task = Task(
            id=task_id,
            type="copernicus_download",
            status="queued",
            progress=0,
            user_id=current_user.id,
            config={
                "image_id": request.image_id,
                "output_path": output_path,
                "project_id": request.project_id,
            },
            created_at=datetime.utcnow(),
        )
        db.add(db_task)
        db.commit()

        # Dispatch Celery task
        run_copernicus_download_and_process.delay(
            task_id=task_id,
            image_id=request.image_id,
            output_path=output_path,
            user_id=current_user.id,
            project_id=request.project_id,
        )

        return {
            "task_id": task_id,
            "status": "queued",
            "message": (
                "Download and processing queued. "
                "Poll status via /api/v1/inference/status/{task_id}. "
                "When completed, the image will appear in /api/v1/images/."
            ),
        }
    except Exception as e:
        logger.error(f"Error initiating download: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error initiating download: {str(e)}"
        )


@router.get("/metadata/{image_id}")
async def get_image_metadata(
    image_id: str, current_user: User = Depends(get_current_active_user)
):
    """Get detailed metadata for a specific Sentinel-2 product from CDSE OData API"""
    try:
        metadata = copernicus_service.get_metadata(image_id)
        return metadata
    except Exception as e:
        logger.error(f"Error getting metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metadata: {str(e)}")
