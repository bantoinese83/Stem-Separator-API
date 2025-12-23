"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from loguru import logger

# Import TensorFlow compatibility patch early (before any Spleeter imports)
import app.tensorflow_compat  # noqa: F401

from app.config import settings
from app.logging_config import setup_logging
from app.models import ErrorResponse
from app.routes import health, separate

# Setup logging first
setup_logging()
logger = logger.bind(name=__name__)

# Patch tensorflow if it's already imported
app.tensorflow_compat.patch_tensorflow_estimator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(
        "Starting application",
        version=settings.API_VERSION,
        debug=settings.DEBUG,
    )

    # Preload models (optional, can be done lazily)
    try:
        logger.info("Audio service initialized")
    except Exception as e:
        logger.exception(
            "Failed to initialize audio service",
            error=str(e),
        )

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "separation",
            "description": "Audio stem separation operations. Upload audio files and separate them into individual instrument/vocal tracks.",
        },
        {
            "name": "health",
            "description": "Health and readiness checks for monitoring and service discovery.",
        },
    ],
    contact={
        "name": "API Support",
        "url": "https://github.com/deezer/spleeter",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(
        "Validation error",
        path=request.url.path,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            error="Request validation failed",
            error_code="VALIDATION_ERROR",
            details={"errors": exc.errors()},
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.exception(
        "Unhandled exception",
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"error": str(exc)} if settings.DEBUG else None,
        ).model_dump(),
    )


# Include routers
app.include_router(health.router)
app.include_router(separate.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # Use our custom logging
    )
