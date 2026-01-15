# anonyfiles_cli/exceptions.py


class AnonyfilesError(Exception):
    """Base exception for Anonyfiles CLI."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class ConfigurationError(AnonyfilesError):
    """Raised for invalid or missing configuration."""

    def __init__(self, message: str):
        super().__init__(f"Configuration Error: {message}", exit_code=1)


class ProcessingError(AnonyfilesError):
    """Raised for errors during file processing (anonymization/deanonymization)."""

    def __init__(self, message: str):
        super().__init__(f"Processing Error: {message}", exit_code=1)


class FileIOError(AnonyfilesError):
    """Raised for file input/output related errors."""

    def __init__(self, message: str):
        super().__init__(f"File I/O Error: {message}", exit_code=1)
