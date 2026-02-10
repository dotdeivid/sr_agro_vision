from celery import Task
from .celery_app import celery_app
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path to import src
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.inference.predictor import SRPredictor
from src.utils.device import get_device
from app.database import SessionLocal
from app.models.task import Task as TaskModel
from app.models.result import Result
from app.core.config import settings


class CallbackTask(Task):
    """Custom task with progress callback"""
    
    def update_progress(self, task_id: str, progress: int, status: str = "processing"):
        """Update task progress in database"""
        db = SessionLocal()
        try:
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                task.progress = progress
                task.status = status
                if status == "processing" and not task.started_at:
                    task.started_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()


@celery_app.task(bind=True, base=CallbackTask)
def run_sr_inference(self, task_id: str, image_id: str, model_name: str, scale: int, device: str = None):
    """
    Execute super-resolution inference on an image
    
    Args:
        task_id: Database task ID
        image_id: Database image ID
        model_name: Model to use ("espcn", "swinir", "gan")
        scale: Scale factor (2 or 4)
        device: Device to use ("cuda", "cpu", or None for auto)
    """
    db = SessionLocal()
    
    try:
        # Update task status
        self.update_progress(task_id, 0, "processing")
        
        # Get image from database
        from app.models.image import Image
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise ValueError(f"Image {image_id} not found")
        
        input_path = image.filepath
        
        # Prepare output path
        output_dir = Path(settings.SR_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_filename = f"sr_{model_name}_x{scale}_{Path(input_path).stem}.tif"
        output_path = output_dir / output_filename
        
        # Progress callback
        def progress_callback(current: int, total: int):
            progress = int((current / total) * 100)
            self.update_progress(task_id, progress)
            self.update_state(state='PROGRESS', meta={'progress': progress})
        
        # Initialize predictor
        self.update_progress(task_id, 5)
        
        if device is None:
            device = get_device()
        
        predictor = SRPredictor(
            model_name=model_name,
            scale_factor=scale,
            device=device
        )
        
        self.update_progress(task_id, 10)
        
        # Run inference
        metrics = predictor.predict(
            input_path=str(input_path),
            output_path=str(output_path),
            calculate_metrics=True,
            progress_callback=progress_callback
        )
        
        # Save result to database
        result = Result(
            task_id=task_id,
            original_image_id=image_id,
            result_filepath=str(output_path),
            model_used=model_name,
            scale_factor=scale,
            psnr=metrics.get('psnr'),
            ssim=metrics.get('ssim'),
            metadata=metrics
        )
        db.add(result)
        
        # Update task as completed
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task:
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            task.result = {"result_id": result.id}
        
        db.commit()
        db.refresh(result)
        
        return {
            "status": "completed",
            "result_id": result.id,
            "metrics": metrics
        }
        
    except Exception as e:
        # Update task as failed
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()
        
        raise
    
    finally:
        db.close()
