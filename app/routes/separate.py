"""Routes for audio stem separation."""

from pathlib import Path as PathLib
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import FileResponse

from loguru import logger

from app.config import settings
from app.exceptions import FileValidationError, StemSeparatorException
from app.models import ErrorResponse, SeparationResponse, StemType
from app.services.audio_service import audio_service
from app.utils import (
    generate_job_id,
    sanitize_filename,
    validate_audio_file,
    validate_file_extension,
)

# Constants
FILE_CHUNK_SIZE = 8192  # For reading uploaded files

# Bind logger with module name
logger = logger.bind(name=__name__)

router = APIRouter(prefix="/api/v1", tags=["separation"])


@router.post(
    "/separate",
    response_model=SeparationResponse,
    status_code=status.HTTP_200_OK,
    summary="Separate audio file into stems",
    description="""
    Upload an audio file and separate it into individual stems using Spleeter's deep learning models.
    
    **Supported Audio Formats:**
    - MP3, WAV, FLAC, M4A, AAC, OGG
    
    **Stem Options:**
    - **2stems**: Separates into vocals and accompaniment
    - **4stems**: Separates into vocals, drums, bass, and other
    - **5stems**: Separates into vocals, drums, bass, piano, and other
    
    **Process:**
    1. Upload your audio file (max size: 100MB)
    2. Choose stem type, bitrate, and output format
    3. Receive a job ID and list of output files
    4. Download individual stems using the download endpoint
    
    **Performance:**
    - Processing time depends on audio length and stem type
    - Typical processing: 10-30 seconds for a 3-minute song
    - Files are temporarily stored and can be cleaned up automatically
    """,
    responses={
        200: {
            "description": "Separation completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Successfully separated audio into 2stems",
                        "job_id": "181543dd-c632-4a42-bb8d-f3ca74c763cd",
                        "stems": "2stems",
                        "output_files": ["vocals.wav", "accompaniment.wav"],
                        "processing_time": 12.45,
                    }
                }
            },
        },
        400: {
            "description": "Bad request - invalid file or parameters",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "File size exceeds maximum allowed size (100MB)",
                        "error_code": "FILE_TOO_LARGE",
                    }
                }
            },
        },
        422: {
            "description": "Validation error - invalid request format",
        },
        500: {
            "description": "Internal server error during processing",
        },
    },
    tags=["separation"],
)
async def separate_audio(
    file: UploadFile = File(
        ...,
        description="Audio file to separate. Supported formats: MP3, WAV, FLAC, M4A, AAC, OGG. Maximum size: 100MB.",
        examples=["song.mp3"],
    ),
    stems: StemType = Query(
        default=StemType.TWO_STEMS,
        description="Number of stems to separate. Options: 2stems (vocals + accompaniment), 4stems (vocals + drums + bass + other), 5stems (vocals + drums + bass + piano + other)",
        examples=[StemType.TWO_STEMS],
    ),
    bitrate: str = Query(
        default="320k",
        description="Output audio bitrate. Format: number followed by 'k' (e.g., '320k', '192k') or just a number.",
        examples=["320k", "192k", "256k"],
    ),
    format: str = Query(
        default="wav",
        description="Output audio format. Supported: wav, mp3, flac, m4a, aac, ogg",
        examples=["wav", "mp3"],
    ),
) -> SeparationResponse:
    """
    Separate uploaded audio file into individual stems using Spleeter.

    This endpoint processes an audio file and separates it into individual instrument/vocal tracks.
    The separation uses pre-trained deep learning models that can isolate different components
    of a mixed audio recording.

    **Example Usage:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/separate?stems=2stems&bitrate=320k&format=wav" \\
         -H "accept: application/json" \\
         -H "Content-Type: multipart/form-data" \\
         -F "file=@song.mp3"
    ```

    **Response:**
    The response includes a unique `job_id` that you can use to download individual stem files.
    Each stem file is available via the download endpoint using the job_id and filename.

    **Error Handling:**
    - File too large: Returns 400 with FILE_TOO_LARGE error code
    - Invalid format: Returns 400 with INVALID_FORMAT error code
    - Processing error: Returns 500 with INTERNAL_ERROR error code
    """
    job_id = generate_job_id()
    temp_input_file: Optional[Path] = None
    output_dir: Optional[Path] = None

    try:
        logger.info(
            "Received separation request",
            job_id=job_id,
            filename=file.filename,
            content_type=file.content_type,
            stems=stems.value,
        )

        # Validate file
        if not file.filename:
            raise FileValidationError("Filename is required")

        sanitized_filename = sanitize_filename(file.filename)
        validate_file_extension(sanitized_filename)

        # Save uploaded file temporarily
        temp_input_file = (
            PathLib(settings.UPLOAD_DIR) / f"{job_id}_{sanitized_filename}"
        )

        # Read file in chunks to handle large files efficiently
        # Use buffered I/O for better performance
        max_size = settings.MAX_UPLOAD_SIZE
        max_size_mb = max_size / (1024 * 1024)
        # Use larger buffer for better I/O performance (64KB is optimal for most systems)
        buffer_size = max(FILE_CHUNK_SIZE, 65536)

        # Use binary mode with buffering for optimal performance
        with open(temp_input_file, "wb", buffering=buffer_size) as f:
            file_size = 0
            # Read in optimized chunks
            while chunk := await file.read(buffer_size):
                chunk_size = len(chunk)
                file_size += chunk_size
                # Early exit check before write for better performance
                if file_size > max_size:
                    raise FileValidationError(
                        f"File size exceeds maximum allowed size ({max_size_mb}MB)"
                    )
                f.write(chunk)

        # Validate saved file
        validate_audio_file(temp_input_file)

        # Create output directory for this job
        output_dir = PathLib(settings.OUTPUT_DIR) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Perform separation
        result = audio_service.separate_audio(
            input_file=temp_input_file,
            output_dir=output_dir,
            stems=stems,
            bitrate=bitrate,
            format=format,
            job_id=job_id,
        )

        # Build response
        response = SeparationResponse(
            success=True,
            message=f"Successfully separated audio into {stems.value}",
            job_id=result["job_id"],
            stems=result["stems"],
            output_files=result["output_files"],
            processing_time=result["processing_time"],
        )

        logger.info(
            "Separation request completed successfully",
            job_id=job_id,
            processing_time=result["processing_time"],
        )

        return response

    except StemSeparatorException as e:
        logger.error(
            "Separation request failed",
            job_id=job_id,
            error=e.message,
            error_code=e.error_code,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error=e.message,
                error_code=e.error_code,
            ).model_dump(),
        )

    except Exception as e:
        logger.exception(
            "Unexpected error during separation",
            job_id=job_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error during processing",
                error_code="INTERNAL_ERROR",
                details={"original_error": str(e)},
            ).model_dump(),
        )

    finally:
        # Cleanup temporary files - combine conditionals for cleaner code
        if (
            settings.CLEANUP_AFTER_PROCESSING
            and temp_input_file
            and temp_input_file.exists()
        ):
            try:
                audio_service.cleanup_files(temp_input_file)
            except Exception as e:
                logger.warning(
                    f"Failed to cleanup input file: {temp_input_file}",
                    error=str(e),
                )


