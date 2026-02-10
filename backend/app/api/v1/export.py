from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.export import ExportRequest, ExportResponse, ExportFormat
from app.services.export_service import export_service

router = APIRouter()


@router.post("/export", response_model=ExportResponse)
async def export_result(
    request: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Export a result in specified format
    
    - **result_id**: ID of the result to export
    - **format**: Export format (png, jpeg, kml, geotiff)
    - **quality**: JPEG quality (1-100)
    """
    try:
        # TODO: Get result from database
        # For now, assume we have the filepath
        result_filepath = f"backend/uploads/results/{request.result_id}.tif"
        
        if not os.path.exists(result_filepath):
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Export
        export_dir = "backend/uploads/exports"
        filename = f"export_{request.result_id}"
        
        exported_path = export_service.export(
            input_path=result_filepath,
            output_dir=export_dir,
            format=request.format.value,
            filename=filename,
            quality=request.quality
        )
        
        # Get file info
        file_size = os.path.getsize(exported_path)
        exported_filename = os.path.basename(exported_path)
        
        return {
            "download_url": f"/api/v1/export/download/{exported_filename}",
            "filename": exported_filename,
            "file_size": file_size,
            "format": request.format
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting result: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_export(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download exported file"""
    file_path = f"backend/uploads/exports/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
