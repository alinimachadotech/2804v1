"""Cliente HTTP seguro para NextRouter API."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import httpx

from app.integrations.nextrouter.endpoints import (
    CDR,
    CDR_DISCONNECTION,
    CDR_SIPCODES,
    GET_CUSTOMER_BALANCE,
    MANAGE_CREDIT,
    MANAGE_CUSTOMERS,
    ONLINE_CALLS,
    ONLINE_CALLS_AGGREGATE,
    PROFIT_CUSTOMERS,
    PROFIT_GATEWAYS,
    STATUS_CUSTOMER,
)
from app.integrations.nextrouter.exceptions import (
    NextRouterAuthError,
    NextRouterBadRequestError,
    NextRouterError,
    NextRouterNotFoundError,
    NextRouterPayloadTooLargeError,
    NextRouterRateLimitError,
    NextRouterServerError,
    NextRouterTimeoutError,
    NextRouterValidationError,
)
from app.integrations.nextrouter.parser import (
    format_money,
    normalize_credit_history,
    normalize_customer,
    normalize_customer_balance,
    normalize_money_collection,
    normalize_passthrough,
)
from app.utils.masking import mask_url


logger = logging.getLogger(__name__)


class NextRouterClient:
    """Cliente para comunicacao segura com NextRouter."""

    DEFAULT_TIMEOUT = 15.0

    _STATUS_ERRORS = {
        400: NextRouterBadRequestError,
        403: NextRouterAuthError,
        404: NextRouterNotFoundError,
        413: NextRouterPayloadTooLargeError,
        422: NextRouterValidationError,
        429: NextRouterRateLimitError,
    }

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
    ):
        """Inicializa o cliente.

        Args:
            base_url: URL base do router, quando usada no modo legado.
            timeout: Timeout em segundos.
            verify_ssl: Verificacao TLS configuravel.
        """
        self.base_url = self._normalize_base_url(base_url) if base_url else None
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    @staticmethod
    def _normalize_base_url(value: str) -> str:
        value = str(value).strip().rstrip("/")
        if value.startswith(("http://", "https://")):
            return value
        return f"https://{value}"

    @staticmethod
    def _get_field(source: Any, name: str) -> Any:
        if source is None:
            return None
        if isinstance(source, dict):
            return source.get(name)
        return getattr(source, name, None)

    @classmethod
    def _secret_value(cls, value: Any) -> str | None:
        if value is None:
            return None
        if hasattr(value, "get_secret_value"):
            return str(value.get_secret_value())
        return str(value)

    def _base_url_for_router(self, router: Any | None = None) -> str:
        if router is None:
            if not self.base_url:
                raise NextRouterError("URL base do router nao configurada")
            return self.base_url

        if isinstance(router, str):
            return self._normalize_base_url(router)

        raw_url = (
            self._get_field(router, "base_url")
            or self._get_field(router, "ip")
            or self._get_field(router, "host")
        )
        if not raw_url:
            raise NextRouterError("URL base do router nao configurada")

        return self._normalize_base_url(raw_url)

    def _credentials_for_router(
        self,
        router: Any | None = None,
        token: Any | None = None,
        key: Any | None = None,
    ) -> tuple[str, str]:
        resolved_token = self._secret_value(token) or self._secret_value(
            self._get_field(router, "token")
        )
        resolved_key = self._secret_value(key) or self._secret_value(
            self._get_field(router, "key")
        )

        if not resolved_token or not resolved_key:
            raise NextRouterAuthError("Credenciais do router ausentes")

        return resolved_token, resolved_key

    def _verify_for_router(self, router: Any | None = None) -> bool:
        verify_tls = self._get_field(router, "verify_tls")
        if verify_tls is None:
            return self.verify_ssl
        return bool(verify_tls)

    def _build_url(
        self,
        endpoint_template: str,
        token: str,
        key: str,
        router: Any | None = None,
    ) -> str:
        base_url = self._base_url_for_router(router)
        endpoint = endpoint_template.format(token=token, key=key)
        return f"{base_url}{endpoint}"

    @staticmethod
    def _clean_params(params: dict[str, Any] | None) -> dict[str, Any]:
        clean: dict[str, Any] = {}
        for key, value in (params or {}).items():
            if value is None:
                continue
            if isinstance(value, Decimal):
                clean[key] = str(value)
            elif isinstance(value, bool):
                clean[key] = int(value)
            else:
                clean[key] = value
        return clean

    def _raise_for_status(self, status_code: int) -> None:
        error_class = self._STATUS_ERRORS.get(status_code)
        if error_class:
            raise error_class(f"Erro HTTP {status_code} do NextRouter")

        if status_code >= 500:
            raise NextRouterServerError(f"Erro HTTP {status_code} do NextRouter")

        if status_code >= 400:
            raise NextRouterError(f"Erro HTTP {status_code} do NextRouter")

    def _request(
        self,
        endpoint_template: str,
        *,
        router: Any | None = None,
        token: Any | None = None,
        key: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        token_value, key_value = self._credentials_for_router(router, token, key)
        url = self._build_url(endpoint_template, token_value, key_value, router)
        clean_params = self._clean_params(params)

        logger.debug("Requisicao NextRouter: %s", mask_url(url))

        try:
            with httpx.Client(
                verify=self._verify_for_router(router),
                timeout=self.timeout,
            ) as client:
                response = client.get(url, params=clean_params)
                self._raise_for_status(response.status_code)
                return response.json()
        except httpx.TimeoutException as exc:
            raise NextRouterTimeoutError(
                f"Timeout ao comunicar com NextRouter (>{self.timeout}s)"
            ) from exc
        except httpx.HTTPError as exc:
            raise NextRouterError("Erro de comunicacao com NextRouter") from exc
        except ValueError as exc:
            raise NextRouterError("Resposta invalida do NextRouter") from exc

    @staticmethod
    def _pagination(start: int = 0, limit: int = 100) -> dict[str, int]:
        return {"start": max(start, 0), "limit": max(limit, 1)}

    def get_customer_balance(self, router: Any, customer_id: Any) -> dict[str, Any]:
        payload = self._request(
            GET_CUSTOMER_BALANCE,
            router=router,
            params={"id_cliente": customer_id},
        )
        return normalize_customer_balance(payload, customer_id=customer_id)

    def get_customer(self, router: Any, customer_id: Any) -> dict[str, Any]:
        payload = self._request(
            MANAGE_CUSTOMERS,
            router=router,
            params={"id_cliente": customer_id},
        )
        return normalize_customer(payload)

    def set_customer_status(self, router: Any, customer_id: Any, status: Any) -> Any:
        return self._request(
            STATUS_CUSTOMER,
            router=router,
            params={"id_cliente": customer_id, "status": status},
        )

    def manage_credit(
        self,
        router: Any,
        customer_id: Any,
        amount: Any,
        operation: str,
        reason: str,
        is_hidden: int = 0,
    ) -> Any:
        return self._request(
            MANAGE_CREDIT,
            router=router,
            params={
                "id_cliente": customer_id,
                "valor": format_money(amount),
                "operacao": operation,
                "motivo": reason,
                "is_hidden": is_hidden,
            },
        )

    def get_credit_history(
        self,
        router: Any,
        customer_id: Any,
        date_ini: Any,
        date_end: Any,
        start: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params = {
            "id_cliente": customer_id,
            "date_ini": date_ini,
            "date_end": date_end,
            "action": "history",
            **self._pagination(start, limit),
        }
        payload = self._request(MANAGE_CREDIT, router=router, params=params)
        return normalize_credit_history(payload)

    def get_online_calls(
        self,
        router: Any,
        id_rota: Any | None = None,
        summary: bool = False,
        id_record: Any | None = None,
    ) -> Any:
        return self._request(
            ONLINE_CALLS,
            router=router,
            params={"id_rota": id_rota, "summary": summary, "id_record": id_record},
        )

    def delete_online_call(self, router: Any, call_id: Any) -> Any:
        return self._request(
            ONLINE_CALLS,
            router=router,
            params={"id_record": call_id, "delete": 1},
        )

    def get_online_calls_aggregate(
        self,
        token: Any | None = None,
        key: Any | None = None,
        router: Any | None = None,
    ) -> Any:
        return self._request(
            ONLINE_CALLS_AGGREGATE,
            router=router,
            token=token,
            key=key,
        )

    def get_cdr(
        self,
        router: Any,
        customer_id: Any | None = None,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        params = {"id_cliente": customer_id, **filters, **self._pagination(start, limit)}
        payload = self._request(CDR, router=router, params=params)
        return normalize_money_collection(payload)

    def get_cdr_disconnection(
        self,
        router: Any,
        customer_id: Any | None = None,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        params = {"id_cliente": customer_id, **filters, **self._pagination(start, limit)}
        payload = self._request(CDR_DISCONNECTION, router=router, params=params)
        return normalize_money_collection(payload)

    def get_cdr_sipcodes(
        self,
        router: Any,
        customer_id: Any | None = None,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> Any:
        params = {"id_cliente": customer_id, **filters, **self._pagination(start, limit)}
        payload = self._request(CDR_SIPCODES, router=router, params=params)
        return normalize_passthrough(payload)

    def get_profit_customers(
        self,
        router: Any,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        params = {**filters, **self._pagination(start, limit)}
        payload = self._request(PROFIT_CUSTOMERS, router=router, params=params)
        return normalize_money_collection(payload)

    def get_profit_gateways(
        self,
        router: Any,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        params = {**filters, **self._pagination(start, limit)}
        payload = self._request(PROFIT_GATEWAYS, router=router, params=params)
        return normalize_money_collection(payload)
