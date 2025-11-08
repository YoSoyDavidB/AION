"""
Custom exceptions for AION.
Provides clear, structured error handling across the application.
"""

from typing import Any


class AIONException(Exception):
    """Base exception for all AION errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# Domain Exceptions


class DomainException(AIONException):
    """Base exception for domain layer errors."""

    pass


class EntityNotFoundError(DomainException):
    """Raised when a requested entity is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"{entity_type} not found",
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class EntityValidationError(DomainException):
    """Raised when entity validation fails."""

    def __init__(self, entity_type: str, errors: dict[str, Any]) -> None:
        super().__init__(
            f"{entity_type} validation failed",
            details={"entity_type": entity_type, "errors": errors},
        )


class ValidationError(DomainException):
    """Raised when input validation fails."""

    pass


# Infrastructure Exceptions


class InfrastructureException(AIONException):
    """Base exception for infrastructure layer errors."""

    pass


class VectorStoreError(InfrastructureException):
    """Raised when vector store operations fail."""

    pass


class GraphDatabaseError(InfrastructureException):
    """Raised when graph database operations fail."""

    pass


class DatabaseError(InfrastructureException):
    """Raised when relational database operations fail."""

    pass


class LLMServiceError(InfrastructureException):
    """Raised when LLM service calls fail."""

    pass


class EmbeddingServiceError(InfrastructureException):
    """Raised when embedding generation fails."""

    pass


class GitHubSyncError(InfrastructureException):
    """Raised when GitHub synchronization fails."""

    pass


# Application Exceptions


class ApplicationException(AIONException):
    """Base exception for application layer errors."""

    pass


class UseCaseExecutionError(ApplicationException):
    """Raised when use case execution fails."""

    pass


class InvalidInputError(ApplicationException):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(
            "Invalid input", details={"field": field, "validation_error": message}
        )


class MemoryLimitExceededError(ApplicationException):
    """Raised when memory storage limits are exceeded."""

    pass


class RateLimitExceededError(ApplicationException):
    """Raised when rate limits are exceeded."""

    def __init__(self, limit: int, window: str) -> None:
        super().__init__(
            "Rate limit exceeded",
            details={"limit": limit, "window": window},
        )


# Presentation Exceptions


class PresentationException(AIONException):
    """Base exception for presentation layer errors."""

    pass


class AuthenticationError(PresentationException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(PresentationException):
    """Raised when user lacks required permissions."""

    pass


class APIValidationError(PresentationException):
    """Raised when API request validation fails."""

    pass


# Security Exceptions


class SecurityException(AIONException):
    """Base exception for security-related errors."""

    pass


class EncryptionError(SecurityException):
    """Raised when encryption/decryption fails."""

    pass


class TokenError(SecurityException):
    """Raised when token operations fail."""

    pass


# Utility function for error mapping


def get_http_status_code(exception: Exception) -> int:
    """
    Map exceptions to HTTP status codes.

    Args:
        exception: Exception instance

    Returns:
        HTTP status code
    """
    error_mapping: dict[type, int] = {
        EntityNotFoundError: 404,
        EntityValidationError: 422,
        InvalidInputError: 422,
        APIValidationError: 422,
        AuthenticationError: 401,
        AuthorizationError: 403,
        RateLimitExceededError: 429,
        MemoryLimitExceededError: 507,
        VectorStoreError: 503,
        GraphDatabaseError: 503,
        DatabaseError: 503,
        LLMServiceError: 503,
        EmbeddingServiceError: 503,
        GitHubSyncError: 502,
        SecurityException: 500,
    }

    for exc_type, status_code in error_mapping.items():
        if isinstance(exception, exc_type):
            return status_code

    # Default to 500 for unknown errors
    return 500
