"""Application settings and configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Slack Configuration
    slack_bot_token: SecretStr = Field(..., description="Slack bot token")
    slack_app_token: SecretStr = Field(..., description="Slack app token for socket mode")
    slack_signing_secret: SecretStr = Field(..., description="Slack signing secret")

    # LLM Configuration
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, ge=1, le=100000)

    # Embeddings Configuration
    embeddings_provider: Literal["openai", "anthropic"] = "openai"
    embeddings_model: str = "text-embedding-3-small"
    embeddings_dimension: int = 1536

    # Vector Database Configuration
    vector_db_provider: Literal["pinecone", "chromadb", "faiss"] = "pinecone"
    pinecone_api_key: SecretStr | None = None
    pinecone_environment: str | None = None
    pinecone_index_name: str = "slack-rag-assistant"

    # Jira Configuration
    jira_url: str | None = None
    jira_username: str | None = None
    jira_api_token: SecretStr | None = None
    jira_project_key: str = "SUPPORT"
    jira_issue_type: str = "Task"

    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True

    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./slack_rag_assistant.db"

    # Security Configuration
    encryption_key: SecretStr | None = None
    secret_key: SecretStr = Field(default="change-me-in-production")

    # Policy Configuration
    default_sla_minutes: int = Field(default=120, ge=1)
    default_first_response_minutes: int = Field(default=15, ge=1)
    enable_pii_redaction: bool = True
    enable_action_approval: bool = True

    # Observability
    metrics_port: int = 9090
    enable_tracing: bool = False
    otlp_endpoint: str | None = None

    # Rate Limiting
    rate_limit_per_user: int = Field(default=10, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

    # RAG Configuration
    rag_retrieval_top_k: int = Field(default=5, ge=1, le=20)
    rag_similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    rag_max_context_length: int = Field(default=8000, ge=100)

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str, info: any) -> str:
        """Validate that required API key exists for the selected provider."""
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
