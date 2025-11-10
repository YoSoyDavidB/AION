"""
OpenRouter client for LLM operations.
"""

import json
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import get_settings
from src.shared.exceptions import LLMServiceError
from src.shared.logging import LoggerMixin


class OpenRouterClient(LoggerMixin):
    """
    Client for interacting with OpenRouter API.

    OpenRouter provides unified access to multiple LLM providers
    through a single API compatible with OpenAI's format.
    """

    def __init__(self) -> None:
        """Initialize OpenRouter client with configuration."""
        settings = get_settings()
        self.api_key = settings.openrouter.openrouter_api_key
        self.base_url = settings.openrouter.openrouter_base_url
        self.timeout = settings.openrouter.openrouter_timeout
        self.max_retries = settings.openrouter.openrouter_max_retries

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://aion-assistant.app",
                "X-Title": "AION Personal Assistant",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )

        self.logger.info(
            "openrouter_client_initialized",
            base_url=self.base_url,
            timeout=self.timeout,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        self.logger.info("openrouter_client_closed")

    async def __aenter__(self) -> "OpenRouterClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _make_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make a request to OpenRouter API with retry logic.

        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request payload

        Returns:
            Response JSON

        Raises:
            LLMServiceError: If request fails after retries
        """
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            self.logger.error(
                "openrouter_http_error",
                status_code=e.response.status_code,
                error=str(e),
                endpoint=endpoint,
            )
            raise LLMServiceError(
                f"OpenRouter API error: {e.response.status_code}",
                details={
                    "status_code": e.response.status_code,
                    "response": e.response.text,
                    "endpoint": endpoint,
                },
            ) from e

        except httpx.TimeoutException as e:
            self.logger.error(
                "openrouter_timeout",
                error=str(e),
                endpoint=endpoint,
                timeout=self.timeout,
            )
            raise LLMServiceError(
                "OpenRouter API request timeout",
                details={"endpoint": endpoint, "timeout": self.timeout},
            ) from e

        except Exception as e:
            self.logger.error(
                "openrouter_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                endpoint=endpoint,
            )
            raise LLMServiceError(
                f"Unexpected error calling OpenRouter: {str(e)}",
                details={"error_type": type(e).__name__, "endpoint": endpoint},
            ) from e

    async def generate_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: list[str] | None = None,
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        response_format: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a chat completion using OpenRouter.

        Args:
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            stop: Stop sequences
            stream: Whether to stream the response
            tools: List of tool definitions for function calling
            tool_choice: Tool choice strategy ("auto", "none", or specific tool)
            response_format: Response format (e.g., {"type": "json_object"} to force JSON)

        Returns:
            Completion response

        Raises:
            LLMServiceError: If generation fails
        """
        self.logger.info(
            "generating_completion",
            model=model,
            num_messages=len(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            has_tools=tools is not None,
        )

        data: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": stream,
        }

        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        if stop is not None:
            data["stop"] = stop

        # Add response format if specified (e.g., for JSON mode)
        if response_format is not None:
            data["response_format"] = response_format
            self.logger.info("response_format_set", format_type=response_format.get("type"))

        # Add tool calling parameters if tools are provided
        if tools is not None and len(tools) > 0:
            data["tools"] = tools
            data["tool_choice"] = tool_choice
            self.logger.info("tools_included", num_tools=len(tools))

        response = await self._make_request("/chat/completions", data=data)

        self.logger.info(
            "completion_generated",
            model=model,
            usage=response.get("usage", {}),
            has_tool_calls=response.get("choices", [{}])[0]
            .get("message", {})
            .get("tool_calls")
            is not None,
        )

        return response

    async def generate_embeddings(
        self, model: str, texts: list[str]
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            model: Embedding model identifier
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            LLMServiceError: If embedding generation fails
        """
        self.logger.info(
            "generating_embeddings",
            model=model,
            num_texts=len(texts),
        )

        data = {
            "model": model,
            "input": texts,
        }

        response = await self._make_request("/embeddings", data=data)

        # Extract embeddings from response
        embeddings = [item["embedding"] for item in response["data"]]

        self.logger.info(
            "embeddings_generated",
            model=model,
            num_embeddings=len(embeddings),
            embedding_dimension=len(embeddings[0]) if embeddings else 0,
        )

        return embeddings

    async def generate_single_embedding(
        self, model: str, text: str
    ) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            model: Embedding model identifier
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            LLMServiceError: If embedding generation fails
        """
        embeddings = await self.generate_embeddings(model, [text])
        return embeddings[0]

    async def get_available_models(self) -> list[dict[str, Any]]:
        """
        Get list of available models from OpenRouter.

        Returns:
            List of model information

        Raises:
            LLMServiceError: If request fails
        """
        try:
            response = await self._make_request("/models", method="GET")
            return response.get("data", [])
        except Exception as e:
            self.logger.error("failed_to_get_models", error=str(e))
            raise LLMServiceError(
                "Failed to get available models",
                details={"error": str(e)},
            ) from e
