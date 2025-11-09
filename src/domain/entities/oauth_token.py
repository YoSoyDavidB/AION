"""
OAuth Token entity for storing authentication tokens.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OAuthProvider(str, Enum):
    """OAuth provider types."""

    GOOGLE = "google"
    MICROSOFT = "microsoft"


class OAuthToken(BaseModel):
    """OAuth token entity."""

    token_id: UUID = Field(default_factory=uuid4, description="Unique token identifier")
    user_id: str = Field(..., description="User ID who owns this token")
    provider: OAuthProvider = Field(..., description="OAuth provider")
    access_token: str = Field(..., description="Encrypted access token")
    refresh_token: str | None = Field(default=None, description="Encrypted refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    scopes: list[str] = Field(default_factory=list, description="Granted scopes")

    # Provider-specific user info
    provider_user_id: str | None = Field(default=None, description="User ID from provider")
    provider_user_email: str | None = Field(default=None, description="User email from provider")
    provider_user_name: str | None = Field(default=None, description="User name from provider")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_used_at: datetime | None = Field(default=None, description="Last time token was used")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() >= self.expires_at

    @property
    def needs_refresh(self) -> bool:
        """Check if token needs to be refreshed (expires in < 5 minutes)."""
        from datetime import timedelta
        threshold = datetime.utcnow() + timedelta(minutes=5)
        return threshold >= self.expires_at

    class Config:
        """Pydantic config."""
        from_attributes = True
