"""
Descarga imágenes Sentinel-2 usando Copernicus Data Space Ecosystem (CDSE)
Actualizado para usar cdse-client (reemplazo de sentinelsat)
"""

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import argparse

# Cargar credenciales desde .env
load_dotenv()


class Sentinel2DownloaderCDSE:
    """Descarga imágenes Sentinel-2 usando CDSE (nuevo sistema)"""

    # Regiones predefinidas
    REGIONS = {
        "corrientes_argentina": {
            # Núcleo arrocero: departamentos Mercedes y Curuzú Cuatiá (INTA, FAUBA)
            "bbox": [-58.5, -30.0, -56.5, -28.0],
            "description": "Corrientes, Argentina - Zona arrocera (Mercedes / Curuzú Cuatiá)",
        },
        "rio_grande_agriculture": {
            # Passo Fundo / Erechim — principal región sojera y triguera del estado
            "bbox": [-53.5, -29.0, -52.0, -27.5],
            "description": "Rio Grande do Sul - Passo Fundo, zona soja/trigo",
        },
        "valencia_spain": {
            # Parque Natural Albufera + L'Horta (arrozales y huerta al sur de Valencia)
            "bbox": [-0.5, 39.1, 0.1, 39.5],
            "description": "Valencia, España - Arrozales Albufera y Huerta",
        },
        "pampa_humeda_argentina": {
            # Triángulo núcleo sojero: Pergamino-Junín-Rosario (norte Bs.As + sur Santa Fe)
            "bbox": [-62.0, -34.5, -59.5, -32.0],
            "description": "Pampa Húmeda - Núcleo sojero (Pergamino / Rosario)",
        },
        "mendoza_vinedos": {
            # Luján de Cuyo + Maipú — corazón vitivinícola de Mendoza
            "bbox": [-69.3, -33.5, -68.5, -32.9],
            "description": "Mendoza - Viñedos Luján de Cuyo y Maipú",
        },
        "mato_grosso_soja": {
            "bbox": [-58.0, -14.0, -54.0, -11.0],
            "description": "Mato Grosso - Soja intensiva (corazón del Cerrado)",
        },
        "sao_paulo_cana": {
            # Piracicaba (22.73°S/47.65°W) + Ribeirão Preto (21.18°S/47.81°W)
            "bbox": [-49.0, -22.8, -47.0, -20.8],
            "description": "São Paulo - Caña de azúcar (Piracicaba / Ribeirão Preto)",
        },
        "valle_central_chile": {
            # Curicó (-34.98°S) + Talca (-35.43°S): viñedos, frutales, cereales
            "bbox": [-71.8, -36.0, -70.5, -34.5],
            "description": "Valle Central Chile - Viñedos y frutales (Curicó / Talca)",
        },
        "ica_peru": {
            # Franja costera irrigada: espárragos y uva de mesa (city -14.07°S/-75.73°W)
            "bbox": [-76.0, -14.5, -75.0, -13.5],
            "description": "Ica, Perú - Espárragos y uvas (desierto costero irrigado)",
        },
        "llanos_colombia": {
            "bbox": [-73.5, 4.0, -71.0, 6.0],
            "description": "Llanos Orientales Colombia - Arroz/Palma",
        },
    }

    def __init__(self, username=None, password=None, output_dir="./downloads"):
        """
        Args:
            username: Email CDSE (opcional, lee de COPERNICUS_USER en .env)
            password: Contraseña CDSE (opcional, lee de COPERNICUS_PASS en .env)
            output_dir: Directorio de descarga
        """
        # Credenciales de usuario CDSE (email + password) — para descarga via OData
        self.username = (
            username or os.getenv("COPERNICUS_USER") or os.getenv("CDSE_USER")
        )
        self.password = (
            password or os.getenv("COPERNICUS_PASS") or os.getenv("CDSE_PASS")
        )

        # OAuth client (sh-xxx) — para búsqueda via cdse-client/STAC
        self.client_id = os.getenv("CDSE_CLIENT_ID")
        self.client_secret = os.getenv("CDSE_CLIENT_SECRET")

        # cdse-client necesita estas vars para la búsqueda STAC
        if self.client_id:
            os.environ["CDSE_CLIENT_ID"] = self.client_id
        if self.client_secret:
            os.environ["CDSE_CLIENT_SECRET"] = self.client_secret

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_oauth_token(self):
        """
        Obtiene token OAuth para OData/descarga usando grant_type=password.

        IMPORTANTE: El endpoint zipper de CDSE requiere un token obtenido con
        usuario+contraseña (grant_type=password, client_id=cdse-public),
        NO con client_credentials (esos son para Sentinel Hub API solamente).

        Ver doc oficial:
        https://documentation.dataspace.copernicus.eu/APIs/OData.html#product-download
        """
        import requests

        if not self.username or not self.password:
            raise RuntimeError(
                "❌ Credenciales de usuario requeridas para descarga.\n"
                "   Agrega al .env:\n"
                "   COPERNICUS_USER=tu_email@ejemplo.com\n"
                "   COPERNICUS_PASS=tu_contraseña"
            )

        token_url = (
            "https://identity.dataspace.copernicus.eu"
            "/auth/realms/CDSE/protocol/openid-connect/token"
        )
        data = {
            "grant_type": "password",  # requerido por OData/zipper
            "client_id": "cdse-public",  # client_id público fijo de CDSE
            "username": self.username,
            "password": self.password,
        }
        try:
            resp = requests.post(token_url, data=data, timeout=30)
            resp.raise_for_status()
            token = resp.json()["access_token"]
            print(f"   ✅ Token OAuth (password grant) obtenido")
            return token
        except Exception as e:
            raise RuntimeError(
                f"❌ No se pudo obtener token: {e}\n"
                "   Verifica COPERNICUS_USER y COPERNICUS_PASS en .env"
            )

    def _get_product_uuid(self, product_name, requests_module):
        """
        Consulta el catálogo OData de CDSE para obtener el UUID real del producto.
        El zipper endpoint necesita el UUID, no el nombre .SAFE.

        Args:
            product_name: Nombre del producto (ej: S2A_MSIL2A_....SAFE)
            requests_module: módulo requests ya importado

        Returns:
            str: UUID del producto o None si no se encontró
        """
        odata_url = (
            "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
            f"?$filter=Name eq '{product_name}'&$select=Id,Name"
        )
        try:
            resp = requests_module.get(odata_url, timeout=20)
            resp.raise_for_status()
            items = resp.json().get("value", [])
            if items:
                return items[0]["Id"]
            return None
        except Exception as e:
            print(f"   ⚠️  No se pudo obtener UUID vía OData: {e}")
            return None

    def search_images(
        self, bbox, start_date, end_date, cloud_cover_max=30, max_results=100
    ):
        """
        Busca imágenes Sentinel-2 en CDSE

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'
            cloud_cover_max: Porcentaje máximo de nubes (0-100)
            max_results: Máximo número de resultados

        Returns:
            List de productos encontrados
        """
        try:
            from cdse import CDSEClient
        except ImportError:
            raise ImportError(
                "cdse-client no está instalado.\n"
                "Instalar con: pip install cdse-client"
            )

        print(f"\n🔍 Buscando imágenes Sentinel-2...")
        print(f"   Región: {bbox}")
        print(f"   Fechas: {start_date} a {end_date}")
        print(f"   Nubes máx: {cloud_cover_max}%")

        # Convertir formato YYYYMMDD → YYYY-MM-DD si es necesario (CDSE exige ISO 8601)
        def to_iso(date_str):
            date_str = str(date_str).strip()
            if len(date_str) == 8 and "-" not in date_str:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            return date_str

        start_date = to_iso(start_date)
        end_date = to_iso(end_date)

        # Crear cliente usando credenciales de env vars
        client = CDSEClient(output_dir=str(self.output_dir))

        # Buscar productos
        products = client.search(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            collection="sentinel-2-l2a",  # L2A = corregido atmosféricamente
            cloud_cover_max=cloud_cover_max,
            limit=max_results,
        )

        # Convertir a lista
        products_list = list(products)

        print(f"✅ Encontradas {len(products_list)} imágenes L2A")

        if len(products_list) == 0:
            print("\n⚠️  No se encontraron imágenes. Intenta:")
            print("   - Ampliar rango de fechas")
            print("   - Aumentar cloud_cover_max (hasta 50-60)")
            print("   - Probar otra región")
        else:
            # Mostrar algunos detalles
            for i, product in enumerate(products_list[:3], 1):
                # Los productos son objetos STAC Item de cdse-client
                props = product.properties if hasattr(product, "properties") else {}
                title = props.get("title", getattr(product, "id", "N/A"))
                cloud = props.get("cloudCover", props.get("eo:cloud_cover", "N/A"))
                print(f"   [{i}] {title} (nubes: {cloud}%)")
            if len(products_list) > 3:
                print(f"   ... y {len(products_list) - 3} más")

        return products_list

    def download_products(self, products, max_downloads=None):
        """
        Descarga productos de CDSE

        Args:
            products: Lista de productos (de search_images)
            max_downloads: Máximo a descargar (None = todos)
        """
        try:
            from cdse import CDSEClient
        except ImportError:
            raise ImportError(
                "cdse-client no está instalado.\n"
                "Instalar con: pip install cdse-client"
            )

        if max_downloads:
            products = products[:max_downloads]

        print(f"\n📥 Descargando {len(products)} productos...")
        print(f"   Destino: {self.output_dir}")
        print(f"   Esto puede tardar varias horas...\n")

        # Obtener token OAuth una vez para toda la sesión de descarga
        import requests
        import tqdm

        token = self._get_oauth_token()
        headers = {"Authorization": f"Bearer {token}"}
        # Zipper endpoint DIRECTO (no usar catalogue que redirige y Python requests
        # pierde el header Authorization en redirect cross-domain)
        # Fix.md ref: https://documentation.dataspace.copernicus.eu/APIs/OData.html
        download_url = "https://zipper.dataspace.copernicus.eu/odata/v1/Products({})"

        successful = 0
        failed = 0

        for idx, product in enumerate(products, 1):
            props = product.properties if hasattr(product, "properties") else {}
            title = props.get("title", getattr(product, "id", f"product_{idx}"))
            product_id = getattr(product, "id", None)
            date = props.get("datetime", "N/A")
            cloud = props.get("cloudCover", props.get("eo:cloud_cover", "N/A"))

            print(f"[{idx}/{len(products)}] {title}")
            print(f"   Fecha: {date}")
            print(f"   Nubes: {cloud}%")

            if not product_id:
                print(f"   ⚠️  Sin ID, no se puede descargar")
                failed += 1
                continue

            try:
                # El product.id puede ser el nombre .SAFE, no el UUID.
                # Consultamos OData para obtener el UUID real.
                print(f"   🔍 Buscando UUID en catálogo...")
                uuid = self._get_product_uuid(product_id, requests)
                if not uuid:
                    # Intentar también con el título
                    uuid = self._get_product_uuid(title, requests)
                if not uuid:
                    print(f"   ❌ No se pudo encontrar UUID para el producto")
                    failed += 1
                    continue
                print(f"   UUID: {uuid}")

                # Descarga directa al zipper endpoint con token OAuth
                url = download_url.format(uuid) + "/$value"
                dest = self.output_dir / f"{title}.zip"

                with requests.get(url, headers=headers, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("content-length", 0))
                    with open(dest, "wb") as f, tqdm.tqdm(
                        total=total, unit="B", unit_scale=True, desc=f"   {title[:40]}"
                    ) as bar:
                        for chunk in r.iter_content(chunk_size=65536):
                            f.write(chunk)
                            bar.update(len(chunk))

                print(f"   ✅ Descargado: {dest.name}")
                successful += 1

            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed += 1
                continue

        print(f"\n{'='*60}")
        print(f"✅ Descarga completada")
        print(f"{'='*60}")
        print(f"Exitosas: {successful}")
        print(f"Fallidas: {failed}")
        print(f"Ubicación: {self.output_dir}")
        print(f"{'='*60}")


