"""Cliente HTTP seguro para NextRouter API."""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Any
from urllib.parse import quote, urlsplit

import httpx

from app.integrations.nextrouter.endpoints import (
    CDR,
    CDR_DISCONNECTION,
    CDR_SIPCODES,
    CONTACTS,
    CREDIT_HISTORY,
    GET_CUSTOMER_BALANCE,
    MANAGE_CUSTOMERS,
    ONLINE_CALLS,
    ONLINE_CALLS_AGGREGATE,
    PROFIT_CUSTOMERS,
    PROFIT_GATEWAYS,
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
            or self._get_field(router, "host")
            or self._get_field(router, "ip")
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
    def _with_optional_id(endpoint_template: str, value: Any | None) -> str:
        if value in (None, ""):
            return endpoint_template
        return f"{endpoint_template}/{quote(str(value).strip(), safe='')}"

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

    @staticmethod
    def _sanitize_text(value: Any, *secrets: str) -> str:
        text = str(value or "")
        for secret in secrets:
            if secret:
                text = text.replace(secret, "****")
        return mask_url(text)

    @staticmethod
    def _endpoint_logical_name(endpoint_template: str) -> str:
        endpoint = endpoint_template.split("/{token}/{key}", 1)[0].rsplit("/", 1)[-1]
        return endpoint or endpoint_template

    @staticmethod
    def _sanitize_path(url: str) -> str:
        path = urlsplit(url).path
        parts = path.split("/")
        try:
            api_index = parts.index("api")
        except ValueError:
            return path

        if len(parts) > api_index + 3:
            masked_parts = list(parts)
            masked_parts[api_index + 2] = "***"
            masked_parts[api_index + 3] = "***"
            return "/".join(masked_parts)
        return path

    def _diagnostics(
        self,
        *,
        endpoint_template: str,
        router: Any | None,
        url: str,
        params: dict[str, Any],
        status_code: int | None,
        body: Any | None,
        elapsed_ms: float,
        exception_type: str | None = None,
        token: str = "",
        key: str = "",
    ) -> dict[str, Any]:
        return {
            "endpoint": self._endpoint_logical_name(endpoint_template),
            "router_name": self._get_field(router, "name"),
            "base_url": self._sanitize_text(
                self._base_url_for_router(router),
                token,
                key,
            ),
            "path": self._sanitize_path(url),
            "query_params": dict(params),
            "status_code": status_code,
            "body_preview": self._sanitize_text(str(body or "")[:500], token, key),
            "exception_type": exception_type,
            "elapsed_ms": round(elapsed_ms, 2),
        }

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
        started_at = time.perf_counter()

        logger.debug("Requisicao NextRouter: %s", mask_url(url))

        try:
            with httpx.Client(
                verify=self._verify_for_router(router),
                timeout=self.timeout,
            ) as client:
                response = client.get(url, params=clean_params)
                if response.status_code >= 400:
                    error_class = self._STATUS_ERRORS.get(response.status_code)
                    if response.status_code >= 500:
                        error_class = NextRouterServerError
                    if error_class is None:
                        error_class = NextRouterError

                    diagnostics = self._diagnostics(
                        endpoint_template=endpoint_template,
                        router=router,
                        url=url,
                        params=clean_params,
                        status_code=response.status_code,
                        body=response.text,
                        elapsed_ms=(time.perf_counter() - started_at) * 1000,
                        exception_type=error_class.__name__,
                        token=token_value,
                        key=key_value,
                    )
                    logger.error(
                        "Erro NextRouter endpoint=%s router_name=%s base_url=%s "
                        "path=%s query_params=%s status_code=%s body_preview=%s "
                        "exception_type=%s elapsed_ms=%s",
                        diagnostics["endpoint"],
                        diagnostics["router_name"],
                        diagnostics["base_url"],
                        diagnostics["path"],
                        diagnostics["query_params"],
                        diagnostics["status_code"],
                        diagnostics["body_preview"],
                        diagnostics["exception_type"],
                        diagnostics["elapsed_ms"],
                    )
                    raise error_class(
                        f"Erro HTTP {response.status_code} do NextRouter",
                        diagnostics=diagnostics,
                    )
                return response.json()
        except httpx.TimeoutException as exc:
            diagnostics = self._diagnostics(
                endpoint_template=endpoint_template,
                router=router,
                url=url,
                params=clean_params,
                status_code=None,
                body=None,
                elapsed_ms=(time.perf_counter() - started_at) * 1000,
                exception_type=type(exc).__name__,
                token=token_value,
                key=key_value,
            )
            logger.error(
                "Erro NextRouter endpoint=%s router_name=%s base_url=%s path=%s "
                "query_params=%s status_code=%s body_preview=%s exception_type=%s "
                "elapsed_ms=%s",
                diagnostics["endpoint"],
                diagnostics["router_name"],
                diagnostics["base_url"],
                diagnostics["path"],
                diagnostics["query_params"],
                diagnostics["status_code"],
                diagnostics["body_preview"],
                diagnostics["exception_type"],
                diagnostics["elapsed_ms"],
            )
            raise NextRouterTimeoutError(
                f"Timeout ao comunicar com NextRouter (>{self.timeout}s)",
                diagnostics=diagnostics,
            ) from exc
        except httpx.HTTPError as exc:
            diagnostics = self._diagnostics(
                endpoint_template=endpoint_template,
                router=router,
                url=url,
                params=clean_params,
                status_code=None,
                body=None,
                elapsed_ms=(time.perf_counter() - started_at) * 1000,
                exception_type=type(exc).__name__,
                token=token_value,
                key=key_value,
            )
            logger.error(
                "Erro NextRouter endpoint=%s router_name=%s base_url=%s path=%s "
                "query_params=%s status_code=%s body_preview=%s exception_type=%s "
                "elapsed_ms=%s",
                diagnostics["endpoint"],
                diagnostics["router_name"],
                diagnostics["base_url"],
                diagnostics["path"],
                diagnostics["query_params"],
                diagnostics["status_code"],
                diagnostics["body_preview"],
                diagnostics["exception_type"],
                diagnostics["elapsed_ms"],
            )
            raise NextRouterError(
                "Erro de comunicacao com NextRouter",
                diagnostics=diagnostics,
            ) from exc
        except ValueError as exc:
            raise NextRouterError("Resposta invalida do NextRouter") from exc

    @staticmethod
    def _pagination(start: int = 0, limit: int = 100) -> dict[str, int]:
        return {"start": max(start, 0), "limit": max(limit, 1)}

    def get_customer_balance(
        self,
        router: Any,
        customer_id: Any | None = None,
    ) -> dict[str, Any]:
        endpoint = self._with_optional_id(GET_CUSTOMER_BALANCE, customer_id)
        payload = self._request(
            endpoint,
            router=router,
        )
        return normalize_customer_balance(payload, customer_id=customer_id)

    def get_customer(self, router: Any, customer_id: Any | None = None) -> dict[str, Any]:
        endpoint = self._with_optional_id(MANAGE_CUSTOMERS, customer_id)
        payload = self._request(
            endpoint,
            router=router,
        )
        return normalize_customer(payload)

    def get_credit_history(
        self,
        router: Any,
        customer_id: Any | None = None,
        date_ini: Any | None = None,
        date_end: Any | None = None,
        start: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params = {
            "date_ini": date_ini,
            "date_end": date_end,
            **self._pagination(start, limit),
        }
        endpoint = self._with_optional_id(CREDIT_HISTORY, customer_id)
        payload = self._request(endpoint, router=router, params=params)
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
        endpoint = self._with_optional_id(CDR, customer_id)
        params = {**filters, **self._pagination(start, limit)}
        payload = self._request(endpoint, router=router, params=params)
        return normalize_money_collection(payload)

    def get_cdr_disconnection(
        self,
        router: Any,
        customer_id: Any | None = None,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        endpoint = self._with_optional_id(CDR_DISCONNECTION, customer_id)
        params = {**filters, **self._pagination(start, limit)}
        payload = self._request(endpoint, router=router, params=params)
        return normalize_money_collection(payload)

    def get_cdr_sipcodes(
        self,
        router: Any,
        customer_id: Any | None = None,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> Any:
        endpoint = self._with_optional_id(CDR_SIPCODES, customer_id)
        params = {**filters, **self._pagination(start, limit)}
        payload = self._request(endpoint, router=router, params=params)
        return normalize_passthrough(payload)

    def get_profit_customers(
        self,
        router: Any,
        customer_id: Any | None = None,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        endpoint = PROFIT_CUSTOMERS
        params = {**filters, **self._pagination(start, limit)}
        if customer_id not in (None, ""):
            params.pop("customer_id", None)
            params["customers[]"] = customer_id
        payload = self._request(endpoint, router=router, params=params)
        return normalize_money_collection(payload)

    def get_profit_gateways(
        self,
        router: Any,
        customer_id: Any | None = None,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        endpoint = PROFIT_GATEWAYS
        params = {**filters, **self._pagination(start, limit)}
        if customer_id not in (None, ""):
            params.pop("customer_id", None)
            params["customers[]"] = customer_id
        payload = self._request(endpoint, router=router, params=params)
        return normalize_money_collection(payload)

    def get_contacts(
        self,
        router: Any,
        customer_id: Any | None = None,
        start: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        endpoint = self._with_optional_id(CONTACTS, customer_id)
        params = {**filters, **self._pagination(start, limit)}
        payload = self._request(endpoint, router=router, params=params)
        return normalize_money_collection(payload)
