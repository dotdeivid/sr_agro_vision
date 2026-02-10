from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models.user import User
from ...models.task import Task
from ...models.result import Result
from ...schemas.inference import (
    InferenceRequest,
    InferenceResponse,
    InferenceStatus,
    ResultResponse
)
from ..deps import get_current_active_user
from ...tasks.processing_tasks import run_sr_inference

router = APIRouter()


@router.post("/process", response_model=InferenceResponse)
def start_inference(
    request: InferenceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start super-resolution inference on an image
    
    Returns task_id to track progress
    """
    # Create task in database
    task = Task(
        type="inference",
        status="queued",
        image_id=request.image_id,
        config={
            "model": request.model,
            "scale": request.scale,
            "device": request.device
        }
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Start Celery task
    celery_task = run_sr_inference.delay(
        task_id=task.id,
        image_id=request.image_id,
        model_name=request.model,
        scale=request.scale,
        device=request.device
    )
    
    # Update task with Celery task ID
    task.celery_task_id = celery_task.id
    db.commit()
    
    return InferenceResponse(
        task_id=task.id,
        status="queued",
        message="Inference task started successfully"
    )


@router.get("/status/{task_id}", response_model=InferenceStatus)
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status of an inference task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result_id = None
    if task.status == "completed" and task.result:
        result_id = task.result.get("result_id")
    
    return InferenceStatus(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        result_id=result_id,
        error=task.error
    )


@router.get("/results/{result_id}", response_model=ResultResponse)
def get_result(
    result_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get inference result by ID"""
    result = db.query(Result).filter(Result.id == result_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return result


@router.get("/tasks", response_model=List[InferenceStatus])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all inference tasks"""
    tasks = db.query(Task).filter(Task.type == "inference").offset(skip).limit(limit).all()
    
    return [
        InferenceStatus(
            task_id=task.id,
            status=task.status,
            progress=task.progress,
            result_id=task.result.get("result_id") if task.result else None,
            error=task.error
        )
        for task in tasks
    ]
