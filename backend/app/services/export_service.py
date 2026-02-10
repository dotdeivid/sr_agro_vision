import os
from pathlib import Path
from typing import Optional
from PIL import Image
import rasterio
from rasterio.crs import CRS
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting results in different formats"""
    
    @staticmethod
    def export_to_png(
        input_path: str,
        output_path: str,
        max_width: int = 2048
    ) -> str:
        """
        Export GeoTIFF to PNG
        """
        try:
            with rasterio.open(input_path) as src:
                # Read data
                data = src.read(1)
                
                # Normalize to 0-255
                data_min = data.min()
                data_max = data.max()
                
                if data_max > data_min:
                    data_norm = ((data - data_min) / (data_max - data_min) * 255).astype('uint8')
                else:
                    data_norm = data.astype('uint8')
                
                # Create PIL image
                img = Image.fromarray(data_norm)
                
                # Resize if too large
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Save as PNG
                img.save(output_path, 'PNG')
                
                return output_path
                
        except Exception as e:
            logger.error(f"Error exporting to PNG: {e}")
            raise
    
    @staticmethod
    def export_to_jpeg(
        input_path: str,
        output_path: str,
        quality: int = 95
    ) -> str:
        """
        Export to JPEG
        """
        try:
            # First export to PNG
            temp_png = output_path.replace('.jpg', '.png')
            ExportService.export_to_png(input_path, temp_png)
            
            # Convert PNG to JPEG
            with Image.open(temp_png) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    rgb_img.save(output_path, 'JPEG', quality=quality)
                else:
                    img.save(output_path, 'JPEG', quality=quality)
            
            # Remove temp PNG
            if os.path.exists(temp_png):
                os.remove(temp_png)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to JPEG: {e}")
            raise
    
    @staticmethod
    def export_to_kml(
        input_path: str,
        output_path: str,
        name: str = "Image"
    ) -> str:
        """
        Export to KML (simplified)
        """
        try:
            with rasterio.open(input_path) as src:
                bounds = src.bounds
                
                # Create simple KML
                kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <GroundOverlay>
      <name>{name}</name>
      <LatLonBox>
        <north>{bounds.top}</north>
        <south>{bounds.bottom}</south>
        <east>{bounds.right}</east>
        <west>{bounds.left}</west>
      </LatLonBox>
    </GroundOverlay>
  </Document>
</kml>"""
                
                with open(output_path, 'w') as f:
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
        quality: int = 95
    ) -> str:
        """
        Export file to specified format
        """
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
            # Just copy the original
            output_path = os.path.join(output_dir, f"{filename}.tif")
            import shutil
            shutil.copy2(input_path, output_path)
            return output_path
        
        else:
            raise ValueError(f"Unsupported format: {format}")


export_service = ExportService()
