"""Excecoes do NextRouter."""


class NextRouterError(Exception):
    """Erro generico do NextRouter."""

    def __init__(self, message: str, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


class NextRouterTimeoutError(NextRouterError):
    """Erro de timeout na comunicacao com NextRouter."""


class NextRouterAuthError(NextRouterError):
    """Erro de autenticacao (token/key invalido)."""


class NextRouterBadRequestError(NextRouterError):
    """Requisicao invalida enviada ao NextRouter."""


class NextRouterNotFoundError(NextRouterError):
    """Recurso nao encontrado no NextRouter."""


class NextRouterPayloadTooLargeError(NextRouterError):
    """Payload grande demais para o NextRouter."""


class NextRouterValidationError(NextRouterError):
    """Erro de validacao retornado pelo NextRouter."""


class NextRouterRateLimitError(NextRouterError):
    """Taxa de requisicoes excedida no NextRouter."""


class NextRouterServerError(NextRouterError):
    """Erro 5xx retornado pelo NextRouter."""
