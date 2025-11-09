"""
AION - AI Personal Assistant with Long-Term Memory
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import get_settings
from src.presentation.api.routes import chat, document, entity, health, memory, obsidian_sync, integrations, prompts
from src.shared.exceptions import AIONException, get_http_status_code
from src.shared.logging import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    logger.info(
        "application_starting",
        app_name=settings.app.app_name,
        version=settings.app.app_version,
        environment=settings.app.environment,
    )

    # TODO: Initialize database connections, collections, etc.
    # await initialize_infrastructure()

    yield

    # Shutdown
    logger.info("application_shutting_down")
    # TODO: Close connections, cleanup resources
    # await cleanup_infrastructure()


# Create FastAPI application
settings = get_settings()
app = FastAPI(
    title=settings.app.app_name,
    version=settings.app.app_version,
    description="AI Personal Assistant with Long-Term Memory and Knowledge Base",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Add CORS middleware
# In development, allow all origins for easier frontend development
cors_origins = ["*"] if settings.is_development else settings.api.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.api.cors_allow_credentials,
    allow_methods=settings.api.cors_allow_methods,
    allow_headers=settings.api.cors_allow_headers,
)


# Exception handlers
@app.exception_handler(AIONException)
async def aion_exception_handler(request, exc: AIONException):
    """Handle AION custom exceptions."""
    status_code = get_http_status_code(exc)

    logger.error(
        "aion_exception",
        exception_type=type(exc).__name__,
        message=exc.message,
        details=exc.details,
        status_code=status_code,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "unexpected_exception",
        exception_type=type(exc).__name__,
        message=str(exc),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {} if settings.is_production else {"error": str(exc)},
        },
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(memory.router, prefix="/api/v1", tags=["Memory"])
app.include_router(document.router, prefix="/api/v1", tags=["Documents"])
app.include_router(entity.router, prefix="/api/v1", tags=["Entities"])
app.include_router(obsidian_sync.router, prefix="/api/v1", tags=["Obsidian Sync"])
app.include_router(integrations.router, prefix="/api/v1", tags=["Integrations"])
app.include_router(prompts.router, prefix="/api/v1", tags=["Prompts"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": settings.app.app_name,
        "version": settings.app.app_version,
        "status": "operational",
        "docs": "/docs" if settings.is_development else "disabled in production",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.api.api_host,
        port=settings.api.api_port,
        reload=settings.api.api_reload and settings.is_development,
        workers=settings.api.api_workers,
        log_level=settings.app.log_level.lower(),
    )
