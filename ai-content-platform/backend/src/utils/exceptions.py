"""Domain-specific exceptions mapped to HTTP responses by FastAPI handlers."""
from __future__ import annotations


class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class ContentSafetyError(AppError):
    status_code = 400
    code = "content_unsafe"


class GenerationError(AppError):
    status_code = 500
    code = "generation_failed"


class ModelUnavailableError(AppError):
    status_code = 503
    code = "model_unavailable"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
