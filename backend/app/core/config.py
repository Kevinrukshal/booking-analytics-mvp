from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./booking_analytics.db"
    cors_origins: str = "http://localhost:5173"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    ai_classify_on_import: bool = False
    allow_external_ai: bool = False
    api_access_token: str = ""
    allow_uploads: bool = False
    max_expanded_mb: int = 100
    max_workbook_rows: int = 100000
    max_workbook_cells: int = 2000000
    max_workbook_sheets: int = 20
    max_upload_mb: int = 100
    min_agent_bookings: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
