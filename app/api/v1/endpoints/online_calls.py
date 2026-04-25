"""Endpoints para gerenciar chamadas online."""

from fastapi import APIRouter, HTTPException

from app.integrations.nextrouter.exceptions import (
    NextRouterAuthError,
    NextRouterError,
    NextRouterNotFoundError,
    NextRouterRateLimitError,
    NextRouterTimeoutError,
)
from app.services.online_calls_service import get_online_aggregate_by_router_id

router = APIRouter(prefix="/api/v1/routers", tags=["Online Calls"])


@router.get("/{router_id}/online-aggregate")
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
