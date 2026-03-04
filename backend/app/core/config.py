from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # -------------------------------------------------------------------------
    # Metadatos de la aplicación — constantes, no cambian entre entornos
    # -------------------------------------------------------------------------
    PROJECT_NAME: str = "SR Agro Vision API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # -------------------------------------------------------------------------
    # Logging — opcional, por defecto INFO
    # -------------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # -------------------------------------------------------------------------
    # JWT — el algoritmo es fijo; el resto viene del .env
    # -------------------------------------------------------------------------
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = Field(min_length=1)
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # -------------------------------------------------------------------------
    # CORS — permite ajustes por entorno sin tocar código
    # -------------------------------------------------------------------------
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # -------------------------------------------------------------------------
    # Base de datos — obligatorio en .env
    # -------------------------------------------------------------------------
    DATABASE_URL: str

    # -------------------------------------------------------------------------
    # Almacenamiento — obligatorio en .env
    # -------------------------------------------------------------------------
    UPLOAD_DIR: str
    DOWNLOAD_DIR: str = "./downloads"  # Copernicus downloads saved here
    MAX_UPLOAD_SIZE: int
    SR_OUTPUT_DIR: str

    # -------------------------------------------------------------------------
    # Celery / Redis — obligatorio en .env
    # -------------------------------------------------------------------------
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # -------------------------------------------------------------------------
    # Copernicus API
    # URLs son constantes de la API pública — no deben cambiarse
    # Credenciales son opcionales
    # -------------------------------------------------------------------------
    COPERNICUS_API_URL: str = "https://catalogue.dataspace.copernicus.eu/odata/v1"
    COPERNICUS_DOWNLOAD_URL: str = "https://catalogue.dataspace.copernicus.eu/odata/v1"
    COPERNICUS_USER: Optional[str] = None
    COPERNICUS_PASS: Optional[str] = None

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent / ".env")
        case_sensitive = True


settings = Settings()
