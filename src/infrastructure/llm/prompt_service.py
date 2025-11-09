"""
Prompt service for retrieving system prompts from database.
"""

from functools import lru_cache

from src.domain.entities.system_prompt import PromptType
from src.infrastructure.database.system_prompt_repository import SystemPromptRepository
from src.shared.logging import LoggerMixin


class PromptService(LoggerMixin):
    """
    Service for managing and retrieving system prompts.

    Provides caching and fallback to defaults for reliability.
    """

    def __init__(self, repository: SystemPromptRepository | None = None):
        """
        Initialize prompt service.

        Args:
            repository: Prompt repository (optional, will create if not provided)
        """
        self.repository = repository or SystemPromptRepository()
        self._cache = {}

    async def get_prompt(self, prompt_type: PromptType) -> str:
        """
        Get a system prompt by type.

        Uses caching and falls back to defaults on error.

        Args:
            prompt_type: Type of prompt to retrieve

        Returns:
            Prompt content string
        """
        # Check cache first
        cache_key = f"prompt_{prompt_type.value}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Get from database
            prompt = await self.repository.get(prompt_type)
            content = prompt.content if prompt else ""

            # Cache it
            self._cache[cache_key] = content
            return content

        except Exception as e:
            # Fall back to default on error
            self.logger.warning(
                "prompt_fetch_failed_using_default",
                prompt_type=prompt_type.value,
                error=str(e),
            )
            default = self._get_default_prompt(prompt_type)
            self._cache[cache_key] = default
            return default

    def _get_default_prompt(self, prompt_type: PromptType) -> str:
        """Get default prompt from the entity."""
        from src.domain.entities.system_prompt import SystemPrompt

        return SystemPrompt.get_default_prompt(prompt_type)

    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()
        self.logger.info("prompt_cache_cleared")

    def clear_prompt_cache(self, prompt_type: PromptType):
        """Clear cache for a specific prompt type."""
        cache_key = f"prompt_{prompt_type.value}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            self.logger.info("prompt_cache_cleared_for_type", prompt_type=prompt_type.value)


@lru_cache
def get_prompt_service() -> PromptService:
    """Get cached prompt service singleton."""
    return PromptService()
