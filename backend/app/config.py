from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "HySpace"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/hyspace"

    # Neo4j Graph Database
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "hyspace2026"

    # Anthropic API
    anthropic_api_key: str = ""

    # Server
    port: int = 8000

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
