"""
Configuration settings for the backend application using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SKIP_DB_INIT: bool = False
    MODEL_PATH: str = "/models/yolo26_quantized.onnx"
    CLASS_NAMES_PATH: str = "/models/class_names.json"
    MODEL_INPUT_SIZE: int = 1024
    MODEL_VERSION: str = "yolo26-seg-onnx"

    # Authentication
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    JWT_ALGORITHM: str = "HS256"

    # PostgreSQL configuration
    DATABASE_URL: str | None = None
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "plant_disease"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "changeme"

    # Redis configuration
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_ENABLED: bool = True
    REDIS_SOCKET_TIMEOUT: float = 2.0
    RATE_LIMIT_PREDICT_PER_MINUTE: int = 30
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    KNOWLEDGE_CACHE_TTL_SECONDS: int = 3600
    # MinIO configuration
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "plant-disease-images"
    MINIO_SECURE: bool = False

    # MLflow tracking
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"

    @property
    def database_url(self) -> str:
        """Returns the PostgreSQL connection string."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        import urllib.parse

        user = urllib.parse.quote_plus(self.POSTGRES_USER)
        password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql://{user}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
