import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CopernicusService:
    """Service for interacting with Copernicus Data Space API"""
    
    def __init__(self):
        self.api_url = settings.COPERNICUS_API_URL
        self.download_url = settings.COPERNICUS_DOWNLOAD_URL
        self.client_id = settings.COPERNICUS_CLIENT_ID
        self.client_secret = settings.COPERNICUS_CLIENT_SECRET
        self.access_token: Optional[str] = None
        self.token_expires: Optional[float] = None
    
    def _get_access_token(self) -> str:
        """Get OAuth2 access token"""
        # Check if we have a valid token
        if self.access_token and self.token_expires:
            if datetime.utcnow().timestamp() < self.token_expires:
                return self.access_token
        
        # Get new token
        token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            # Token typically expires in 600 seconds
            expires_in = token_data.get("expires_in", 600)
            self.token_expires = datetime.utcnow().timestamp() + expires_in
            
            return self.access_token
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise
    
    def search_images(
        self,
        bbox: List[float],
        start_date: str,
        end_date: str,
        max_cloud_cover: int = 20,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for Sentinel-2 images
        
        Args:
            bbox: Bounding box [lon_min, lat_min, lon_max, lat_max]
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            max_cloud_cover: Maximum cloud cover percentage
            max_results: Maximum number of results
        
        Returns:
            Dictionary with search results
        """
        search_url = f"{self.api_url}/collections/Sentinel2/search.json"
        
        # Format bbox as string
        bbox_str = ",".join(map(str, bbox))
        
        params = {
            "box": bbox_str,
            "startDate": start_date,
            "completionDate": end_date,
            "maxCloudCover": max_cloud_cover,
            "maxRecords": max_results,
            "productType": "S2MSI2A",  # Level-2A products
            "status": "ARCHIVED"
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Parse results
            results = []
            features = data.get("features", [])
            
            for feature in features:
                props = feature.get("properties", {})
                
                # Extract band information
                bands = self._extract_bands(props)
                
                image_data = {
                    "id": props.get("id", ""),
                    "title": props.get("title", ""),
                    "product_type": props.get("productType", ""),
                    "platform": props.get("platform", ""),
                    "sensing_time": props.get("startDate", ""),
                    "cloud_cover": props.get("cloudCover", 0),
                    "footprint": str(feature.get("geometry", {}).get("coordinates", [])),
                    "thumbnail_url": self._get_thumbnail_url(props),
                    "download_url": self._get_download_url(props.get("id", "")),
                    "size_mb": props.get("productSizeMB", 0),
                    "bands_available": bands
                }
                
                results.append(image_data)
            
            return {
                "total_results": data.get("totalResults", 0),
                "images": results
            }
            
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            raise
    
    def _extract_bands(self, properties: Dict) -> List[str]:
        """Extract available bands from properties"""
        # Sentinel-2 standard bands
        return [
            "B01", "B02", "B03", "B04", "B05", "B06", 
            "B07", "B08", "B8A", "B09", "B10", "B11", "B12"
        ]
    
    def _get_thumbnail_url(self, properties: Dict) -> str:
        """Get thumbnail URL for image"""
        # Try to get quicklook
        links = properties.get("links", [])
        for link in links:
            if link.get("rel") == "icon":
                return link.get("href", "")
        return ""
    
    def _get_download_url(self, image_id: str) -> str:
        """Get download URL for image"""
        return f"{self.download_url}/Products({image_id})/$value"
    
    def download_image(
        self,
        image_id: str,
        output_path: str,
        bands: Optional[List[str]] = None
    ) -> str:
        """
        Download a Sentinel-2 image
        
        Args:
            image_id: Image ID from search results
            output_path: Path to save the downloaded file
            bands: Optional list of bands to download
        
        Returns:
            Path to downloaded file
        """
        token = self._get_access_token()
        download_url = self._get_download_url(image_id)
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Save to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded image {image_id} to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            raise


# Singleton instance
copernicus_service = CopernicusService()
