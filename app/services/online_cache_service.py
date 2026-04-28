"""Serviço de cache para agregação de chamadas online."""

import logging
from typing import Optional

from app.core.cache import redis_get_json, redis_set_json
from app.core.settings import settings
from app.schemas.online_calls import OnlineAggregateAllRoutersOut

logger = logging.getLogger(__name__)

# Chave padrão do Redis
CACHE_KEY = "gerax:online:aggregate:all"


def get_cached_online_aggregate_all() -> Optional[OnlineAggregateAllRoutersOut]:
    """Obtém agregação de chamadas online do cache.
    
    Returns:
        OnlineAggregateAllRoutersOut ou None se não existir no cache
    """
    try:
        cached_data = redis_get_json(CACHE_KEY)
        if not cached_data:
            return None

        # Valida com o schema Pydantic
        return OnlineAggregateAllRoutersOut(**cached_data)
    except Exception as exc:
        logger.warning(f"Erro ao deserializar cache {CACHE_KEY}: {exc}")
        return None


def set_cached_online_aggregate_all(
    data: OnlineAggregateAllRoutersOut,
) -> bool:
    """Salva agregação de chamadas online no cache.
    
    Args:
        data: Dados a cachear
        
    Returns:
        True se bem-sucedido, False caso contrário
    """
    try:
        # TTL mínimo de 60 segundos
        ttl = max(settings.online_cache_ttl_seconds, 60)
        
        # Converte para dicionário
        payload = data.model_dump()
        
        # Salva no Redis
        result = redis_set_json(CACHE_KEY, payload, ttl)
        
        if result:
            logger.debug(f"Cache {CACHE_KEY} salvo com TTL {ttl}s")
        
        return result
    except Exception as exc:
        logger.warning(f"Erro ao cachear {CACHE_KEY}: {exc}")
        return False
