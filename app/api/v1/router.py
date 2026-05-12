from fastapi import APIRouter

from app.api.v1.endpoints import customers, health, online_calls, routers

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(routers.router)
api_router.include_router(customers.router)
api_router.include_router(online_calls.routers_router)
api_router.include_router(online_calls.online_router)
