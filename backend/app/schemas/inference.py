from pydantic import BaseModel, ConfigDict
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
    image_db_id: Optional[str] = None  # set for copernicus download tasks
    error: Optional[str] = None


class ResultResponse(BaseModel):
    # model_used starts with 'model_' which Pydantic v2 treats as a protected namespace.
    # Disable that check since the field name is intentional (it stores the ML model name).
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: str
    task_id: str
    original_image_id: str
    result_filepath: str
    model_used: str
    scale_factor: int
    psnr: Optional[float] = None
    ssim: Optional[float] = None
