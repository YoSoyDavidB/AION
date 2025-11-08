"""
Health check endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from src.config.settings import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""

    status: str
    version: str
    environment: str
    services: dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns application status and version.
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        version=settings.app.app_version,
        environment=settings.app.environment,
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check endpoint.

    Returns application status, version, and service statuses.
    """
    settings = get_settings()

    # TODO: Add actual service health checks
    services = {
        "qdrant": "unknown",  # TODO: Check Qdrant connection
        "neo4j": "unknown",  # TODO: Check Neo4j connection
        "postgres": "unknown",  # TODO: Check PostgreSQL connection
        "openrouter": "unknown",  # TODO: Check OpenRouter API
    }

    return DetailedHealthResponse(
        status="healthy",
        version=settings.app.app_version,
        environment=settings.app.environment,
        services=services,
    )
