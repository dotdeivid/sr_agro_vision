from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path
import uuid

from ...database import get_db
from ...models.user import User
from ...models.image import Image
from ...schemas.image import ImageResponse, ImageCreate
from ..deps import get_current_active_user
from ...core.config import settings

router = APIRouter()

@router.post("/upload", response_model=ImageResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    project_id: str = "default",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a GeoTIFF image"""
    # Validate file type
    if not file.filename.endswith(('.tif', '.tiff')):
        raise HTTPException(status_code=400, detail="Only GeoTIFF files (.tif, .tiff) are allowed")
    
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
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f} MB"
        )
    
    # Create image record
    image = Image(
        filename=file.filename,
        filepath=str(file_path),
        file_size=file_size,
        project_id=project_id
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
    db: Session = Depends(get_db)
):
    """List uploaded images"""
    images = db.query(Image).offset(skip).limit(limit).all()
    return images

@router.get("/{image_id}", response_model=ImageResponse)
def get_image(
    image_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get image by ID"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image
