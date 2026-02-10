from pydantic import BaseModel
from typing import Optional, Literal

class InferenceRequest(BaseModel):
    image_id: str
    model: Literal["espcn", "swinir", "gan"] = "espcn"
    scale: Literal[2, 4] = 4
    device: Optional[str] = None  # "cuda", "cpu", None=auto

class InferenceResponse(BaseModel):
    task_id: str
    status: str
    message: str

class InferenceStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    result_id: Optional[str] = None
    error: Optional[str] = None

class ResultResponse(BaseModel):
    id: str
    task_id: str
    original_image_id: str
    result_filepath: str
    model_used: str
    scale_factor: int
    psnr: Optional[float]
    ssim: Optional[float]
    
    class Config:
        from_attributes = True
