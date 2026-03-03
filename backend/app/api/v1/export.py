from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.result import Result
from app.schemas.export import ExportRequest, ExportResponse, ExportFormat
from app.services.export_service import export_service
from app.core.config import settings

router = APIRouter()


@router.post("/export", response_model=ExportResponse)
async def export_result(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Export a result in specified format

    - **result_id**: ID of the result to export
    - **format**: Export format (png, jpeg, kml, geotiff)
    - **quality**: JPEG quality (1-100)
    """
    try:
        # Get result from database and verify ownership
        result = (
            db.query(Result)
            .join(Result.task)
            .join(Result.task.property.mapper.class_.image)
            .filter(Result.id == request.result_id)
            .first()
        )
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")

        # Ownership check: navigate Result → Task → Image → Project → user_id
        # Simpler approach: check via Task.user_id which we now store
        task = result.task if hasattr(result, "task") and result.task else None
        if task and task.user_id and task.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to export this result"
            )

        result_filepath = result.result_filepath
        if not os.path.exists(result_filepath):
            raise HTTPException(status_code=404, detail="Result file not found on disk")

        # Use settings-based export dir (not hardcoded string)
        export_dir = str(Path(settings.UPLOAD_DIR) / "exports")
        filename = f"export_{request.result_id}"

        exported_path = export_service.export(
            input_path=result_filepath,
            output_dir=export_dir,
            format=request.format.value,
            filename=filename,
            quality=request.quality,
        )

        file_size = os.path.getsize(exported_path)
        exported_filename = os.path.basename(exported_path)

        return {
            "download_url": f"/api/v1/export/download/{exported_filename}",
            "filename": exported_filename,
            "file_size": file_size,
            "format": request.format,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting result: {str(e)}")


@router.get("/download/{filename}")
async def download_export(
    filename: str,
    current_user: User = Depends(get_current_active_user),
):
    """Download an exported file"""
    # Build path from settings, not from a raw user-supplied string
    export_dir = Path(settings.UPLOAD_DIR) / "exports"
    file_path = export_dir / filename

    # Prevent path traversal attacks
    try:
        file_path.resolve().relative_to(export_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )
