from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    type: str
    status: str = "queued"
    progress: int = 0

class TaskCreate(TaskBase):
    image_id: Optional[str] = None
    config: Optional[dict] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    result: Optional[dict] = None
    error: Optional[str] = None

class TaskResponse(TaskBase):
    id: str
    image_id: Optional[str]
    config: Optional[dict]
    result: Optional[dict]
    error: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    celery_task_id: Optional[str]
    
    class Config:
        from_attributes = True
