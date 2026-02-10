from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.exception_handlers import app_exception_handler
from app.api.routes import appointments as appointments_router
from app.api.routes import medspas as medspas_router
from app.api.routes import services as services_router
from app.exceptions import AppException

app = FastAPI(
    title="MedSpa API",
    description="API for medspa services and appointments",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",    # ReDoc (alternative docs)
    openapi_url="/openapi.json",
)

app.add_exception_handler(AppException, app_exception_handler)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(medspas_router.router, prefix="/medspas")
app.include_router(services_router.router, tags=["services"])
app.include_router(appointments_router.router, tags=["appointments"])
