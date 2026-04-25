"""Cliente HTTP seguro para NextRouter API."""

import httpx

from app.integrations.nextrouter.endpoints import ONLINE_CALLS_AGGREGATE
from app.integrations.nextrouter.exceptions import (
    NextRouterAuthError,
    NextRouterError,
    NextRouterNotFoundError,
    NextRouterRateLimitError,
    NextRouterTimeoutError,
)
from app.utils.masking import mask_url


class NextRouterClient:
    """Cliente para comunicação segura com NextRouter."""
    
    DEFAULT_TIMEOUT = 15.0  # segundos
    
    def __init__(self, base_url: str, timeout: float = DEFAULT_TIMEOUT):
        """Inicializa o cliente.
        
        Args:
            base_url: URL base do router (ex: https://192.168.1.100)
            timeout: Timeout em segundos
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    def get_online_calls_aggregate(self, token: str, key: str) -> dict:
        """Busca agregação de chamadas online.
        
        Args:
            token: Token do NextRouter (SecretStr.get_secret_value())
            key: Chave do NextRouter (SecretStr.get_secret_value())
            
        Returns:
            Dicionário com dados de agregação
            
        Raises:
            NextRouterAuthError: Token/key inválido (403)
            NextRouterNotFoundError: Recurso não encontrado (404)
            NextRouterRateLimitError: Taxa de requisições excedida (429)
            NextRouterTimeoutError: Timeout na comunicação
            NextRouterError: Erro genérico
        """
        endpoint = ONLINE_CALLS_AGGREGATE.format(token=token, key=key)
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Nunca vamos imprimir a URL real com credenciais
            # Se precisar debugar, usar mask_url()
            
            with httpx.Client(verify=False, timeout=self.timeout) as client:
                response = client.get(url)
                
                if response.status_code == 403:
                    raise NextRouterAuthError(
                        "Autenticação falhou - token/key inválido"
                    )
                elif response.status_code == 404:
                    raise NextRouterNotFoundError(
                        "Recurso não encontrado no NextRouter"
                    )
                elif response.status_code == 429:
                    raise NextRouterRateLimitError(
                        "Taxa de requisições excedida"
                    )
                elif response.status_code >= 400:
                    raise NextRouterError(
                        f"Erro HTTP {response.status_code} do NextRouter"
                    )
                
                response.raise_for_status()
                return response.json()
        
        except httpx.TimeoutException as exc:
            raise NextRouterTimeoutError(
                f"Timeout ao comunicar com NextRouter (>{self.timeout}s)"
            ) from exc
        except httpx.HTTPError as exc:
            raise NextRouterError(
                f"Erro de comunicação com NextRouter: {exc}"
            ) from exc
