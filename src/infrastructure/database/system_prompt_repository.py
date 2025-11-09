"""
Repository for managing system prompts in PostgreSQL.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text, select
from sqlalchemy.exc import SQLAlchemyError

from src.domain.entities.system_prompt import PromptType, SystemPrompt
from src.infrastructure.database.connection import Base, DatabaseManager
from src.shared.logging import get_logger

logger = get_logger(__name__)


class SystemPromptModel(Base):
    """SQLAlchemy model for system prompts."""

    __tablename__ = "system_prompts"

    prompt_type = Column(String(50), primary_key=True)
    content = Column(Text, nullable=False)
    description = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemPromptRepository:
    """Repository for managing system prompts."""

    def __init__(self):
        """Initialize repository."""
        self.db_manager = DatabaseManager()
        logger.info("system_prompt_repository_initialized")

    def _to_domain(self, model: SystemPromptModel) -> SystemPrompt:
        """Convert database model to domain entity."""
        return SystemPrompt(
            prompt_type=PromptType(model.prompt_type),
            content=model.content,
            description=model.description,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, prompt: SystemPrompt) -> SystemPromptModel:
        """Convert domain entity to database model."""
        return SystemPromptModel(
            prompt_type=prompt.prompt_type.value,
            content=prompt.content,
            description=prompt.description,
            is_active=prompt.is_active,
            created_at=prompt.created_at or datetime.utcnow(),
            updated_at=prompt.updated_at or datetime.utcnow(),
        )

    async def get(self, prompt_type: PromptType) -> SystemPrompt | None:
        """
        Get a prompt by type.

        Args:
            prompt_type: Type of prompt to retrieve

        Returns:
            SystemPrompt if found, None otherwise
        """
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(SystemPromptModel).where(
                    SystemPromptModel.prompt_type == prompt_type.value,
                    SystemPromptModel.is_active == True,
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

                if model:
                    return self._to_domain(model)

                # If not found in DB, return default
                logger.info("prompt_not_found_using_default", prompt_type=prompt_type.value)
                return SystemPrompt(
                    prompt_type=prompt_type,
                    content=SystemPrompt.get_default_prompt(prompt_type),
                    description=f"Default {prompt_type.value} prompt",
                    is_active=True,
                )

        except SQLAlchemyError as e:
            logger.error("get_prompt_failed", prompt_type=prompt_type.value, error=str(e))
            # Return default on error
            return SystemPrompt(
                prompt_type=prompt_type,
                content=SystemPrompt.get_default_prompt(prompt_type),
                description=f"Default {prompt_type.value} prompt",
                is_active=True,
            )

    async def get_all(self) -> list[SystemPrompt]:
        """
        Get all prompts.

        Returns:
            List of all system prompts
        """
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(SystemPromptModel)
                result = await session.execute(stmt)
                models = result.scalars().all()

                return [self._to_domain(model) for model in models]

        except SQLAlchemyError as e:
            logger.error("get_all_prompts_failed", error=str(e))
            return []

    async def save(self, prompt: SystemPrompt) -> SystemPrompt:
        """
        Save or update a prompt.

        Args:
            prompt: Prompt to save

        Returns:
            Saved prompt
        """
        try:
            async with self.db_manager.get_session() as session:
                # Check if exists
                stmt = select(SystemPromptModel).where(
                    SystemPromptModel.prompt_type == prompt.prompt_type.value
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing
                    existing.content = prompt.content
                    existing.description = prompt.description
                    existing.is_active = prompt.is_active
                    existing.updated_at = datetime.utcnow()
                    logger.info("prompt_updated", prompt_type=prompt.prompt_type.value)
                else:
                    # Create new
                    model = self._to_model(prompt)
                    session.add(model)
                    logger.info("prompt_created", prompt_type=prompt.prompt_type.value)

                return prompt

        except SQLAlchemyError as e:
            logger.error("save_prompt_failed", prompt_type=prompt.prompt_type.value, error=str(e))
            raise

    async def delete(self, prompt_type: PromptType) -> bool:
        """
        Delete a prompt (soft delete by marking inactive).

        Args:
            prompt_type: Type of prompt to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(SystemPromptModel).where(
                    SystemPromptModel.prompt_type == prompt_type.value
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

                if model:
                    model.is_active = False
                    model.updated_at = datetime.utcnow()
                    logger.info("prompt_deactivated", prompt_type=prompt_type.value)
                    return True

                return False

        except SQLAlchemyError as e:
            logger.error("delete_prompt_failed", prompt_type=prompt_type.value, error=str(e))
            raise

    async def reset_to_default(self, prompt_type: PromptType) -> SystemPrompt:
        """
        Reset a prompt to its default value.

        Args:
            prompt_type: Type of prompt to reset

        Returns:
            Reset prompt
        """
        default_content = SystemPrompt.get_default_prompt(prompt_type)
        prompt = SystemPrompt(
            prompt_type=prompt_type,
            content=default_content,
            description=f"Default {prompt_type.value} prompt (reset)",
            is_active=True,
        )

        await self.save(prompt)
        logger.info("prompt_reset_to_default", prompt_type=prompt_type.value)
        return prompt

    async def initialize_defaults(self) -> None:
        """Initialize all prompts with default values if they don't exist."""
        try:
            for prompt_type, content in SystemPrompt.get_all_default_prompts().items():
                # Check if exists
                existing = await self.get(prompt_type)

                # Only create if doesn't exist in DB
                async with self.db_manager.get_session() as session:
                    stmt = select(SystemPromptModel).where(
                        SystemPromptModel.prompt_type == prompt_type.value
                    )
                    result = await session.execute(stmt)
                    model = result.scalar_one_or_none()

                    if not model:
                        prompt = SystemPrompt(
                            prompt_type=prompt_type,
                            content=content,
                            description=f"Default {prompt_type.value} prompt",
                            is_active=True,
                        )
                        await self.save(prompt)
                        logger.info("default_prompt_initialized", prompt_type=prompt_type.value)

        except Exception as e:
            logger.error("initialize_defaults_failed", error=str(e))
            raise
