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
def run_copernicus_download_and_process(
    self,
    task_id: str,
    image_id: str,
    output_path: str,
    user_id: str,
    project_id: str = None,
):
    """
    Download a Sentinel-2 image from Copernicus, process it to RGBNIR format,
    and register it in the database so it appears in the frontend.

    Pipeline:
    1. Download .zip from Copernicus
    2. Extract .SAFE structure
    3. Read bands B02 (Blue), B03 (Green), B04 (Red), B08 (NIR) at 10m
    4. Normalize to [0, 1] and combine into a 4-band GeoTIFF
    5. Register in the Image table
    6. Cleanup temp files (.zip + extracted .SAFE)
    """
    from app.services.copernicus_service import copernicus_service
    from app.models.image import Image
    from app.models.project import Project
    import zipfile
    import shutil

    db = SessionLocal()
    try:
        # ── Step 1: Download .zip ────────────────────────────────────────
        self.update_progress(task_id, 5, "processing")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading Sentinel-2 product: {image_id}")
        downloaded_path = copernicus_service.download_image(
            image_id=image_id,
            output_path=output_path,
        )
        self.update_progress(task_id, 30)
        logger.info(f"Downloaded to: {downloaded_path}")

        # ── Step 2: Extract .SAFE ────────────────────────────────────────
        extract_dir = Path(output_path).parent / f"extract_{task_id}"
        extract_dir.mkdir(exist_ok=True)

        logger.info(f"Extracting .SAFE to: {extract_dir}")
        with zipfile.ZipFile(downloaded_path, "r") as zf:
            zf.extractall(extract_dir)
        self.update_progress(task_id, 50)

        # ── Step 3: Locate band files ────────────────────────────────────
        safe_dir = list(extract_dir.glob("*.SAFE"))[0]
        granule_dir = safe_dir / "GRANULE"

        # L2A puts 10 m bands in R10m; L1C puts them directly in IMG_DATA
        img_data_dirs = list(granule_dir.glob("*/IMG_DATA/R10m")) or list(
            granule_dir.glob("*/IMG_DATA")
        )
        if not img_data_dirs:
            raise ValueError("No IMG_DATA directory found in .SAFE")

        img_data_dir = img_data_dirs[0]
        logger.info(f"IMG_DATA at: {img_data_dir}")

        def _find_band(band_name: str) -> Path:
            for pattern in (
                f"*_{band_name}_10m.jp2",
                f"*_{band_name}.jp2",
                f"*_{band_name}_10m.tif",
                f"*_{band_name}.tif",
            ):
                hits = list(img_data_dir.glob(pattern))
                if hits:
                    return hits[0]
            raise FileNotFoundError(f"Band {band_name} not found in {img_data_dir}")

        b02_file = _find_band("B02")
        b03_file = _find_band("B03")
        b04_file = _find_band("B04")
        b08_file = _find_band("B08")
        logger.info("Located bands B02, B03, B04, B08")
        self.update_progress(task_id, 60)

        # ── Step 4: Read & combine bands ──────────────────────────────────
        import rasterio
        import rasterio.warp
        import numpy as np

        with rasterio.open(b02_file) as src:
            b02 = src.read(1).astype(np.float32)
            meta = src.meta.copy()
            crs = src.crs
            width, height = src.width, src.height

        with rasterio.open(b03_file) as src:
            b03 = src.read(1).astype(np.float32)
        with rasterio.open(b04_file) as src:
            b04 = src.read(1).astype(np.float32)
        with rasterio.open(b08_file) as src:
            b08 = src.read(1).astype(np.float32)

        # Sentinel-2 reflectance is 0-10000 → normalize to [0, 1]
        for arr in (b02, b03, b04, b08):
            np.clip(arr, 0, 10000, out=arr)
            arr /= 10000.0

        self.update_progress(task_id, 70)

        # ── Step 5: Write RGBNIR GeoTIFF ──────────────────────────────────
        rgbnir_filename = f"sentinel_{image_id}_RGBNIR.tif"
        rgbnir_path = Path(settings.DOWNLOAD_DIR) / rgbnir_filename

        meta.update(count=4, dtype="float32", driver="GTiff", compress="lzw")

        with rasterio.open(rgbnir_path, "w", **meta) as dst:
            dst.write(b02, 1)
            dst.write(b03, 2)
            dst.write(b04, 3)
            dst.write(b08, 4)
            dst.set_band_description(1, "Blue (B02)")
            dst.set_band_description(2, "Green (B03)")
            dst.set_band_description(3, "Red (B04)")
            dst.set_band_description(4, "NIR (B08)")

        self.update_progress(task_id, 80)
        logger.info(f"RGBNIR file written: {rgbnir_path}")

        # ── Step 6: Register in DB ────────────────────────────────────────
        # Resolve or create project
        effective_project_id = project_id
        if not effective_project_id or effective_project_id == "default":
            project = (
                db.query(Project)
                .filter(Project.user_id == user_id, Project.name == "default")
                .first()
            )
            if not project:
                project = Project(
                    name="default",
                    description="Default project for Sentinel-2 downloads",
                    user_id=user_id,
                )
                db.add(project)
                db.commit()
                db.refresh(project)
            effective_project_id = project.id

        file_size = rgbnir_path.stat().st_size

        with rasterio.open(rgbnir_path) as src:
            bounds = src.bounds
            if src.crs and str(src.crs) != "EPSG:4326":
                bounds_wgs84 = rasterio.warp.transform_bounds(
                    src.crs,
                    "EPSG:4326",
                    bounds.left,
                    bounds.bottom,
                    bounds.right,
                    bounds.top,
                )
            else:
                bounds_wgs84 = (bounds.left, bounds.bottom, bounds.right, bounds.top)

        image_record = Image(
            filename=rgbnir_filename,
            filepath=str(rgbnir_path),
            file_size=file_size,
            width=width,
            height=height,
            num_channels=4,
            image_metadata={
                "bounds": list(bounds_wgs84),
                "crs": str(crs),
                "dtype": "float32",
                "sentinel_product_id": image_id,
                "bands": ["Blue (B02)", "Green (B03)", "Red (B04)", "NIR (B08)"],
                "source": "Copernicus Data Space Ecosystem",
            },
            project_id=effective_project_id,
        )
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
        logger.info(f"Image registered in DB: {image_record.id}")
        self.update_progress(task_id, 90)

        # ── Step 7: Cleanup temp files ────────────────────────────────────
        try:
            shutil.rmtree(extract_dir, ignore_errors=True)
            Path(downloaded_path).unlink(missing_ok=True)
            logger.info("Temp files cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

        # ── Done ──────────────────────────────────────────────────────────
        result_payload = {
            "image_db_id": image_record.id,
            "filename": rgbnir_filename,
            "sentinel_product_id": image_id,
            "bands": 4,
            "width": width,
            "height": height,
            "file_size": file_size,
        }
        self.mark_completed(task_id, result_payload)
        logger.info(f"✅ Sentinel-2 download & processing completed: {image_id}")
        return {"status": "completed", "image_id": image_record.id}

    except Exception as e:
        import traceback

        error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        logger.error(f"Task failed: {error_msg}")
        self.mark_failed(task_id, str(e))
        # Best-effort cleanup
        try:
            if "extract_dir" in locals():
                shutil.rmtree(extract_dir, ignore_errors=True)
            if "downloaded_path" in locals():
                Path(downloaded_path).unlink(missing_ok=True)
        except Exception:
            pass
        raise
    finally:
        db.close()
