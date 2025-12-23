"""Health check routes."""

from fastapi import APIRouter
from loguru import logger

from app.config import settings
from app.models import HealthResponse

logger = logger.bind(name=__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="""
    Check if the API service is running and healthy.
    
    This endpoint provides basic health status information including:
    - Service status (healthy/unhealthy)
    - API version
    - Service name
    
    **Use Cases:**
    - Load balancer health checks
    - Monitoring and alerting systems
    - Service discovery
    
    **Response:**
    Returns 200 OK if the service is healthy, with status information in the response body.
    """,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "service": "stem-separator-api",
                    }
                }
            },
        },
    },
    tags=["health"],
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the current health status of the API service.
    This is a lightweight endpoint that doesn't perform any heavy checks,
    making it suitable for frequent monitoring.
    """
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION,
        service=settings.API_TITLE,
    )


@router.get(
    "/ready",
    summary="Readiness check",
    description="""
    Check if the API is ready to process separation requests.
    
    This endpoint performs a more thorough check than `/health` by verifying:
    - Service is running
    - Spleeter models are loaded and available
    - Audio service is initialized
    
    **Use Cases:**
    - Kubernetes readiness probes
    - Pre-flight checks before sending requests
    - Verifying model availability
    
    **Response States:**
    - `ready`: Service is fully operational and can process requests
    - `loading`: Service is starting up, models are being loaded
    - `not_ready`: Service is not ready (error occurred)
    """,
    responses={
        200: {
            "description": "Readiness status",
            "content": {
                "application/json": {
                    "examples": {
                        "ready": {
                            "summary": "Service is ready",
                            "value": {
                                "status": "ready",
                                "models_loaded": True,
                                "version": "1.0.0",
                            },
                        },
                        "loading": {
                            "summary": "Service is loading",
                            "value": {
                                "status": "loading",
                                "models_loaded": False,
                                "version": "1.0.0",
                            },
                        },
                        "not_ready": {
                            "summary": "Service is not ready",
                            "value": {
                                "status": "not_ready",
                                "error": "Model loading failed",
                                "version": "1.0.0",
                            },
                        },
                    }
                }
            },
        },
    },
    tags=["health"],
)
async def readiness_check() -> dict:
    """
    Readiness check endpoint.

    Verifies that the service is fully ready to process audio separation requests.
    This includes checking that Spleeter models are loaded and the audio service
    is properly initialized.
    """
    # Check if models are loaded
    try:
        from app.services.audio_service import audio_service

        # Try to access separators (this will trigger model loading if needed)
        models_loaded = len(audio_service.separators) > 0

        return {
            "status": "ready" if models_loaded else "loading",
            "models_loaded": models_loaded,
            "version": settings.API_VERSION,
        }
    except Exception as e:
        logger.exception("Readiness check failed", error=str(e))
        return {
            "status": "not_ready",
            "error": str(e),
            "version": settings.API_VERSION,
        }
