from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_permissions
from app.schemas.router import RouterOptionOut, RouterOut
from app.services.router_service import (
    get_router_by_id,
    get_router_by_slug,
    list_router_options,
    list_routers,
)

router = APIRouter(
    prefix="/api/v1/routers",
    tags=["Routers"],
    dependencies=[Depends(require_permissions(["routers:read"]))],
)


@router.get("", response_model=list[RouterOut])
def get_routers():
    return list_routers()


@router.get("/options", response_model=list[RouterOptionOut])
def get_router_options():
    return list_router_options()


@router.get("/slug/{router_slug}", response_model=RouterOut)
def get_router_slug(router_slug: str):
    router_data = get_router_by_slug(router_slug)

    if router_data is None:
        raise HTTPException(status_code=404, detail="Router não encontrado")

    return router_data


@router.get("/{router_id}", response_model=RouterOut)
def get_router(router_id: int):
    router_data = get_router_by_id(router_id)

    if router_data is None:
        raise HTTPException(status_code=404, detail="Router não encontrado")

    return router_data
