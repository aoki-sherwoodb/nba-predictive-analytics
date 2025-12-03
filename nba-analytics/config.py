"""
Configuration settings for NBA Analytics Platform.
Supports environment variables for cloud deployment.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "nba_analytics")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "postgres")
    # Cloud SQL specific settings
    use_cloud_sql: bool = os.getenv("USE_CLOUD_SQL", "false").lower() == "true"
    cloud_sql_connection_name: str = os.getenv("CLOUD_SQL_CONNECTION_NAME", "")

    @property
    def connection_string(self) -> str:
        if self.use_cloud_sql:
            # For Cloud SQL with Unix socket
            return f"postgresql+pg8000://{self.user}:{self.password}@/{self.database}?unix_sock={self.host}/.s.PGSQL.5432"
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis cache configuration."""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    db: int = int(os.getenv("REDIS_DB", "0"))
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("API_DEBUG", "false").lower() == "true"
    cors_origins: list = None
    
    def __post_init__(self):
        origins = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000")
        self.cors_origins = [origin.strip() for origin in origins.split(",")]


@dataclass
class IngestionConfig:
    """Data ingestion configuration."""
    # How often to poll for new data (in seconds)
    poll_interval: int = int(os.getenv("INGESTION_POLL_INTERVAL", "300"))  # 5 minutes
    # Number of seasons of historical data to fetch
    historical_seasons: int = int(os.getenv("HISTORICAL_SEASONS", "3"))
    # Current NBA season (format: "2025-26")
    current_season: str = os.getenv("CURRENT_SEASON", "2025-26")


@dataclass
class StorageConfig:
    """Model storage configuration for local or GCS."""
    backend: str = os.getenv("MODEL_STORAGE_BACKEND", "local")  # "local" or "gcs"
    local_path: str = os.getenv("MODEL_LOCAL_PATH", "trained_models")
    gcs_bucket: str = os.getenv("MODEL_BUCKET", "")
    gcs_prefix: str = os.getenv("MODEL_GCS_PREFIX", "models")


@dataclass
class AppConfig:
    """Main application configuration."""
    database: DatabaseConfig = None
    redis: RedisConfig = None
    api: APIConfig = None
    ingestion: IngestionConfig = None
    storage: StorageConfig = None

    def __post_init__(self):
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.api = APIConfig()
        self.ingestion = IngestionConfig()
        self.storage = StorageConfig()


# Global configuration instance
config = AppConfig()
