"""
Embedding service - Handles text-to-vector conversion.
"""

from typing import Any

from src.config.settings import get_settings
from src.infrastructure.llm.openrouter_client import OpenRouterClient
from src.shared.exceptions import EmbeddingServiceError
from src.shared.logging import LoggerMixin


class EmbeddingService(LoggerMixin):
    """
    Service for generating text embeddings.

    Uses OpenRouter to access various embedding models.
    Provides caching and batch processing capabilities.
    """

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        """
        Initialize embedding service.

        Args:
            client: OpenRouter client instance (optional)
        """
        self.settings = get_settings()
        self.client = client or OpenRouterClient()
        self.default_model = self.settings.openrouter.openrouter_embedding_model
        self.vector_size = self.settings.qdrant.qdrant_vector_size

        self.logger.info(
            "embedding_service_initialized",
            model=self.default_model,
            vector_size=self.vector_size,
        )

    async def close(self) -> None:
        """Close the underlying client."""
        await self.client.close()

    async def embed_text(
        self, text: str, model: str | None = None
    ) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Model to use (defaults to configured model)

        Returns:
            Embedding vector

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        model = model or self.default_model

        if not text.strip():
            raise EmbeddingServiceError(
                "Cannot embed empty text",
                details={"text": text},
            )

        try:
            self.logger.debug(
                "embedding_text",
                text_length=len(text),
                model=model,
            )

            embedding = await self.client.generate_single_embedding(model, text)

            # Validate embedding dimensions
            if len(embedding) != self.vector_size:
                self.logger.warning(
                    "unexpected_embedding_size",
                    expected=self.vector_size,
                    actual=len(embedding),
                    model=model,
                )

            return embedding

        except Exception as e:
            self.logger.error(
                "embedding_generation_failed",
                error=str(e),
                text_length=len(text),
                model=model,
            )
            raise EmbeddingServiceError(
                f"Failed to generate embedding: {str(e)}",
                details={"text_length": len(text), "model": model},
            ) from e

    async def embed_texts(
        self, texts: list[str], model: str | None = None, batch_size: int = 100
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            model: Model to use (defaults to configured model)
            batch_size: Number of texts to process in each batch

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        model = model or self.default_model

        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [text.strip() for text in texts if text.strip()]
        if not valid_texts:
            raise EmbeddingServiceError(
                "No valid texts to embed",
                details={"original_count": len(texts)},
            )

        try:
            self.logger.info(
                "embedding_batch",
                num_texts=len(valid_texts),
                model=model,
                batch_size=batch_size,
            )

            embeddings: list[list[float]] = []

            # Process in batches to avoid overwhelming the API
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i : i + batch_size]

                self.logger.debug(
                    "processing_batch",
                    batch_num=i // batch_size + 1,
                    batch_size=len(batch),
                )

                batch_embeddings = await self.client.generate_embeddings(
                    model, batch
                )
                embeddings.extend(batch_embeddings)

            self.logger.info(
                "batch_embedding_complete",
                num_embeddings=len(embeddings),
            )

            return embeddings

        except Exception as e:
            self.logger.error(
                "batch_embedding_failed",
                error=str(e),
                num_texts=len(valid_texts),
                model=model,
            )
            raise EmbeddingServiceError(
                f"Failed to generate batch embeddings: {str(e)}",
                details={"num_texts": len(valid_texts), "model": model},
            ) from e

    async def embed_query(self, query: str, model: str | None = None) -> list[float]:
        """
        Generate embedding for a search query.

        This is a specialized method for queries that may apply
        query-specific preprocessing in the future.

        Args:
            query: Search query text
            model: Model to use (defaults to configured model)

        Returns:
            Embedding vector

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        # Currently just wraps embed_text, but allows for future
        # query-specific preprocessing or different models
        self.logger.debug("embedding_query", query_length=len(query))
        return await self.embed_text(query, model)

    def get_vector_size(self) -> int:
        """
        Get the expected embedding vector size.

        Returns:
            Vector dimension size
        """
        return self.vector_size

    def get_default_model(self) -> str:
        """
        Get the default embedding model.

        Returns:
            Model identifier
        """
        return self.default_model

    async def compute_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1, where 1 is most similar)

        Raises:
            EmbeddingServiceError: If embeddings have different dimensions
        """
        if len(embedding1) != len(embedding2):
            raise EmbeddingServiceError(
                "Embeddings have different dimensions",
                details={
                    "embedding1_size": len(embedding1),
                    "embedding2_size": len(embedding2),
                },
            )

        # Compute cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        similarity = dot_product / (magnitude1 * magnitude2)

        # Clamp to [0, 1] range
        return max(0.0, min(1.0, similarity))

    def truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens

        Returns:
            Truncated text
        """
        # Rough approximation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text

        self.logger.warning(
            "truncating_text",
            original_length=len(text),
            truncated_length=max_chars,
        )

        return text[:max_chars]
