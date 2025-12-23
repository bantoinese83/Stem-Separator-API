"""Pydantic models for request/response validation."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class StemType(str, Enum):
    """Available stem separation types."""

    TWO_STEMS = "2stems"
    FOUR_STEMS = "4stems"
    FIVE_STEMS = "5stems"

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


class SeparationRequest(BaseModel):
    """Request model for stem separation."""

    stems: StemType = Field(
        default=StemType.TWO_STEMS,
        description="Number of stems to separate (2stems, 4stems, or 5stems)",
    )
    bitrate: Optional[str] = Field(
        default="320k",
        description="Audio bitrate for output files",
    )
    format: Optional[str] = Field(
        default="wav",
        description="Output audio format (wav, mp3, etc.)",
    )

    @field_validator("bitrate")
    @classmethod
    def validate_bitrate(cls, v: Optional[str]) -> Optional[str]:
        """Validate bitrate format."""
        if v is None:
            return v
        # Use any() for cleaner boolean check
        if not (v.endswith("k") or v.isdigit()):
            raise ValueError("Bitrate must be in format like '320k' or a number")
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate audio format."""
        if v is None:
            return v
        allowed_formats = {"wav", "mp3", "flac", "m4a", "aac", "ogg"}
        v_lower = v.lower()
        if v_lower not in allowed_formats:
            raise ValueError(
                f"Format must be one of: {', '.join(sorted(allowed_formats))}"
            )
        return v_lower


class SeparationResponse(BaseModel):
    """Response model for successful separation."""

    success: bool = Field(
        default=True,
        description="Indicates if the separation was successful",
        examples=[True],
    )
    message: str = Field(
        description="Human-readable success message",
        examples=["Successfully separated audio into 2stems"],
    )
    job_id: str = Field(
        description="Unique identifier for this separation job. Use this to download output files.",
        examples=["181543dd-c632-4a42-bb8d-f3ca74c763cd"],
    )
    stems: StemType = Field(
        description="The stem type that was used for separation",
        examples=[StemType.TWO_STEMS],
    )
    output_files: list[str] = Field(
        description="List of generated output file paths. Use these with the download endpoint.",
        examples=[["vocals.wav", "accompaniment.wav"]],
    )
    processing_time: Optional[float] = Field(
        default=None,
        description="Processing time in seconds",
        examples=[12.45],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Successfully separated audio into 2stems",
                "job_id": "181543dd-c632-4a42-bb8d-f3ca74c763cd",
                "stems": "2stems",
                "output_files": ["vocals.wav", "accompaniment.wav"],
                "processing_time": 12.45,
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(
        default=False,
        description="Always false for error responses",
        examples=[False],
    )
    error: str = Field(
        description="Human-readable error message",
        examples=["File size exceeds maximum allowed size (100MB)"],
    )
    error_code: str = Field(
        description="Machine-readable error code for programmatic handling",
        examples=["FILE_TOO_LARGE", "INVALID_FORMAT", "PROCESSING_ERROR"],
    )
    details: Optional[dict] = Field(
        default=None,
        description="Additional error details (only in debug mode)",
        examples=[{"original_error": "ValueError: Invalid audio format"}],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": "File size exceeds maximum allowed size (100MB)",
                "error_code": "FILE_TOO_LARGE",
                "details": None,
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(
        default="healthy",
        description="Service health status",
        examples=["healthy"],
    )
    version: str = Field(
        description="API version number",
        examples=["1.0.0"],
    )
    service: str = Field(
        default="stem-separator-api",
        description="Service name",
        examples=["stem-separator-api"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "service": "stem-separator-api",
            }
        }
    }
