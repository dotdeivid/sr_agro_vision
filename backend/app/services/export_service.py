import os
import tempfile
from pathlib import Path
from typing import Optional
from PIL import Image
import rasterio
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting results in different formats"""

    @staticmethod
    def export_to_png(input_path: str, output_path: str, max_width: int = 2048) -> str:
        """Export GeoTIFF to PNG"""
        try:
            with rasterio.open(input_path) as src:
                data = src.read(1)
                data_min, data_max = data.min(), data.max()
                if data_max > data_min:
                    data_norm = (
                        (data - data_min) / (data_max - data_min) * 255
                    ).astype("uint8")
                else:
                    data_norm = data.astype("uint8")
                img = Image.fromarray(data_norm)
                if img.width > max_width:
                    ratio = max_width / img.width
                    img = img.resize(
                        (max_width, int(img.height * ratio)),
                        Image.Resampling.LANCZOS,
                    )
                img.save(output_path, "PNG")
                return output_path
        except Exception as e:
            logger.error(f"Error exporting to PNG: {e}")
            raise

    @staticmethod
    def export_to_jpeg(input_path: str, output_path: str, quality: int = 95) -> str:
        """Export GeoTIFF to JPEG.

        Uses a named temp file so there's no race condition: the temp file is
        always cleaned up in a ``finally`` block, whether conversion succeeds
        or fails.
        """
        # Derive a safe temp path alongside the final output file
        output_dir = Path(output_path).parent
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".png", dir=output_dir, delete=False
            ) as tmp:
                tmp_path = tmp.name

            # Step 1: render GeoTIFF to a temporary PNG
            ExportService.export_to_png(input_path, tmp_path)

            # Step 2: convert PNG → JPEG
            with Image.open(tmp_path) as img:
                if img.mode in ("RGBA", "LA", "P"):
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    mask = img.split()[-1] if img.mode == "RGBA" else None
                    rgb_img.paste(img, mask=mask)
                    rgb_img.save(output_path, "JPEG", quality=quality)
                else:
                    img.convert("RGB").save(output_path, "JPEG", quality=quality)

            return output_path
        except Exception as e:
            logger.error(f"Error exporting to JPEG: {e}")
            raise
        finally:
            # Always clean up, even on error
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def export_to_kml(input_path: str, output_path: str, name: str = "Image") -> str:
        """Export bounding box to KML (GroundOverlay stub)"""
        try:
            with rasterio.open(input_path) as src:
                # Reproject bounds to WGS84 if needed
                import rasterio.warp

                bounds = src.bounds
                if src.crs and str(src.crs).upper() != "EPSG:4326":
                    west, south, east, north = rasterio.warp.transform_bounds(
                        src.crs,
                        "EPSG:4326",
                        bounds.left,
                        bounds.bottom,
                        bounds.right,
                        bounds.top,
                    )
                else:
                    west, south, east, north = (
                        bounds.left,
                        bounds.bottom,
                        bounds.right,
                        bounds.top,
                    )

                kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <GroundOverlay>
      <name>{name}</name>
      <LatLonBox>
        <north>{north}</north>
        <south>{south}</south>
        <east>{east}</east>
        <west>{west}</west>
      </LatLonBox>
    </GroundOverlay>
  </Document>
</kml>"""
                with open(output_path, "w") as f:
                    f.write(kml_content)
                return output_path
        except Exception as e:
            logger.error(f"Error exporting to KML: {e}")
            raise

    @staticmethod
    def export(
        input_path: str,
        output_dir: str,
        format: str,
        filename: str,
        quality: int = 95,
    ) -> str:
        """Export file to specified format"""
        os.makedirs(output_dir, exist_ok=True)

        if format == "png":
            output_path = os.path.join(output_dir, f"{filename}.png")
            return ExportService.export_to_png(input_path, output_path)
        elif format == "jpeg":
            output_path = os.path.join(output_dir, f"{filename}.jpg")
            return ExportService.export_to_jpeg(input_path, output_path, quality)
        elif format == "kml":
            output_path = os.path.join(output_dir, f"{filename}.kml")
            return ExportService.export_to_kml(input_path, output_path, filename)
        elif format == "geotiff":
            import shutil

            output_path = os.path.join(output_dir, f"{filename}.tif")
            shutil.copy2(input_path, output_path)
            return output_path
        else:
            raise ValueError(f"Unsupported format: {format}")


export_service = ExportService()
