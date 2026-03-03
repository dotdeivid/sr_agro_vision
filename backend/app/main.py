from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

# Compute .env path from this file's location: backend/app/main.py → .parent.parent = backend/
# Note: config.py does the same from its own depth (backend/app/core/ → .parent x3)
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# 1. Load .env early — must happen before any module reads os.getenv(...)
load_dotenv(str(_ENV_FILE), override=False)

# 2. Standalone logger — import after dotenv so LOG_LEVEL is already set
from .core.logger import get_logger  # noqa: E402

_logger = get_logger("sr_agro.startup")

# 3. Import settings — catch ValidationError so missing vars are logged clearly
try:
    from app.core.config import settings

except ValidationError as exc:
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        _logger.error(f"Missing required environment variable: {field}")
    _logger.critical(
        "Application cannot start — fix the environment variables above",
        extra={"missing_count": len(exc.errors())},
    )
    raise SystemExit(1)

# 4. Build the FastAPI app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse

from .database import engine, Base
from .api.v1.router import api_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url=None,  # disabled — served manually below with a pinned CDN
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

_logger.info(
    "Application started",
    extra={"version": settings.VERSION, "docs": "/docs", "redoc": "/redoc"},
)


@app.get("/redoc", include_in_schema=False)
async def redoc_html() -> HTMLResponse:
    """
    Serve ReDoc with a pinned CDN URL.
    FastAPI's default uses redoc@next which Chrome blocks with ERR_BLOCKED_BY_ORB
    because the CDN returns the JS with an incorrect Content-Type header.
    """
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
    )


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "SR Agro Vision API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
