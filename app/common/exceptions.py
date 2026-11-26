from __future__ import annotations

from http import HTTPStatus


class AppException(Exception):
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message: str = "Internal server error"

    def __init__(
        self, message: str | None = None, status_code: int | None = None
    ) -> None:
        self.message = message or self.default_message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = HTTPStatus.NOT_FOUND
    default_message = "Resource not found"


class ConflictError(AppException):
    status_code = HTTPStatus.CONFLICT
    default_message = "Resource already exists"


class UnauthorizedError(AppException):
    status_code = HTTPStatus.UNAUTHORIZED
    default_message = "Unauthorized"


class ForbiddenError(AppException):
    status_code = HTTPStatus.FORBIDDEN
    default_message = "Forbidden"


class ValidationError(AppException):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Validation error"


class ServiceUnavailableError(AppException):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_message = "Service unavailable"