def main(args=None):
    """
    Función main para ser llamada desde main.py o directamente

    Args:
        args: Argumentos parseados (opcional, si None se parsean desde consola)
    """
    import argparse

    if args is None:
        parser = argparse.ArgumentParser(
            description="Descargar imágenes Sentinel-2 desde Copernicus CDSE"
        )
        parser.add_argument(
            "--region",
            type=str,
            required=True,
            choices=list(Sentinel2DownloaderCDSE.REGIONS.keys()),
            help="Región predefinida a descargar",
        )
        parser.add_argument(
            "--output", type=str, default="data/raw", help="Directorio de salida"
        )
        parser.add_argument(
            "--start-date", type=str, default="20230901", help="Fecha inicio (YYYYMMDD)"
        )
        parser.add_argument(
            "--end-date", type=str, default="20240301", help="Fecha fin (YYYYMMDD)"
        )
        parser.add_argument(
            "--cloud-max", type=int, default=20, help="Nubosidad máxima (%)"
        )
        parser.add_argument(
            "--max-images", type=int, default=10, help="Máximo de imágenes a descargar"
        )

        args = parser.parse_args()

    # Inicializar downloader
    downloader = Sentinel2DownloaderCDSE(output_dir=args.output)

    # Obtener bbox de región
    bbox = Sentinel2DownloaderCDSE.REGIONS[args.region]["bbox"]

    print(f"\n{'='*60}")
    print(f"🛰️  SENTINEL-2 DOWNLOAD")
    print(f"{'='*60}")
    print(f"📍 Región: {Sentinel2DownloaderCDSE.REGIONS[args.region]['description']}")

    products = downloader.search_images(
        bbox=bbox,
        start_date=args.start_date,
        end_date=args.end_date,
        cloud_cover_max=args.cloud_max,
        max_results=args.max_images * 3,
    )

    if len(products) > 0:
        downloader.download_products(products, max_downloads=args.max_images)


if __name__ == "__main__":
    main()
