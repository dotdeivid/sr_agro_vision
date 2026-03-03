"""
Copernicus Data Space Ecosystem (CDSE) service.

Authentication
--------------
- Search  : OData catalogue — public, no token required.
- Download: Bearer token obtained via OAuth2 password grant.

  POST https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
  client_id = cdse-public   (fixed public client — not a service-account ID)
  grant_type = password
  username   = COPERNICUS_USER  (your CDSE account email)
  password   = COPERNICUS_PASS  (your CDSE account password)

API migration note
------------------
The OpenSearch Catalogue API (`/resto/api/...`) was decommissioned on 2026-03-02.
All search queries now use the OData v1 endpoint:
  https://catalogue.dataspace.copernicus.eu/odata/v1/Products
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# OAuth2 token endpoint — fixed for all CDSE users
_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu"
    "/auth/realms/CDSE/protocol/openid-connect/token"
)
# OData Products endpoint — replaces the decommissioned OpenSearch API
_ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
# Download base URL (OData $value)
_DOWNLOAD_URL = (
    "https://catalogue.dataspace.copernicus.eu/odata/v1/Products({id})/$value"
)


class CopernicusService:
    """Service for interacting with Copernicus Data Space (CDSE) APIs."""

    def __init__(self):
        self.user = settings.COPERNICUS_USER
        self.password = settings.COPERNICUS_PASS
        self._access_token: Optional[str] = None
        self._token_expires: float = 0.0

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _get_access_token(self) -> str:
        """
        Get (or refresh) an OAuth2 Bearer token using password grant.

        The public client 'cdse-public' is used — no service-account
        Client ID / Secret required.
        """
        if self._access_token and datetime.utcnow().timestamp() < self._token_expires:
            return self._access_token

        if not self.user or not self.password:
            raise ValueError(
                "COPERNICUS_USER and COPERNICUS_PASS must be set in backend/.env "
                "to download Sentinel-2 products."
            )

        response = requests.post(
            _TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": "cdse-public",
                "username": self.user,
                "password": self.password,
            },
            timeout=30,
        )
        response.raise_for_status()
        token_data = response.json()

        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 600)
        # Subtract 30 s buffer so we refresh before actual expiry
        self._token_expires = datetime.utcnow().timestamp() + expires_in - 30

        logger.info("Copernicus access token refreshed")
        return self._access_token

    # ------------------------------------------------------------------
    # Search  (OData — public, no auth required)
    # ------------------------------------------------------------------

    def search_images(
        self,
        bbox: List[float],
        start_date: str,
        end_date: str,
        max_cloud_cover: int = 20,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for Sentinel-2 L2A products via OData.

        Args:
            bbox: [lon_min, lat_min, lon_max, lat_max]
            start_date: 'YYYY-MM-DD'
            end_date:   'YYYY-MM-DD'
            max_cloud_cover: maximum cloud cover %
            max_results: max products to return

        Returns:
            {'total_results': int, 'images': [...]}
        """
        lon_min, lat_min, lon_max, lat_max = bbox

        # Build WKT polygon from bbox
        wkt = (
            f"POLYGON(("
            f"{lon_min} {lat_min},"
            f"{lon_max} {lat_min},"
            f"{lon_max} {lat_max},"
            f"{lon_min} {lat_max},"
            f"{lon_min} {lat_min}"
            f"))"
        )

        # OData $filter expression
        filter_parts = [
            "Collection/Name eq 'SENTINEL-2'",
            "Attributes/OData.CSC.StringAttribute/any("
            "att:att/Name eq 'productType' and "
            "att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')",
            f"ContentDate/Start ge {start_date}T00:00:00.000Z",
            f"ContentDate/Start le {end_date}T23:59:59.000Z",
            f"Attributes/OData.CSC.DoubleAttribute/any("
            f"att:att/Name eq 'cloudCover' and "
            f"att/OData.CSC.DoubleAttribute/Value le {float(max_cloud_cover)})",
            f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')",
        ]

        params = {
            "$filter": " and ".join(filter_parts),
            "$top": max_results,
            "$expand": "Attributes,Assets",
            "$orderby": "ContentDate/Start desc",
        }

        try:
            # ── Step 1: search products with Attributes expand ──────────────
            # ($expand=Attributes,Assets is not supported by the OData endpoint)
            response = requests.get(
                _ODATA_URL,
                params={**params, "$expand": "Attributes"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("value", [])
            if not items:
                return {"total_results": 0, "images": []}

            # ── Step 2: batch-fetch QUICKLOOK asset URLs ────────────────────
            # One extra OData request for all product IDs — avoids N calls
            product_ids = [item["Id"] for item in items]
            id_list = ",".join(f"'{pid}'" for pid in product_ids)
            asset_resp = requests.get(
                _ODATA_URL,
                params={
                    "$filter": f"Id in ({id_list})",
                    "$expand": "Assets",
                    "$top": len(product_ids),
                },
                timeout=30,
            )
            # Build {product_id: quicklook_url} map (fail silently)
            thumbnail_map: dict = {}
            if asset_resp.ok:
                for a_item in asset_resp.json().get("value", []):
                    for asset in a_item.get("Assets", []):
                        if asset.get("Type") == "QUICKLOOK":
                            thumbnail_map[a_item["Id"]] = asset.get("DownloadLink", "")
                            break

            # ── Step 3: build result list ───────────────────────────────────
            results = []
            for item in items:
                attrs = {a["Name"]: a.get("Value") for a in item.get("Attributes", [])}
                pid = item.get("Id", "")
                image_data = {
                    "id": pid,
                    "title": item.get("Name", ""),
                    "product_type": attrs.get("productType", "S2MSI2A"),
                    "platform": attrs.get("platformShortName", "Sentinel-2"),
                    "sensing_time": item.get("ContentDate", {}).get("Start", ""),
                    "cloud_cover": attrs.get("cloudCover", 0),
                    "footprint": item.get("Footprint", ""),
                    "thumbnail_url": thumbnail_map.get(pid, ""),
                    "download_url": _DOWNLOAD_URL.format(id=pid),
                    "size_mb": round(item.get("ContentLength", 0) / 1_048_576, 1),
                    "bands_available": self._sentinel2_bands(),
                    "online": item.get("Online", True),
                }
                results.append(image_data)

            total = data.get("@odata.count", len(results))
            logger.info(f"Copernicus search returned {len(results)} products")
            return {"total_results": total, "images": results}

        except Exception as e:
            logger.error(f"Error searching Sentinel-2 images: {e}")
            raise

    # ------------------------------------------------------------------
    # Download  (requires Bearer token)
    # ------------------------------------------------------------------

    def download_image(
        self, image_id: str, output_path: str, bands: Optional[List[str]] = None
    ) -> str:
        """
        Download a Sentinel-2 product by its OData product ID.

        Args:
            image_id:    Product UUID from search results
            output_path: Filesystem path to save the file
            bands:       Ignored for now (full product is downloaded)

        Returns:
            output_path on success
        """
        token = self._get_access_token()
        url = _DOWNLOAD_URL.format(id=image_id)
        headers = {"Authorization": f"Bearer {token}"}

        try:
            # Copernicus redirects catalogue.dataspace → download.dataspace.
            # requests strips the Authorization header on cross-domain
            # redirects, causing a 401. We handle the redirect manually.
            response = requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=60,
                allow_redirects=False,
            )

            # Follow redirect with token preserved
            if response.status_code in (301, 302, 303, 307, 308):
                redirect_url = response.headers.get("Location")
                if redirect_url:
                    response = requests.get(
                        redirect_url,
                        headers=headers,
                        stream=True,
                        timeout=300,
                    )

            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded Sentinel-2 product {image_id} → {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error downloading product {image_id}: {e}")
            raise

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, image_id: str) -> dict:
        """Get detailed metadata for a product via OData."""
        url = (
            f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products('{image_id}')"
        )
        try:
            token = self._get_access_token()
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "id": data.get("Id"),
                "name": data.get("Name"),
                "content_type": data.get("ContentType"),
                "content_length": data.get("ContentLength"),
                "origin_date": data.get("OriginDate"),
                "publication_date": data.get("PublicationDate"),
                "modification_date": data.get("ModificationDate"),
                "online": data.get("Online"),
                "s3_path": data.get("S3Path"),
                "checksum": data.get("Checksum", []),
                "raw": data,
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {image_id}: {e}")
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_thumbnail_url(item: dict) -> str:
        """
        Extract the quicklook/thumbnail URL from an OData product item.

        OData returns Assets as a list when $expand=Assets is used.
        We look for an asset with Type == 'QUICKLOOK' and return its
        DownloadLink. Falls back to empty string if none found.
        """
        for asset in item.get("Assets", []):
            if asset.get("Type") == "QUICKLOOK":
                return asset.get("DownloadLink", "")
        return ""

    @staticmethod
    def _sentinel2_bands() -> List[str]:
        return [
            "B01",
            "B02",
            "B03",
            "B04",
            "B05",
            "B06",
            "B07",
            "B08",
            "B8A",
            "B09",
            "B10",
            "B11",
            "B12",
        ]


# Singleton instance
copernicus_service = CopernicusService()
