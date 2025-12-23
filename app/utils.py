"""Utility functions for file validation and processing."""

import hashlib
import mimetypes
import uuid
from pathlib import Path

from app.config import settings
from app.exceptions import FileValidationError, UnsupportedFormatError

# Constants
CHUNK_SIZE = 4096  # For file reading/hashing
MAX_FILENAME_LENGTH = 255
DANGEROUS_CHARS = '<>:"|?*\x00'


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())


def validate_file_extension(filename: str) -> None:
    """Validate file extension against allowed formats using O(1) set lookup."""
    # Cache Path operations
    file_path = Path(filename)
    extension = file_path.suffix.lower()

    # O(1) set membership check (faster than list/tuple)
    if extension not in settings.ALLOWED_EXTENSIONS:
        # Only join when error occurs (lazy evaluation)
        allowed_str = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
        raise UnsupportedFormatError(
            f"File extension '{extension}' is not supported. "
            f"Allowed extensions: {allowed_str}"
        )


def validate_file_size(file_size: int) -> None:
    """Validate file size against maximum allowed size."""
    if file_size > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise FileValidationError(
            f"File size ({file_size / (1024 * 1024):.2f}MB) exceeds "
            f"maximum allowed size ({max_size_mb}MB)"
        )


def validate_audio_file(file_path: Path) -> None:
    """Comprehensive validation of audio file with optimized path operations."""
    # Cache Path methods for performance
    exists = file_path.exists
    is_file = file_path.is_file

    # Combine existence and file checks (short-circuit evaluation)
    if not (exists() and is_file()):
        error_msg = (
            f"File not found: {file_path}"
            if not exists()
            else f"Path is not a file: {file_path}"
        )
        raise FileValidationError(error_msg)

    validate_file_extension(file_path.name)

    # Cache stat() result to avoid multiple filesystem calls
    file_stat = file_path.stat()
    validate_file_size(file_stat.st_size)

    # Check MIME type - cache str conversion
    file_path_str = str(file_path)
    mime_type, _ = mimetypes.guess_type(file_path_str)
    if mime_type and not mime_type.startswith("audio/"):
        raise FileValidationError(
            f"File does not appear to be an audio file. Detected MIME type: {mime_type}"
        )


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file using optimized buffered I/O."""
    sha256_hash = hashlib.sha256()
    # Use larger buffer for better I/O performance
    buffer_size = max(CHUNK_SIZE, 65536)

    # Use buffered binary read for optimal performance
    with open(file_path, "rb", buffering=buffer_size) as f:
        # Use generator expression for memory efficiency
        # Read in optimized chunks
        for byte_block in iter(lambda: f.read(buffer_size), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other issues."""
    # Remove path components
    file_path = Path(filename)
    sanitized = file_path.name

    # Remove or replace dangerous characters using str.translate (more efficient)
    sanitized = sanitized.translate(
        str.maketrans(DANGEROUS_CHARS, "_" * len(DANGEROUS_CHARS))
    )

    # Limit length
    if len(sanitized) > MAX_FILENAME_LENGTH:
        sanitized_path = Path(sanitized)
        name, ext = sanitized_path.stem, sanitized_path.suffix
        sanitized = f"{name[: MAX_FILENAME_LENGTH - len(ext)]}{ext}"

    return sanitized
