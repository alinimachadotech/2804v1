"""Cliente Redis centralizado para cache."""

import json
import logging
from typing import Any, Optional

import redis

from app.core.settings import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Cliente Redis com tratamento de erros seguro para produção."""

    def __init__(self):
        """Inicializa o cliente Redis."""
        self._client: Optional[redis.Redis] = None
        self._initialized = False

    def _get_client(self) -> Optional[redis.Redis]:
        """Retorna o cliente Redis, criando se necessário.
        
        Retorna None se a conexão falhar (Redis é opcional).
        """
        if self._initialized:
            return self._client

        try:
            self._client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_timeout=3,  # 3 segundos timeout curto
                socket_connect_timeout=3,
                retry_on_timeout=False,
            )
            # Teste de conexão
            self._client.ping()
            self._initialized = True
            logger.info("Redis conectado com sucesso")
            return self._client
        except Exception as exc:
            logger.warning(f"Falha ao conectar ao Redis: {exc}. Cache será desabilitado.")
            self._initialized = True
            self._client = None
            return None

    def redis_get_json(self, key: str) -> Optional[dict]:
        """Obtém valor JSON do Redis.
        
        Args:
            key: Chave Redis
            
        Returns:
            Dicionário deserializado ou None
        """
        try:
            client = self._get_client()
            if not client:
                return None

            value = client.get(key)
            if not value:
                return None

            return json.loads(value)
        except Exception as exc:
            # Falha de Redis não derruba a API
            logger.warning(f"Erro ao obter chave {key} do Redis: {exc}")
            return None

    def redis_set_json(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Define valor JSON no Redis.
        
        Args:
            key: Chave Redis
            value: Valor a serializar
            ttl_seconds: TTL em segundos (opcional)
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            client = self._get_client()
            if not client:
                return False

            json_value = json.dumps(value, ensure_ascii=False, default=str)
            if ttl_seconds:
                client.setex(key, ttl_seconds, json_value)
            else:
                client.set(key, json_value)
            return True
        except Exception as exc:
            # Falha de Redis não derruba a API
            logger.warning(f"Erro ao salvar chave {key} no Redis: {exc}")
            return False


# Instância global do cliente Redis
redis_client = RedisClient()


def redis_get_json(key: str) -> Optional[dict]:
    """Obtém valor JSON do Redis.
    
    Args:
        key: Chave Redis
        
    Returns:
        Dicionário deserializado ou None
    """
    return redis_client.redis_get_json(key)


def redis_set_json(key: str, value: dict, ttl_seconds: int) -> bool:
    """Define valor JSON no Redis.
    
    Args:
        key: Chave Redis
        value: Valor a serializar
        ttl_seconds: TTL em segundos
        
    Returns:
        True se bem-sucedido, False caso contrário
    """
    return redis_client.redis_set_json(key, value, ttl_seconds)
