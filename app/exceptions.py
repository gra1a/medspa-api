class AppException(Exception):
    """Base for API exceptions that map to HTTP responses."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppException):
    """Raise when a requested resource does not exist (HTTP 404)."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=404)


class BadRequestError(AppException):
    """Raise when the request is invalid (HTTP 400)."""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=400)


class ConflictError(AppException):
    """Raise when the request conflicts with current resource state (HTTP 409)."""

    def __init__(self, detail: str = "One or more services are already booked for this time slot."):
        super().__init__(detail=detail, status_code=409)
