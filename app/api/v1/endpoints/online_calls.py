"""Endpoints para gerenciar chamadas online."""

from fastapi import APIRouter, HTTPException

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
)

# Router para endpoints /api/v1/routers/{router_id}/online-aggregate
routers_router = APIRouter(prefix="/api/v1/routers", tags=["Online Calls"])


@routers_router.get("/{router_id}/online-aggregate")
def get_online_aggregate(router_id: int):
    """Busca agregação de chamadas online de um router.
    
    Args:
        router_id: ID do router (1-based)
        
    Returns:
        Dados de agregação de chamadas online em JSON
        
    Raises:
        HTTPException: Erros de comunicação ou validação
    """
    try:
        return get_online_aggregate_by_router_id(router_id)
    
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    
    except NextRouterAuthError:
        raise HTTPException(
            status_code=401,
            detail="Falha na autenticação com o NextRouter (credenciais inválidas)"
        )
    
    except NextRouterNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Recurso não encontrado no NextRouter"
        )
    
    except NextRouterRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Taxa de requisições para NextRouter excedida"
        )
    
    except NextRouterTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Timeout ao comunicar com NextRouter"
        )
    
    except NextRouterError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao comunicar com NextRouter: {exc}"
        )


# Router para endpoints /api/v1/online/...
online_router = APIRouter(prefix="/api/v1/online", tags=["Online Calls"])


@online_router.get("/aggregate/all-routers", response_model=OnlineAggregateAllRoutersOut)
def get_online_aggregate_all():
    """Busca agregação de chamadas online de todos os routers.
    
    Usa cache Redis com TTL mínimo de 60 segundos.
    Se um router falhar, continua com os outros e registra a falha.
    
    Returns:
        OnlineAggregateAllRoutersOut com dados consolidados
    """
    # Tenta obter do cache primeiro
    cached_data = get_cached_online_aggregate_all()
    if cached_data:
        # Cache válido: atualiza métricas e retorna
        update_online_metrics(cached_data.model_dump())
        return cached_data
    
    # Sem cache válido: consulta os routers
    result = get_online_aggregate_all_routers()
    
    # Salva no cache
    set_cached_online_aggregate_all(result)
    
    # Atualiza métricas
    update_online_metrics(result.model_dump())
    
    return result


# Compatibilidade: usar ambos os routers
router = routers_router
