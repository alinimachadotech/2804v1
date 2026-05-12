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


class NextRouterBadRequestError(NextRouterError):
    """Requisição inválida enviada ao NextRouter."""
    pass


class NextRouterNotFoundError(NextRouterError):
    """Recurso não encontrado no NextRouter."""
    pass


class NextRouterPayloadTooLargeError(NextRouterError):
    """Payload grande demais para o NextRouter."""
    pass


class NextRouterValidationError(NextRouterError):
    """Erro de validação retornado pelo NextRouter."""
    pass


class NextRouterRateLimitError(NextRouterError):
    """Taxa de requisições excedida no NextRouter."""
    pass


class NextRouterServerError(NextRouterError):
    """Erro 5xx retornado pelo NextRouter."""
    pass
