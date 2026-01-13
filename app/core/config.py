from typing import Annotated
from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    database_username: str
    database_password: str
    database_hostname: str
    database_port: str = "5432"
    database_name: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings():
    return Settings()  # type: ignore


settings = Settings()  # type: ignore
SettingsDep = Annotated[Settings, Depends(get_settings)]
