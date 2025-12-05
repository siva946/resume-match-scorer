import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/resumsync")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-min-32-chars")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_minutes: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))
    
    # CORS
    allowed_origins: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    
    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
    
    # File Upload
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    max_file_size_bytes: int = max_file_size_mb * 1024 * 1024
    allowed_file_types: List[str] = ["application/pdf"]
    
    # API
    api_timeout_seconds: int = int(os.getenv("API_TIMEOUT_SECONDS", "30"))
    max_jobs_per_request: int = int(os.getenv("MAX_JOBS_PER_REQUEST", "50"))
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Sentry
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    
    class Config:
        env_file = ".env"

settings = Settings()
