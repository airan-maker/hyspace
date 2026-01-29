from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Silicon Nexus"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/silicon_nexus"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
