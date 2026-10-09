from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    portal_base_url: str = "https://portaldatransparencia.gov.br"
    headless: bool = True
    max_concurrency: int = 3
    navigation_timeout: int = 45
    max_retries: int = 3

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"

    api_public_url: str = "http://localhost:8000"
    google_drive_folder_id: str = ""
    google_sheets_spreadsheet_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
