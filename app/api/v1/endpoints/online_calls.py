"""Endpoints read-only para chamadas online."""

from fastapi import APIRouter, HTTPException, Query

from app.api.v1.errors import handle_service_error
from app.core.online_metrics import update_online_metrics
from app.integrations.nextrouter.exceptions import (
    NextRouterAuthError,
    NextRouterError,
    NextRouterNotFoundError,
    NextRouterRateLimitError,
    NextRouterTimeoutError,
)
from app.schemas.online_calls import OnlineAggregateAllRoutersOut
from app.services.online_cache_service import (
    get_cached_online_aggregate_all,
    set_cached_online_aggregate_all,
)
from app.services.online_calls_service import (
    get_online_aggregate_all_routers,
    get_online_aggregate_by_router_id,
    get_online_calls_by_router,
)
from app.services.online_snapshot_service import save_online_snapshot


routers_router = APIRouter(prefix="/api/v1/routers", tags=["Online Calls"])


@routers_router.get("/{router_id}/online-aggregate")
def get_online_aggregate(router_id: int):
    try:
        return get_online_aggregate_by_router_id(router_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except NextRouterAuthError:
        raise HTTPException(
            status_code=403,
            detail="Falha na autenticacao com NextRouter",
        )
    except NextRouterNotFoundError:
        raise HTTPException(status_code=404, detail="Recurso nao encontrado no NextRouter")
    except NextRouterRateLimitError:
        raise HTTPException(status_code=429, detail="Rate limit do NextRouter excedido")
    except NextRouterTimeoutError:
        raise HTTPException(status_code=504, detail="Timeout ao comunicar com NextRouter")
    except NextRouterError:
        raise HTTPException(status_code=502, detail="Erro ao comunicar com NextRouter")


online_router = APIRouter(prefix="/api/v1/online", tags=["Online Calls"])
noc_router = APIRouter(prefix="/api/v1/noc/online", tags=["NOC"])


def _get_or_collect_online_aggregate_all(
    router_name: str | None = None,
) -> OnlineAggregateAllRoutersOut:
    if router_name not in (None, ""):
        result = get_online_aggregate_all_routers(router_name=router_name)
        update_online_metrics(result.model_dump())
        return result

    cached_data = get_cached_online_aggregate_all()
    if cached_data:
        update_online_metrics(cached_data.model_dump())
        return cached_data

    result = get_online_aggregate_all_routers()
    set_cached_online_aggregate_all(result)
    update_online_metrics(result.model_dump())
    save_online_snapshot(result)
    return result


@online_router.get("/aggregate/all-routers", response_model=OnlineAggregateAllRoutersOut)
def get_online_aggregate_all():
    return _get_or_collect_online_aggregate_all()


@noc_router.get("/calls")
def read_online_calls(
    router_name: str = Query(..., min_length=1),
    id_rota: str | None = None,
    summary: bool = False,
    id_record: str | None = None,
):
    try:
        return get_online_calls_by_router(
            router_name,
            id_rota=id_rota,
            summary=summary,
            id_record=id_record,
        )
    except Exception as exc:
        handle_service_error(exc)


@noc_router.get("/aggregate", response_model=OnlineAggregateAllRoutersOut)
def read_noc_online_aggregate(router_name: str | None = None):
    try:
        return _get_or_collect_online_aggregate_all(router_name=router_name)
    except Exception as exc:
        handle_service_error(exc)


@noc_router.get("/routes")
def read_noc_online_routes():
    return _get_or_collect_online_aggregate_all().routes


@noc_router.get("/clients")
def read_noc_online_clients():
    return _get_or_collect_online_aggregate_all().top_clients


@noc_router.get("/servers")
def read_noc_online_servers():
    return _get_or_collect_online_aggregate_all().servers


router = routers_router