@router.get(
    "/separate/{job_id}/download/{filename}",
    summary="Download separated stem file",
    description="""
    Download a specific stem file from a completed separation job.
    
    Use the `job_id` and `filename` from the separation response to download individual stems.
    The filename should match one of the files listed in the `output_files` array from the separation response.
    
    **Example:**
    If the separation response contains:
    ```json
    {
      "job_id": "181543dd-c632-4a42-bb8d-f3ca74c763cd",
      "output_files": ["vocals.wav", "accompaniment.wav"]
    }
    ```
    
    You can download vocals.wav using:
    ```
    GET /api/v1/separate/181543dd-c632-4a42-bb8d-f3ca74c763cd/download/vocals.wav
    ```
    """,
    responses={
        200: {
            "description": "File downloaded successfully",
            "content": {
                "audio/wav": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                },
                "audio/mpeg": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                },
            },
        },
        404: {
            "description": "File not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "File not found: vocals.wav",
                        "error_code": "FILE_NOT_FOUND",
                    }
                }
            },
        },
        403: {
            "description": "Invalid file path (path traversal attempt)",
        },
    },
    tags=["separation"],
)
async def download_stem(
    job_id: str = Path(
        ...,
        description="Unique job ID from the separation response",
        examples=["181543dd-c632-4a42-bb8d-f3ca74c763cd"],
    ),
    filename: str = Path(
        ...,
        description="Name of the stem file to download. Must match one of the files in output_files from the separation response.",
        examples=["vocals.wav", "accompaniment.wav", "drums.wav"],
    ),
) -> FileResponse:
    """
    Download a specific stem file from a separation job.

    This endpoint allows you to download individual stem files that were generated
    during the separation process. The job_id and filename must match the values
    returned in the separation response.

    **Security:**
    - Path traversal attempts are blocked
    - Only files within the output directory can be accessed
    - File names are sanitized before processing

    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/separate/181543dd-c632-4a42-bb8d-f3ca74c763cd/download/vocals.wav" \\
         --output vocals.wav
    ```
    """
    try:
        logger.info(
            "Download request received",
            job_id=job_id,
            filename=filename,
        )

        # Sanitize inputs
        sanitized_job_id = sanitize_filename(job_id)
        sanitized_filename = sanitize_filename(filename)

        # Build file path
        file_path = PathLib(settings.OUTPUT_DIR) / sanitized_job_id / sanitized_filename

        # Validate file exists - combine conditionals
        if not (file_path.exists() and file_path.is_file()):
            logger.warning(
                "File not found for download",
                job_id=job_id,
                filename=filename,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error=f"File not found: {filename}",
                    error_code="FILE_NOT_FOUND",
                ).model_dump(),
            )

        # Validate file is within output directory (prevent path traversal)
        output_dir_resolved = PathLib(settings.OUTPUT_DIR).resolve()
        try:
            file_path.resolve().relative_to(output_dir_resolved)
        except ValueError:
            logger.warning(
                "Path traversal attempt detected",
                job_id=job_id,
                filename=filename,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid file path",
                    error_code="INVALID_PATH",
                ).model_dump(),
            )

        return FileResponse(
            path=str(file_path),
            filename=sanitized_filename,
            media_type="audio/wav",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error during file download",
            job_id=job_id,
            filename=filename,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error during download",
                error_code="DOWNLOAD_ERROR",
            ).model_dump(),
        )
