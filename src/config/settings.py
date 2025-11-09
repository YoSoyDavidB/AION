"""
Application configuration using Pydantic Settings.
All environment variables are centralized here.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Main application settings."""

    app_name: str = Field(default="AION", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment"
    )
    debug: bool = Field(default=True, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class APISettings(BaseSettings):
    """API configuration settings."""

    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port", ge=1, le=65535)
    api_reload: bool = Field(default=True, description="Auto-reload on code changes")
    api_workers: int = Field(default=1, description="Number of worker processes", ge=1)

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials")
    cors_allow_methods: list[str] = Field(default=["*"], description="Allowed HTTP methods")
    cors_allow_headers: list[str] = Field(default=["*"], description="Allowed headers")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class OpenRouterSettings(BaseSettings):
    """OpenRouter API configuration."""

    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", description="OpenRouter base URL"
    )
    openrouter_embedding_model: str = Field(
        default="openai/text-embedding-3-small", description="Embedding model"
    )
    openrouter_llm_model: str = Field(
        default="anthropic/claude-3.5-sonnet", description="LLM model for generation"
    )
    openrouter_timeout: int = Field(default=60, description="Request timeout in seconds", ge=1)
    openrouter_max_retries: int = Field(default=3, description="Maximum retry attempts", ge=0)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class QdrantSettings(BaseSettings):
    """Qdrant vector database settings."""

    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port", ge=1, le=65535)
    qdrant_api_key: str | None = Field(default=None, description="Qdrant API key (optional)")
    qdrant_collection_memories: str = Field(
        default="memories", description="Memories collection name"
    )
    qdrant_collection_documents: str = Field(
        default="kb_documents", description="Documents collection name"
    )
    qdrant_vector_size: int = Field(
        default=1536, description="Vector embedding dimension", ge=1
    )
    qdrant_distance_metric: Literal["Cosine", "Euclid", "Dot"] = Field(
        default="Cosine", description="Distance metric"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class Neo4jSettings(BaseSettings):
    """Neo4j graph database settings."""

    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(..., description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")
    neo4j_max_connection_lifetime: int = Field(
        default=3600, description="Max connection lifetime in seconds", ge=60
    )
    neo4j_max_connection_pool_size: int = Field(
        default=50, description="Max connection pool size", ge=1
    )
    neo4j_connection_timeout: int = Field(
        default=30, description="Connection timeout in seconds", ge=1
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class PostgresSettings(BaseSettings):
    """PostgreSQL database settings."""

    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port", ge=1, le=65535)
    postgres_db: str = Field(default="aion_metadata", description="Database name")
    postgres_user: str = Field(default="aion_user", description="Database user")
    postgres_password: str = Field(..., description="Database password")
    postgres_pool_size: int = Field(default=10, description="Connection pool size", ge=1)
    postgres_max_overflow: int = Field(default=20, description="Max overflow connections", ge=0)
    postgres_echo: bool = Field(default=False, description="Echo SQL queries")

    @property
    def database_url(self) -> str:
        """Generate database URL for SQLAlchemy."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class GitHubSettings(BaseSettings):
    """GitHub configuration for Obsidian Vault synchronization."""

    github_token: str = Field(..., description="GitHub personal access token")
    github_repo_owner: str = Field(..., description="Repository owner username")
    github_repo_name: str = Field(..., description="Repository name")
    github_branch: str = Field(default="main", description="Branch to sync")
    obsidian_vault_path: str = Field(
        default="./obsidian_vault", description="Local path for Obsidian vault"
    )

    @property
    def repo_full_name(self) -> str:
        """Get full repository name."""
        return f"{self.github_repo_owner}/{self.github_repo_name}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class SyncSettings(BaseSettings):
    """Synchronization and processing settings."""

    auto_sync_enabled: bool = Field(default=True, description="Enable automatic sync")
    sync_interval_hours: int = Field(
        default=1, description="Sync interval in hours", ge=1, le=24
    )
    chunk_size: int = Field(
        default=500, description="Document chunk size in tokens", ge=100, le=2000
    )
    chunk_overlap: int = Field(
        default=50, description="Chunk overlap in tokens", ge=0, le=500
    )

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info: dict) -> int:
        """Ensure chunk overlap is less than chunk size."""
        chunk_size = info.data.get("chunk_size", 500)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class MemorySettings(BaseSettings):
    """Memory management settings."""

    memory_max_length: int = Field(
        default=150, description="Maximum memory text length", ge=50, le=500
    )
    memory_retrieval_limit: int = Field(
        default=5, description="Number of memories to retrieve", ge=1, le=20
    )
    document_retrieval_limit: int = Field(
        default=10, description="Number of documents to retrieve", ge=1, le=50
    )
    memory_consolidation_enabled: bool = Field(
        default=True, description="Enable memory consolidation"
    )
    memory_min_relevance_score: float = Field(
        default=0.7, description="Minimum relevance score for retrieval", ge=0.0, le=1.0
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class SecuritySettings(BaseSettings):
    """Security and encryption settings."""

    secret_key: str = Field(..., description="Secret key for JWT and encryption")
    encrypt_at_rest: bool = Field(default=True, description="Encrypt data at rest")
    encryption_key: str = Field(..., description="Encryption key for sensitive data")
    oauth_encryption_key: str = Field(..., description="Fernet encryption key for OAuth tokens")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes", ge=5
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class RateLimitSettings(BaseSettings):
    """Rate limiting settings."""

    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(
        default=60, description="Requests per minute", ge=1, le=1000
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class GoogleOAuthSettings(BaseSettings):
    """Google OAuth2 configuration for Calendar and Gmail."""

    google_client_id: str | None = Field(default=None, description="Google OAuth2 Client ID")
    google_client_secret: str | None = Field(default=None, description="Google OAuth2 Client Secret")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/integrations/google/callback",
        description="Google OAuth2 Redirect URI"
    )
    google_scopes: list[str] = Field(
        default=[
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        description="Google API scopes"
    )

    @property
    def is_configured(self) -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(self.google_client_id and self.google_client_secret)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class MicrosoftOAuthSettings(BaseSettings):
    """Microsoft OAuth2 configuration for Outlook Calendar and Email."""

    microsoft_client_id: str | None = Field(default=None, description="Microsoft OAuth2 Client ID")
    microsoft_client_secret: str | None = Field(default=None, description="Microsoft OAuth2 Client Secret")
    microsoft_tenant_id: str = Field(default="common", description="Microsoft Tenant ID")
    microsoft_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/integrations/microsoft/callback",
        description="Microsoft OAuth2 Redirect URI"
    )
    microsoft_scopes: list[str] = Field(
        default=[
            "Calendars.Read",
            "Mail.Read",
            "User.Read",
            "offline_access",
        ],
        description="Microsoft Graph API scopes"
    )

    @property
    def is_configured(self) -> bool:
        """Check if Microsoft OAuth is properly configured."""
        return bool(self.microsoft_client_id and self.microsoft_client_secret)

    @property
    def authority(self) -> str:
        """Get Microsoft authority URL."""
        return f"https://login.microsoftonline.com/{self.microsoft_tenant_id}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class Settings:
    """
    Main settings aggregator.
    Provides access to all configuration sections.
    """

    def __init__(self) -> None:
        self.app = AppSettings()
        self.api = APISettings()
        self.openrouter = OpenRouterSettings()
        self.qdrant = QdrantSettings()
        self.neo4j = Neo4jSettings()
        self.postgres = PostgresSettings()
        self.github = GitHubSettings()
        self.sync = SyncSettings()
        self.memory = MemorySettings()
        self.security = SecuritySettings()
        self.rate_limit = RateLimitSettings()
        self.google_oauth = GoogleOAuthSettings()
        self.microsoft_oauth = MicrosoftOAuthSettings()

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()
