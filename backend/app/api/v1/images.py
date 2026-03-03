from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path
import uuid
import logging

from app.database import get_db
from app.models.user import User
from app.models.image import Image
from app.models.project import Project
from app.schemas.image import ImageResponse, ImageCreate
from app.api.deps import get_current_active_user
from app.core.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()


def _get_or_create_default_project(db: Session, user_id: str, project_id: str) -> str:
    """Return a valid project ID, creating 'default' project for the user if it doesn't exist."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="You do not own this project")
        return project.id

    # If project_id == "default", auto-create a default project for this user
    if project_id == "default":
        default = (
            db.query(Project)
            .filter(Project.user_id == user_id, Project.name == "default")
            .first()
        )
        if default:
            return default.id
        default = Project(
            name="default", description="Default project", user_id=user_id
        )
        db.add(default)
        db.commit()
        db.refresh(default)
        return default.id

    raise HTTPException(status_code=404, detail="Project not found")


@router.post("/upload", response_model=ImageResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    project_id: str = "default",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a GeoTIFF image"""
    # Validate file type
    if not file.filename.endswith((".tif", ".tiff")):
        raise HTTPException(
            status_code=400, detail="Only GeoTIFF files (.tif, .tiff) are allowed"
        )

    # Resolve / create project
    resolved_project_id = _get_or_create_default_project(
        db, current_user.id, project_id
    )

    # Create upload directory if not exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    new_filename = f"{file_id}{file_extension}"
    file_path = upload_dir / new_filename

    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = file_path.stat().st_size

    # Validate file size
    if file_size > settings.MAX_UPLOAD_SIZE:
        file_path.unlink()  # Delete file
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f} MB",
        )

    # Extract rasterio metadata
    width = height = num_channels = None
    image_metadata = {}
    try:
        import rasterio
        import rasterio.warp

        with rasterio.open(str(file_path)) as src:
            width = src.width
            height = src.height
            num_channels = src.count
            bounds_native = src.bounds
            if src.crs:
                west, south, east, north = rasterio.warp.transform_bounds(
                    src.crs,
                    "EPSG:4326",
                    bounds_native.left,
                    bounds_native.bottom,
                    bounds_native.right,
                    bounds_native.top,
                )
                image_metadata["bounds"] = [west, south, east, north]
                image_metadata["crs"] = str(src.crs)
            else:
                image_metadata["bounds"] = None
            image_metadata["dtype"] = str(src.dtypes[0])
    except Exception as e:
        logger.warning(f"Could not extract rasterio metadata: {e}")

    # Create image record
    image = Image(
        filename=file.filename,
        filepath=str(file_path),
        file_size=file_size,
        width=width,
        height=height,
        num_channels=num_channels,
        image_metadata=image_metadata or None,
        project_id=resolved_project_id,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return image


@router.get("/", response_model=List[ImageResponse])
def list_images(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List uploaded images for the current user"""
    images = (
        db.query(Image)
        .join(Project, Image.project_id == Project.id)
        .filter(Project.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return images


# NOTE: /view/ and /download/ MUST come before /{image_id} so FastAPI
# doesn't match the literal strings "view" / "download" as image_id values.


@router.get("/view/{filename}")
def view_file(filename: str, current_user: User = Depends(get_current_active_user)):
    """Serve an image file for in-browser viewing (maps, colormaps)"""
    search_dirs = [
        Path(settings.UPLOAD_DIR),
        Path(settings.SR_OUTPUT_DIR),
        Path(settings.UPLOAD_DIR) / "analysis",
        Path(settings.UPLOAD_DIR) / "exports",
    ]
    for directory in search_dirs:
        file_path = directory / filename
        if file_path.exists():
            suffix = file_path.suffix.lower()
            media_type = (
                "image/png"
                if suffix == ".png"
                else (
                    "image/jpeg"
                    if suffix in (".jpg", ".jpeg")
                    else (
                        "image/tiff"
                        if suffix in (".tif", ".tiff")
                        else "application/octet-stream"
                    )
                )
            )
            return FileResponse(str(file_path), media_type=media_type)
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/download/{filename}")
def download_file(filename: str, current_user: User = Depends(get_current_active_user)):
    """Download an image file as an attachment"""
    search_dirs = [
        Path(settings.UPLOAD_DIR),
        Path(settings.SR_OUTPUT_DIR),
        Path(settings.UPLOAD_DIR) / "analysis",
        Path(settings.UPLOAD_DIR) / "exports",
    ]
    for directory in search_dirs:
        file_path = directory / filename
        if file_path.exists():
            return FileResponse(
                str(file_path),
                filename=filename,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/{image_id}", response_model=ImageResponse)
def get_image(
    image_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get image by ID — only returns images belonging to the current user"""
    image = (
        db.query(Image)
        .join(Project, Image.project_id == Project.id)
        .filter(Image.id == image_id, Project.user_id == current_user.id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image
