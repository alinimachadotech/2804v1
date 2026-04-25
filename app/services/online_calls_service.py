"""Serviço para gerenciar chamadas online."""

from app.integrations.nextrouter.client import NextRouterClient
from app.services.router_service import get_router_secret_by_router_id


def get_online_aggregate_by_router_id(router_id: int) -> dict:
    """Busca agregação de chamadas online de um router.
    
    Args:
        router_id: ID do router
        
    Returns:
        Dicionário com dados de agregação de chamadas online
        
    Raises:
        ValueError: Router não encontrado
        NextRouterError: Erro ao comunicar com NextRouter
    """
    router_config = get_router_secret_by_router_id(router_id)
    
    if not router_config:
        raise ValueError(f"Router {router_id} não encontrado")
    
    client = NextRouterClient(
        base_url=f"https://{router_config.ip}"
    )
    
    token = router_config.token.get_secret_value()
    key = router_config.key.get_secret_value()
    
    return client.get_online_calls_aggregate(token, key)
