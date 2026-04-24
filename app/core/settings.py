import json
from functools import cached_property

from pydantic import BaseModel, Field, SecretStr
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @cached_property
    def routers(self) -> list[RouterSettings]:
        try:
            raw_routers = json.loads(self.routers_json)
        except json.JSONDecodeError as exc:
            raise ValueError("ROUTERS_JSON inválido no .env") from exc

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


settings = Settings()