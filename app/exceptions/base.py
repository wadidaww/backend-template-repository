from __future__ import annotations

from http import HTTPStatus


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, HTTPStatus.NOT_FOUND)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, HTTPStatus.CONFLICT)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, HTTPStatus.UNAUTHORIZED)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, HTTPStatus.FORBIDDEN)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, HTTPStatus.UNPROCESSABLE_ENTITY)
