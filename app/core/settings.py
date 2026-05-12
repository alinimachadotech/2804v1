import json
from functools import cached_property
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RouterSettings(BaseModel):
    name: str
    ip: str
    token: SecretStr = Field(repr=False)
    key: SecretStr = Field(repr=False)


class Settings(BaseSettings):
    app_name: str = "API do Gerax Manager"
    app_version: str = "0.1.0"
    app_env: str = "local"
    debug: bool = True

    routers_json: str = Field(default="[]", repr=False)

    mariadb_host: str = "127.0.0.1"
    mariadb_port: int = 3317
    mariadb_user: str = "gerax"
    mariadb_password: SecretStr = Field(default=SecretStr("change-me-local-password"), repr=False)
    mariadb_database: str = "gerax_manager"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    nextrouter_verify_ssl: bool = True
    nextrouter_timeout_seconds: int = 60
    balance_cache_ttl_seconds: int = 60
    customer_cache_ttl_seconds: int = 60
    online_cache_ttl_seconds: int = 60
    router_request_timeout_seconds: int = 60

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"local", "dev", "development"}:
                return True
        return value

    @cached_property
    def routers(self) -> list[RouterSettings]:
        try:
            raw_routers = json.loads(self.routers_json)
        except json.JSONDecodeError as exc:
            raise ValueError("ROUTERS_JSON invÃ¡lido no .env") from exc

        routers: list[RouterSettings] = []

        for item in raw_routers:
            ip = item.get("ip")
            token = item.get("token")
            key = item.get("key")

            if not ip or ip == "0.0.0.0":
                continue

            if not token or not key:
                continue

            routers.append(RouterSettings(**item))

        return routers

    @property
    def database_url(self) -> str:
        password = quote_plus(self.mariadb_password.get_secret_value())
        return (
            f"mysql+pymysql://{self.mariadb_user}:{password}"
            f"@{self.mariadb_host}:{self.mariadb_port}/{self.mariadb_database}"
            "?charset=utf8mb4"
        )


settings = Settings()
