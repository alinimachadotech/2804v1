from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.settings import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


app.include_router(api_router)