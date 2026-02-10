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
            "bbox": [-59.5, -29.5, -55.5, -27.0],
            "description": "Corrientes, Argentina - Zona arrocera",
        },
        "rio_grande_agriculture": {
            "bbox": [-53.5, -30.5, -52.0, -29.0],  # Interior agrícola
            "description": "Rio Grande do Sul - Zona agrícola interior",
        },
        "valencia_spain": {
            "bbox": [-0.8, 38.8, 0.2, 39.8],
            "description": "Valencia, España",
        },
    }

    def __init__(self, username=None, password=None, output_dir="./downloads"):
        """
        Args:
            username: Usuario CDSE (opcional si está en .env como CDSE_CLIENT_ID)
            password: Contraseña CDSE (opcional si está en .env como CDSE_CLIENT_SECRET)
            output_dir: Directorio de descarga
        """
        # cdse-client usa CDSE_CLIENT_ID y CDSE_CLIENT_SECRET
        # Mantener compatibilidad con COPERNICUS_USER y COPERNICUS_PASS
        self.client_id = (
            username or os.getenv("CDSE_CLIENT_ID") or os.getenv("COPERNICUS_USER")
        )
        self.client_secret = (
            password or os.getenv("CDSE_CLIENT_SECRET") or os.getenv("COPERNICUS_PASS")
        )

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "❌ Credenciales no encontradas.\n\n"
                "Opciones:\n"
                "1. Crear archivo .env en la raíz del proyecto:\n"
                "   CDSE_CLIENT_ID=tu_usuario\n"
                "   CDSE_CLIENT_SECRET=tu_contraseña\n"
                "   (o usar COPERNICUS_USER/COPERNICUS_PASS)\n\n"
                "2. Pasar como argumentos:\n"
                "   --user tu_usuario --password tu_contraseña\n\n"
                "📝 Regístrate en:\n"
                "   https://dataspace.copernicus.eu/\n"
                "   (NOTA: Nuevo sistema, necesitas nueva cuenta)"
            )

        # Configurar variables de entorno para cdse-client
        os.environ["CDSE_CLIENT_ID"] = self.client_id
        os.environ["CDSE_CLIENT_SECRET"] = self.client_secret

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"✅ Credenciales cargadas: {self.client_id}")
        print(f"📁 Directorio de salida: {self.output_dir}")

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

        # Crear cliente
        client = CDSEClient(output_dir=str(self.output_dir))

        successful = 0
        failed = 0

        for idx, product in enumerate(products, 1):
            # Acceder a propiedades del objeto STAC Item
            props = product.properties if hasattr(product, "properties") else {}
            title = props.get("title", getattr(product, "id", f"product_{idx}"))
            date = props.get("datetime", "N/A")
            cloud = props.get("cloudCover", props.get("eo:cloud_cover", "N/A"))

            print(f"[{idx}/{len(products)}] {title}")
            print(f"   Fecha: {date}")
            print(f"   Nubes: {cloud}%")

            try:
                # Descargar producto
                result = client.download(product)

                if result:
                    print(f"   ✅ Descargado")
                    successful += 1
                else:
                    print(f"   ⚠️  No se pudo descargar")
                    failed += 1

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


def download_corrientes_data(
    output_dir="./data/satellite/raw",
    start_date="2023-09-01",
    end_date="2024-03-01",
    max_images=10,
):
    """
    Función helper para descargar imágenes de Corrientes

    Args:
        output_dir: Directorio de salida
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        max_images: Máximo a descargar
    """
    print("🌾 Descargando imágenes de Corrientes, Argentina")
    print("=" * 60)

    downloader = Sentinel2DownloaderCDSE(output_dir=output_dir)

    bbox = Sentinel2DownloaderCDSE.REGIONS["corrientes_argentina"]["bbox"]

    products = downloader.search_images(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        cloud_cover_max=30,  # Corrientes tiene mucha nubosidad
    )

    if len(products) == 0:
        return

    downloader.download_products(products, max_downloads=max_images)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descargar imágenes Sentinel-2 desde Copernicus Data Space Ecosystem"
    )
    parser.add_argument(
        "--region",
        type=str,
        default="corrientes_argentina",
        choices=list(Sentinel2DownloaderCDSE.REGIONS.keys()),
        help="Región a descargar",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./data/satellite/raw",
        help="Directorio de salida",
    )
    parser.add_argument(
        "--start-date", type=str, default="2023-09-01", help="Fecha inicio (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", type=str, default="2024-03-01", help="Fecha fin (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--max-images", type=int, default=10, help="Máximo número de imágenes"
    )
    parser.add_argument(
        "--cloud-max", type=int, default=30, help="Cobertura de nubes máxima (0-100)"
    )
    parser.add_argument("--user", type=str, help="Usuario CDSE")
    parser.add_argument("--password", type=str, help="Contraseña CDSE")

    args = parser.parse_args()

    downloader = Sentinel2DownloaderCDSE(
        username=args.user, password=args.password, output_dir=args.output
    )

    bbox = Sentinel2DownloaderCDSE.REGIONS[args.region]["bbox"]
    print(f"📍 Región: {Sentinel2DownloaderCDSE.REGIONS[args.region]['description']}")

    products = downloader.search_images(
        bbox=bbox,
        start_date=args.start_date,
        end_date=args.end_date,
        cloud_cover_max=args.cloud_max,
        max_results=args.max_images * 3,  # Buscar más para compensar filtros
    )

    if len(products) > 0:
        downloader.download_products(products, max_downloads=args.max_images)
