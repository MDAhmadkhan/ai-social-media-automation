from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import ensure_indexes
from app.core.logging import configure_logging
from app.middlewares.security_headers import security_headers_middleware

settings = get_settings()
configure_logging()
logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Production-ready AI social media automation API with content detection, AI generation, scheduling, publishing, and analytics.",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(security_headers_middleware)

Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.local_storage_path), name="storage")
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.on_event("startup")
async def on_startup() -> None:
    await ensure_indexes()
    logger.info("application_started", environment=settings.environment)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
