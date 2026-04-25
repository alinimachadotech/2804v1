"""Exceções do NextRouter."""


class NextRouterError(Exception):
    """Erro genérico do NextRouter."""
    pass


class NextRouterTimeoutError(NextRouterError):
    """Erro de timeout na comunicação com NextRouter."""
    pass


class NextRouterAuthError(NextRouterError):
    """Erro de autenticação (token/key inválido)."""
    pass


class NextRouterNotFoundError(NextRouterError):
    """Recurso não encontrado no NextRouter."""
    pass


class NextRouterRateLimitError(NextRouterError):
    """Taxa de requisições excedida no NextRouter."""
    pass
