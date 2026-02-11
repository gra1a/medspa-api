import logging

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.exceptions import AppException

logger = logging.getLogger(__name__)


def app_exception_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, AppException)
    method = getattr(request, "method", "?")
    path = getattr(request, "url", None)
    path_str = path.path if path else "?"
    # request_id is included on the log record via RequestIDFilter (contextvar)
    if exc.status_code >= 500:
        logger.error(
            "app_exception status=%s method=%s path=%s detail=%s",
            exc.status_code,
            method,
            path_str,
            exc.detail,
            exc_info=True,
        )
    else:
        logger.warning(
            "app_exception status=%s method=%s path=%s detail=%s",
            exc.status_code,
            method,
            path_str,
            exc.detail,
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
