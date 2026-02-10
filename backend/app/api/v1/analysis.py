from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
from datetime import datetime

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.image import Image
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisStats,
    IndexType
)
from app.services.ndvi_service import ndvi_service

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_image(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        output_dir = Path("backend/uploads/analysis") / str(uuid.uuid4())
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process image
        result_tiff, colormap_png, stats = ndvi_service.process_image(
            image_path=image.filepath,
            index_type=request.index_type,
            output_dir=str(output_dir)
        )
        
        # Create result
        result_id = str(uuid.uuid4())
        
        result_data = {
            "id": result_id,
            "image_id": request.image_id,
            "index_type": request.index_type,
            "result_filepath": result_tiff,
            "colormap_filepath": colormap_png,
            "stats": stats,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # TODO: Save to database
        
        return result_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing image: {str(e)}"
        )


@router.get("/results/{result_id}", response_model=AnalysisResult)
async def get_analysis_result(
    result_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get analysis result by ID"""
    # TODO: Implement database retrieval
    raise HTTPException(status_code=501, detail="Not implemented yet")
