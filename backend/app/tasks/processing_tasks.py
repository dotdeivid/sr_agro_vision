from celery import Task
from .celery_app import celery_app
from pathlib import Path
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# sys.path setup – kept here so it only runs once at import time.
# The project root must be in the path so `src.*` modules are importable.
# When running in production, prefer installing the package with:
#   pip install -e .
# from the project root instead of relying on this path manipulation.
# ---------------------------------------------------------------------------
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.models.task import Task as TaskModel
from app.models.result import Result
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# NOTE: SRPredictor and get_device are intentionally NOT imported here.
# Importing them at module level would cause Celery to load torch/CUDA
# at worker startup — even when no inference task is queued — which
# crashes workers in environments without torch installed.
# They are imported lazily inside run_sr_inference() instead.


class CallbackTask(Task):
    """Base Celery task class with shared DB helpers for progress, completion and failure."""

    def update_progress(self, task_id: str, progress: int, status: str = "processing"):
        """Persist progress and status to the Task row."""
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

    def mark_completed(self, task_id: str, result_payload: dict):
        """Mark a task as completed with the given result payload."""
        db = SessionLocal()
        try:
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                task.status = "completed"
                task.progress = 100
                task.completed_at = datetime.utcnow()
                task.result = result_payload
                db.commit()
        finally:
            db.close()

    def mark_failed(self, task_id: str, error: str):
        """Mark a task as failed with the error message."""
        db = SessionLocal()
        try:
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                task.status = "failed"
                task.error = error
                task.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()


@celery_app.task(bind=True, base=CallbackTask)
def run_sr_inference(
    self, task_id: str, image_id: str, model_name: str, scale: int, device: str = None
):
    """
    Execute super-resolution inference on an image.

    Args:
        task_id:    Database Task ID
        image_id:   Database Image ID
        model_name: Model to use ("espcn", "swinir", "gan")
        scale:      Scale factor (2 or 4)
        device:     Device to use ("cuda", "cpu", or None for auto)
    """
    db = SessionLocal()
    try:
        self.update_progress(task_id, 0, "processing")

        # Lazy imports: torch and the SR predictor are only loaded when
        # this task actually executes, not at worker startup.
        from src.inference.predictor import SRPredictor  # noqa: E402
        from src.utils.device import get_device  # noqa: E402

        from app.models.image import Image

        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise ValueError(f"Image {image_id} not found")

        input_path = image.filepath

        output_dir = Path(settings.SR_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"sr_{model_name}_x{scale}_{Path(input_path).stem}.tif"
        output_path = output_dir / output_filename

        def progress_callback(current: int, total: int):
            progress = int((current / total) * 100)
            self.update_progress(task_id, progress)
            self.update_state(state="PROGRESS", meta={"progress": progress})

        self.update_progress(task_id, 5)

        if device is None:
            device = get_device()

        predictor = SRPredictor(
            model_name=model_name, scale_factor=scale, device=device
        )
        self.update_progress(task_id, 10)

        metrics = predictor.predict(
            input_path=str(input_path),
            output_path=str(output_path),
            calculate_metrics=True,
            progress_callback=progress_callback,
        )

        # Save result to DB
        result = Result(
            task_id=task_id,
            original_image_id=image_id,
            result_filepath=str(output_path),
            model_used=model_name,
            scale_factor=scale,
            psnr=metrics.get("psnr"),
            ssim=metrics.get("ssim"),
            extra_metadata=metrics,
        )
        db.add(result)
        db.commit()
        db.refresh(result)

        self.mark_completed(task_id, {"result_id": result.id})
        return {"status": "completed", "result_id": result.id, "metrics": metrics}

    except Exception as e:
        logger.error(
            f"Task failed: {type(e).__name__}: {e}",
            extra={"task_id": task_id, "image_id": image_id},
        )
        self.mark_failed(task_id, str(e))
        raise
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask)
def run_copernicus_download(self, task_id: str, image_id: str, output_path: str):
    """
    Download a Sentinel-2 image from Copernicus Data Space (CDSE).

    Args:
        task_id:     Database Task ID
        image_id:    Sentinel-2 product ID from CDSE search results
        output_path: Filesystem path to save the downloaded file
    """
    from app.services.copernicus_service import copernicus_service

    db = SessionLocal()
    try:
        self.update_progress(task_id, 0, "processing")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        self.update_progress(task_id, 10)

        downloaded_path = copernicus_service.download_image(
            image_id=image_id, output_path=output_path
        )

        self.mark_completed(
            task_id, {"downloaded_path": downloaded_path, "image_id": image_id}
        )
        return {
            "status": "completed",
            "downloaded_path": downloaded_path,
            "image_id": image_id,
        }

    except Exception as e:
        self.mark_failed(task_id, str(e))
        raise
    finally:
        db.close()
