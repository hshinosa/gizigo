from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_base_url: str = "http://43.228.214.145:8317/v1"
    openai_api_key: str = "sk-ama"
    openai_model: str = "gpt-5.4-mini"

    database_url: str = "postgresql://gizigo:devpw@127.0.0.1:5433/gizigo"

    cors_allowed_origin: str = "http://localhost:5173"

    humanizer_llm_enabled: bool = False

    api_host: str = "127.0.0.1"
    api_port: int = 8001
    log_level: str = "info"

    catalog_path: str = "data/normalized/ingredients.json"
    akg_path: str = "data/akg/permenkes-28-2019.json"
    prices_dki: str = "data/prices/dki_jakarta.yaml"
    prices_national: str = "data/prices/national_baseline.yaml"
    substitutes_path: str = "data/substitutes.yaml"
    cooking_method_path: str = "data/cooking-method.yaml"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
