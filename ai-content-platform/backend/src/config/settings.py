"""Application settings loaded from environment variables.

All env access lives here; every other module imports `settings` rather than
reading `os.environ` directly.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- App -----
    app_name: str = "AI Content Platform"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    # Stored as a raw comma-separated string; use the `cors_allow_origins` property to read
    # as a list. Storing as `list[str]` makes pydantic-settings try JSON-parsing the env var.
    cors_allow_origins_raw: str = Field(
        default="http://localhost:3000", alias="CORS_ALLOW_ORIGINS"
    )

    # ----- Google Gemini -----
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 1024

    # ----- Content pipeline -----
    content_mock: bool = True
    content_refinement_loop: bool = True
    content_refinement_max_iterations: int = 2
    content_quality_threshold: float = 0.7
    content_personalization: bool = True
    content_safety_filter: bool = True
    content_default_tone: str = "professional"
    content_default_length: str = "medium"
    content_default_platform: str = "blog"

    # ----- Image generation -----
    content_generate_image: bool = True
    # "pollinations" (free, no key, Flux/SD-backed) or "gemini" (paid, gemini-2.5-flash-image)
    image_provider: str = "pollinations"
    image_model_id: str = "gemini-2.5-flash-image"
    image_pollinations_model: str = "flux"
    image_width: int = 1024
    image_height: int = 576
    image_storage_dir: str = "./storage/images"
    public_image_base_url: str = "/static/images"

    # ----- Storage -----
    database_url: str = "sqlite:///./storage/content.db"

    @property
    def cors_allow_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins_raw.split(",") if o.strip()]

    @property
    def image_storage_path(self):
        from pathlib import Path
        path = Path(self.image_storage_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
