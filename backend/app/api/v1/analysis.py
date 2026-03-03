from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from datetime import datetime

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.image import Image
from app.models.analysis_result import AnalysisResult
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult as AnalysisResultSchema,
    AnalysisStats,
    IndexType,
)
from app.services.ndvi_service import ndvi_service

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResultSchema)
async def analyze_image(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Analyze an image and calculate vegetation index

    - **image_id**: ID of the image to analyze
    - **index_type**: Type of index (ndvi, evi, savi, ndwi)
    """
    try:
        # Get image
        image = db.query(Image).filter(Image.id == request.image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        # Create output directory
        result_id = str(uuid.uuid4())
        from app.core.config import settings

        output_dir = (Path(settings.UPLOAD_DIR) / "analysis") / result_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Process image
        result_tiff, colormap_png, stats = ndvi_service.process_image(
            image_path=image.filepath,
            index_type=request.index_type,
            output_dir=str(output_dir),
        )

        # Save result to database
        db_result = AnalysisResult(
            id=result_id,
            image_id=request.image_id,
            index_type=(
                request.index_type.value
                if hasattr(request.index_type, "value")
                else request.index_type
            ),
            result_filepath=result_tiff,
            colormap_filepath=colormap_png,
            stats=(
                stats
                if isinstance(stats, dict)
                else stats.dict() if hasattr(stats, "dict") else {}
            ),
            created_at=datetime.utcnow(),
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)

        return {
            "id": db_result.id,
            "image_id": db_result.image_id,
            "index_type": db_result.index_type,
            "result_filepath": db_result.result_filepath,
            "colormap_filepath": db_result.colormap_filepath,
            "stats": db_result.stats,
            "created_at": db_result.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")


@router.get("/results/{result_id}", response_model=AnalysisResultSchema)
async def get_analysis_result(
    result_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get analysis result by ID"""
    result = db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    return {
        "id": result.id,
        "image_id": result.image_id,
        "index_type": result.index_type,
        "result_filepath": result.result_filepath,
        "colormap_filepath": result.colormap_filepath,
        "stats": result.stats,
        "created_at": result.created_at.isoformat(),
    }
