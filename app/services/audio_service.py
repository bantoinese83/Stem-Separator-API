"""Audio processing service using Spleeter."""

# Import TensorFlow compatibility shim before Spleeter
# This patches tensorflow.estimator which is required by Spleeter
import app.tensorflow_compat  # noqa: F401

import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from halo import Halo
from loguru import logger
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator

from app.config import settings
from app.exceptions import (
    ModelNotFoundError,
    ProcessingError,
)
from app.models import StemType
from app.profiling import profile_performance
from app.utils import generate_job_id

# Patch tensorflow if it's already imported (lazy patching)
# This must happen after imports but before Spleeter uses tensorflow
app.tensorflow_compat.patch_tensorflow_estimator()  # noqa: E402

# Bind logger with module name
logger = logger.bind(name=__name__)

# Pre-compute stem files mapping for O(1) lookup instead of O(n) if/elif
STEM_FILES_MAP: Dict[StemType, List[str]] = {
    StemType.TWO_STEMS: ["vocals", "accompaniment"],
    StemType.FOUR_STEMS: ["vocals", "drums", "bass", "other"],
    StemType.FIVE_STEMS: ["vocals", "drums", "bass", "piano", "other"],
}


class AudioService:
    """Service for audio stem separation using Spleeter."""

    def __init__(self):
        """Initialize the audio service."""
        self.separators: Dict[str, Separator] = {}
        self.audio_adapter = AudioAdapter.default()
        logger.info("AudioService initialized")

    def _get_separator(self, stems: StemType) -> Separator:
        """Get or create a separator for the specified number of stems."""
        stems_str = stems.value

        if stems_str not in self.separators:
            try:
                logger.info(f"Loading Spleeter model: {stems_str}")
                separator = Separator(f"spleeter:{stems_str}")
                self.separators[stems_str] = separator
                logger.info(f"Successfully loaded model: {stems_str}")
            except Exception as e:
                logger.exception(
                    f"Failed to load Spleeter model: {stems_str}",
                    error=str(e),
                    stems=stems_str,
                )
                raise ModelNotFoundError(
                    f"Failed to load Spleeter model '{stems_str}'. Error: {str(e)}"
                )

        return self.separators[stems_str]

    def separate_audio(
        self,
        input_file: Path,
        output_dir: Path,
        stems: StemType = StemType.TWO_STEMS,
        bitrate: Optional[str] = None,
        format: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> dict:
        """
        Separate audio file into stems.

        Args:
            input_file: Path to input audio file
            output_dir: Directory to save output files
            stems: Number of stems to separate
            bitrate: Audio bitrate (optional)
            format: Output format (optional)
            job_id: Optional job ID for tracking

        Returns:
            Dictionary with separation results
        """
        if job_id is None:
            job_id = generate_job_id()

        # Cache settings lookups for performance
        audio_format = format or settings.AUDIO_FORMAT
        audio_bitrate = bitrate or settings.AUDIO_BITRATE

        logger.info(
            "Starting audio separation",
            job_id=job_id,
            input_file=str(input_file),
            stems=stems.value,
        )

        # Use performance profiling context manager
        with profile_performance(f"audio_separation_{job_id}"):
            start_time = time.perf_counter()  # Use perf_counter for better precision

            try:
                # Ensure output directory exists (single call, cached)
                output_dir.mkdir(parents=True, exist_ok=True)

                # Get separator (cached in instance dict)
                separator = self._get_separator(stems)

                # Perform separation
                logger.info("Performing separation", job_id=job_id, stems=stems.value)

                # Use halo spinner for visual feedback (only in terminal environments)
                # Spinner won't interfere with API responses
                spinner_text = (
                    f"Separating audio into {stems.value} (job: {job_id[:8]}...)"
                )
                try:
                    # Check if running in terminal (not in API server context)
                    import sys

                    is_terminal = sys.stdout.isatty()
                    if is_terminal:
                        with Halo(text=spinner_text, spinner="dots"):
                            separator.separate_to_file(
                                str(input_file),
                                str(output_dir),
                                codec=audio_format,
                                bitrate=audio_bitrate,
                                filename_format="{instrument}.{codec}",
                            )
                    else:
                        # No spinner in non-terminal environments (API server)
                        separator.separate_to_file(
                            str(input_file),
                            str(output_dir),
                            codec=audio_format,
                            bitrate=audio_bitrate,
                            filename_format="{instrument}.{codec}",
                        )
                except Exception:
                    # Fallback if halo fails, just run without spinner
                    separator.separate_to_file(
                        str(input_file),
                        str(output_dir),
                        codec=audio_format,
                        bitrate=audio_bitrate,
                        filename_format="{instrument}.{codec}",
                    )

                # Get output files (optimized with dict lookup)
                output_files = self._get_output_files(output_dir, stems)

                processing_time = time.perf_counter() - start_time

                logger.info(
                    "Audio separation completed successfully",
                    job_id=job_id,
                    processing_time=processing_time,
                    output_files=output_files,
                )

                return {
                    "job_id": job_id,
                    "output_files": output_files,
                    "processing_time": processing_time,
                    "stems": stems,
                }

            except Exception as e:
                processing_time = time.perf_counter() - start_time
                logger.exception(
                    "Audio separation failed",
                    job_id=job_id,
                    error=str(e),
                    processing_time=processing_time,
                )
                raise ProcessingError(f"Failed to separate audio: {str(e)}") from e

    def _get_output_files(self, output_dir: Path, stems: StemType) -> List[str]:
        """Get list of output files based on stem type."""
        # O(1) dict lookup instead of O(n) if/elif chain
        expected_files = STEM_FILES_MAP.get(stems, [])

        # Spleeter creates files in a subdirectory matching the input filename (without extension)
        # Use generator expression for memory efficiency (lazy evaluation)
        subdirs = (d for d in output_dir.iterdir() if d.is_dir())
        search_dir = next(subdirs, output_dir)  # More efficient than list + indexing

        # Use generator expression for finding files (memory efficient)
        output_files = []
        # Cache Path.relative_to for performance
        rel_to = Path.relative_to

        for expected_file in expected_files:
            pattern = f"{expected_file}.*"
            # Use generator instead of list for memory efficiency
            found_files = search_dir.glob(pattern)

            # Convert to list only when needed
            found_files_list = list(found_files)
            if found_files_list:
                # Use generator expression for relative paths
                rel_paths = [
                    str(rel_to(file_path, output_dir)) for file_path in found_files_list
                ]
                output_files.extend(rel_paths)
            else:
                logger.warning(
                    f"Expected output file not found: {expected_file}",
                    output_dir=str(output_dir),
                    search_dir=str(search_dir),
                    stems=stems.value,
                )

        # Sort in-place for better memory efficiency
        output_files.sort()
        return output_files

    def cleanup_files(self, *file_paths: Path) -> None:
        """Clean up temporary files."""
        # Cache method lookups for performance
        is_file = Path.is_file
        is_dir = Path.is_dir
        unlink = Path.unlink

        for file_path in file_paths:
            try:
                if is_file(file_path):
                    unlink(file_path)
                    logger.debug(f"Deleted file: {file_path}")
                elif is_dir(file_path):
                    shutil.rmtree(file_path)
                    logger.debug(f"Deleted directory: {file_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to cleanup file: {file_path}",
                    extra={"error": str(e)},
                )


# Global service instance
audio_service = AudioService()
