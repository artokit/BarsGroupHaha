from pathlib import Path
from typing import Annotated
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Config(BaseSettings):
    bot_token: str = ""
    admin_ids: Annotated[list[int], NoDecode] = []

    @field_validator("bot_token")
    @classmethod
    def _validate_bot_token(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("BOT_TOKEN не задан в .env")
        return value

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
