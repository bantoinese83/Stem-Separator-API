"""Custom exceptions for the application."""


class StemSeparatorException(Exception):
    """Base exception for stem separator errors."""

    def __init__(self, message: str, error_code: str = "GENERAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FileValidationError(StemSeparatorException):
    """Exception raised for file validation errors."""

    def __init__(self, message: str):
        super().__init__(message, error_code="FILE_VALIDATION_ERROR")


class UnsupportedFormatError(StemSeparatorException):
    """Exception raised for unsupported audio formats."""

    def __init__(self, message: str):
        super().__init__(message, error_code="UNSUPPORTED_FORMAT")


class ProcessingError(StemSeparatorException):
    """Exception raised during audio processing."""

    def __init__(self, message: str):
        super().__init__(message, error_code="PROCESSING_ERROR")


class ModelNotFoundError(StemSeparatorException):
    """Exception raised when Spleeter model is not found."""

    def __init__(self, message: str):
        super().__init__(message, error_code="MODEL_NOT_FOUND")


class TimeoutError(StemSeparatorException):
    """Exception raised when processing times out."""

    def __init__(self, message: str):
        super().__init__(message, error_code="PROCESSING_TIMEOUT")
