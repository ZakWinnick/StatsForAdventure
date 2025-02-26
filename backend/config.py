"""Application configuration."""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App settings
    APP_NAME: str = "Stats For Adventure"
    SECRET_KEY: str
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Session settings
    SESSION_SECRET_KEY: str
    SESSION_MAX_AGE: int = 1800  # 30 minutes in seconds
    
    # Rivian API settings
    RIVIAN_API_BASE_URL: str = "https://rivian.com/api/gql"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()