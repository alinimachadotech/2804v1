from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.endpoints.health import legacy_router as health_legacy_router
from app.api.v1.router import api_router
from app.core.settings import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


# MantÃ©m compatibilidade com testes e URLs antigas: /, /ping e /health.
app.include_router(health_legacy_router)

# Rotas novas e versionadas.
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(api_router)

