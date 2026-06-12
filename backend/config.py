from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_anon_key: str = Field(alias="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(alias="SUPABASE_SERVICE_KEY")
    google_api_key: str = Field(alias="GOOGLE_API_KEY")
    qdrant_url: str = Field(alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    redis_url: str = Field(alias="REDIS_URL")
    redis_token: str | None = Field(default=None, alias="REDIS_TOKEN")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    frontend_origin: str = "http://localhost:3000"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    max_upload_bytes: int = 20 * 1024 * 1024
    query_cache_semantic_threshold: float = 0.92
    embedding_model: str = "models/embedding-001"
    embedding_dimensions: int = 768
    cerebras_api_key: str = Field(alias="CEREBRAS_API_KEY")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
