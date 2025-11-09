"""
Repository for OAuth tokens with encryption.
"""

import json
from datetime import datetime
from typing import List
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import Column, DateTime, String, Text, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.exc import SQLAlchemyError

from src.domain.entities.oauth_token import OAuthProvider, OAuthToken
from src.infrastructure.database.connection import Base, DatabaseManager
from src.shared.logging import get_logger

logger = get_logger(__name__)


class OAuthTokenModel(Base):
    """SQLAlchemy model for OAuth tokens."""

    __tablename__ = "oauth_tokens"

    token_id = Column(PGUUID(as_uuid=True), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_type = Column(String(50), nullable=False, default="Bearer")
    expires_at = Column(DateTime, nullable=False)
    scopes = Column(Text, nullable=False)  # JSON array
    provider_user_id = Column(String(255), nullable=True)
    provider_user_email = Column(String(255), nullable=True)
    provider_user_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class OAuthTokenRepository:
    """Repository for managing OAuth tokens with encryption."""

    def __init__(self, encryption_key: str):
        """Initialize repository with encryption key."""
        self.db_manager = DatabaseManager()
        # Ensure encryption key is properly formatted for Fernet
        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        logger.info("oauth_token_repository_initialized")

    def _encrypt(self, value: str) -> str:
        """Encrypt a string value."""
        return self.fernet.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        """Decrypt a string value."""
        return self.fernet.decrypt(value.encode()).decode()

    def _to_domain(self, model: OAuthTokenModel) -> OAuthToken:
        """Convert database model to domain entity."""
        return OAuthToken(
            token_id=model.token_id,
            user_id=model.user_id,
            provider=OAuthProvider(model.provider),
            access_token=self._decrypt(model.access_token),
            refresh_token=self._decrypt(model.refresh_token) if model.refresh_token else None,
            token_type=model.token_type,
            expires_at=model.expires_at,
            scopes=json.loads(model.scopes),
            provider_user_id=model.provider_user_id,
            provider_user_email=model.provider_user_email,
            provider_user_name=model.provider_user_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_used_at=model.last_used_at,
        )

    def _to_model(self, token: OAuthToken) -> OAuthTokenModel:
        """Convert domain entity to database model."""
        return OAuthTokenModel(
            token_id=token.token_id,
            user_id=token.user_id,
            provider=token.provider.value,
            access_token=self._encrypt(token.access_token),
            refresh_token=self._encrypt(token.refresh_token) if token.refresh_token else None,
            token_type=token.token_type,
            expires_at=token.expires_at,
            scopes=json.dumps(token.scopes),
            provider_user_id=token.provider_user_id,
            provider_user_email=token.provider_user_email,
            provider_user_name=token.provider_user_name,
            created_at=token.created_at,
            updated_at=token.updated_at,
            last_used_at=token.last_used_at,
        )

    async def save(self, token: OAuthToken) -> OAuthToken:
        """Save or update an OAuth token."""
        try:
            async with self.db_manager.get_session() as session:
                model = self._to_model(token)
                await session.merge(model)
                logger.info(
                    "oauth_token_saved",
                    user_id=token.user_id,
                    provider=token.provider.value,
                    token_id=str(token.token_id),
                )
                return token
        except SQLAlchemyError as e:
            logger.error("save_oauth_token_failed", error=str(e))
            raise

    async def get_by_user_and_provider(self, user_id: str, provider: OAuthProvider) -> OAuthToken | None:
        """Get token by user ID and provider."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(OAuthTokenModel).where(
                    OAuthTokenModel.user_id == user_id,
                    OAuthTokenModel.provider == provider.value
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                return self._to_domain(model) if model else None
        except SQLAlchemyError as e:
            logger.error("get_oauth_token_failed", error=str(e))
            raise

    async def get_by_id(self, token_id: UUID) -> OAuthToken | None:
        """Get token by ID."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(OAuthTokenModel).where(OAuthTokenModel.token_id == token_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                return self._to_domain(model) if model else None
        except SQLAlchemyError as e:
            logger.error("get_oauth_token_by_id_failed", error=str(e))
            raise

    async def get_all_by_user(self, user_id: str) -> List[OAuthToken]:
        """Get all tokens for a user."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(OAuthTokenModel).where(OAuthTokenModel.user_id == user_id)
                result = await session.execute(stmt)
                models = result.scalars().all()
                return [self._to_domain(model) for model in models]
        except SQLAlchemyError as e:
            logger.error("get_user_oauth_tokens_failed", error=str(e))
            raise

    async def delete(self, token_id: UUID) -> bool:
        """Delete a token."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(OAuthTokenModel).where(OAuthTokenModel.token_id == token_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    await session.delete(model)
                    logger.info("oauth_token_deleted", token_id=str(token_id))
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error("delete_oauth_token_failed", error=str(e))
            raise

    async def delete_by_user_and_provider(self, user_id: str, provider: OAuthProvider) -> bool:
        """Delete token by user and provider."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(OAuthTokenModel).where(
                    OAuthTokenModel.user_id == user_id,
                    OAuthTokenModel.provider == provider.value
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    await session.delete(model)
                    logger.info("oauth_token_deleted", user_id=user_id, provider=provider.value)
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error("delete_oauth_token_failed", error=str(e))
            raise

    async def update_last_used(self, token_id: UUID) -> None:
        """Update last used timestamp."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(OAuthTokenModel).where(OAuthTokenModel.token_id == token_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if model:
                    model.last_used_at = datetime.utcnow()
        except SQLAlchemyError as e:
            logger.error("update_last_used_failed", error=str(e))
            raise
