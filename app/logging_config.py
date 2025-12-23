"""Structured logging configuration using Loguru."""

import sys

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    """Configure structured logging using Loguru."""
    # Remove default handler
    logger.remove()

    # Determine log level
    log_level = settings.LOG_LEVEL.upper()

    # Console handler with colored output for development, JSON for production
    if settings.LOG_FORMAT.lower() == "json":
        # Use serialize=True for JSON output instead of custom format
        console_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}"
    else:
        # Pretty format with colors for development
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # Add console handler
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=settings.LOG_FORMAT.lower() != "json",
        serialize=settings.LOG_FORMAT.lower() == "json",
    )

    # File handler with rotation
    log_file = settings.LOG_DIR / settings.LOG_FILE
    # Convert bytes to MB for loguru rotation format
    rotation_size_mb = settings.LOG_MAX_BYTES / (1024 * 1024)
    logger.add(
        str(log_file),
        format=console_format,
        level=log_level,
        rotation=f"{rotation_size_mb:.0f} MB",
        retention=settings.LOG_BACKUP_COUNT,
        compression="zip",
        serialize=settings.LOG_FORMAT.lower() == "json",
        encoding="utf-8",
        enqueue=True,  # Thread-safe logging
    )

    # Configure third-party loggers
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": log_level,
                "format": console_format,
            }
        ]
    )

    # Suppress verbose third-party loggers
    logger.add(
        sys.stderr,
        level="WARNING",
        filter=lambda record: record["name"].startswith(
            ("uvicorn", "spleeter", "tensorflow")
        ),
    )

    logger.info(
        "Logging configured with Loguru",
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        log_file=str(log_file),
    )


def get_logger(name: str):
    """Get a logger instance with the given name (for compatibility)."""
    return logger.bind(name=name)
