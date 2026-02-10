from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "SR Agro Vision API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sr_agro.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Uploads
    UPLOAD_DIR: str = "backend/uploads"
    MAX_UPLOAD_SIZE: int = 524288000  # 500 MB
    
    # Celery / Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # SR Processing
    SR_OUTPUT_DIR: str = "backend/uploads/results"
    
    # Copernicus API
    COPERNICUS_CLIENT_ID: str = ""
    COPERNICUS_CLIENT_SECRET: str = ""
    COPERNICUS_API_URL: str = "https://catalogue.dataspace.copernicus.eu/resto/api"
    COPERNICUS_DOWNLOAD_URL: str = "https://zipper.dataspace.copernicus.eu/odata/v1"
    
    class Config:
        env_file = "backend/.env"
        case_sensitive = True

settings = Settings()
