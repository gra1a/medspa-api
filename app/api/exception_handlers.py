from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.exceptions import AppException


def app_exception_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, AppException)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
