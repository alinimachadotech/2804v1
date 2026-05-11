from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.endpoints.health import legacy_router as health_legacy_router
from app.api.v1.router import api_router
from app.core.settings import settings
from app.routes.auth import router as auth_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    )

# Configuração de CORS para o frontend Sakai Vue
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
# MantÃ©m compatibilidade com testes e URLs antigas: /, /ping e /health.
app.include_router(health_legacy_router)

# Rotas novas e versionadas.
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(api_router)

