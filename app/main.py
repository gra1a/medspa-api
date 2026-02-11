from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.exception_handlers import app_exception_handler
from app.api.routes import appointments as appointments_router
from app.api.routes import medspas as medspas_router
from app.api.routes import services as services_router
from app.config import settings
from app.db.database import engine
from app.exceptions import AppException
from app.logging_config import request_id_ctx, setup_logging
from app.utils.ulid import generate_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    yield


app = FastAPI(
    title="MedSpa API",
    description="API for medspa services and appointments",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc (alternative docs)
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_exception_handler(AppException, app_exception_handler)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a ULID request ID to each request; set in request.state and context for logging."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or generate_id()
        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)


app.add_middleware(RequestIDMiddleware)


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "detail": "database unavailable"},
        )
    return {"status": "ok"}


app.include_router(medspas_router.router, prefix="/medspas")
app.include_router(services_router.router, tags=["services"])
app.include_router(appointments_router.router, tags=["appointments"])
