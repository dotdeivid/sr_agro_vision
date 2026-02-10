from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ImageBase(BaseModel):
    filename: str
    project_id: str

class ImageCreate(ImageBase):
    filepath: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    num_channels: Optional[int] = None

class ImageResponse(ImageBase):
    id: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True
