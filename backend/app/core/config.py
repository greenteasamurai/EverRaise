import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, AnyUrl, field_validator, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    SERVER_NAME: str = "EverRaise API"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"
    
    # Authentication
    ALGORITHM: str = "HS256"  # JWT token algorithm
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:5173", "http://localhost:5174"]
    
    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "everraise"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[AnyUrl] = "sqlite+aiosqlite:///./everraise.db"
    ASYNC_DATABASE_URL: Optional[PostgresDsn] = None
    DB_ECHO_LOG: bool = False  # Whether to echo SQL queries for debugging

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: Any) -> Any:
        if isinstance(v, str):
            # If it's a SQLite URL, just return it as is
            if v.startswith("sqlite"):
                return v
            return v
        
        # Use SQLite for development
        if cls.model_fields["ENVIRONMENT"].default == "development":
            return "sqlite+aiosqlite:///./everraise.db"
        
        # Use PostgreSQL in other environments
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=cls.model_fields["POSTGRES_USER"].default,
            password=cls.model_fields["POSTGRES_PASSWORD"].default,
            host=cls.model_fields["POSTGRES_SERVER"].default,
            port=int(cls.model_fields["POSTGRES_PORT"].default),
            path=f"{cls.model_fields['POSTGRES_DB'].default or ''}",
        )

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Vector Database Configuration
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-west1-gcp"
    PINECONE_INDEX_NAME: str = "everraise-embeddings"

    # LLM Configuration
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    LLM_DEFAULT_MODEL: str = "gpt-4"
    LLM_TIMEOUT: int = 60
    LLM_MAX_TOKENS: int = 1000
    LLM_TEMPERATURE: float = 0.2
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = ""
    SMTP_USER: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""
    EMAILS_FROM_EMAIL: Optional[EmailStr] = "support@everraise.app"
    EMAILS_FROM_NAME: Optional[str] = "EverRaise Support"

    # OAuth2 Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""

    # Security & Monitoring
    ENVIRONMENT: str = "development"
    SENTRY_DSN: Optional[HttpUrl] = None
    LOG_LEVEL: str = "INFO"
    ENCRYPTION_KEY: str = secrets.token_hex(16)  # For encrypting sensitive data

    # Application Features
    ENABLE_REPORT_SCHEDULING: bool = True
    ENABLE_ADVANCED_ANALYTICS: bool = True
    ENABLE_PRIVATE_LLM: bool = False  # Use private LLMs or public APIs
    
    # Gmail API Configuration
    GMAIL_API_CREDENTIALS_FILE: str = "credentials.json"
    GMAIL_API_TOKEN_FILE: str = "token.json"
    GMAIL_API_SCOPES: str = "https://www.googleapis.com/auth/gmail.readonly"


settings = Settings() 