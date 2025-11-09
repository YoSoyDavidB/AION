"""
Email tool for accessing user's email messages.
"""

from typing import Any

from google.oauth2.credentials import Credentials as GoogleCredentials

from src.config.settings import get_settings
from src.domain.entities.oauth_token import OAuthProvider
from src.domain.entities.tool import BaseTool, ToolParameter
from src.infrastructure.integrations import (
    GoogleGmailClient,
    GoogleOAuthClient,
    MicrosoftEmailClient,
    MicrosoftOAuthClient,
)
from src.infrastructure.persistence.oauth_token_repository import OAuthTokenRepository
from src.shared.logging import LoggerMixin


class EmailTool(BaseTool, LoggerMixin):
    """
    Email tool for retrieving user's email messages.

    Automatically detects which email provider (Gmail/Outlook)
    is connected and fetches recent messages.
    """

    def __init__(self, token_repo: OAuthTokenRepository):
        """
        Initialize Email tool.

        Args:
            token_repo: OAuth token repository for accessing user credentials
        """
        self.token_repo = token_repo
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "get_email_messages"

    @property
    def description(self) -> str:
        return """Get recent email messages from the user's connected email account (Gmail or Outlook).
Use this tool when the user asks about:
- Their emails or inbox
- Recent messages or correspondence
- If they received an email from someone
- Important or unread emails
- Email content or details

The tool automatically detects which email provider is connected (Google Gmail or Microsoft Outlook) and retrieves messages accordingly.
Returns a list of recent emails with subjects, senders, snippets, and read status."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="user_id",
                type="string",
                description="User ID to get email messages for",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of messages to return (default: 10, max: 50)",
                required=False,
            ),
            ToolParameter(
                name="only_unread",
                type="boolean",
                description="Only return unread messages (default: false)",
                required=False,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Get email messages.

        Args:
            user_id: User ID
            max_results: Maximum messages to return (default 10)
            only_unread: Only return unread messages (default False)

        Returns:
            Dictionary with email messages or error message

        Raises:
            ValueError: If required parameters are missing
            Exception: If email access fails
        """
        user_id = kwargs.get("user_id")
        max_results = int(kwargs.get("max_results", 10))
        only_unread = kwargs.get("only_unread", False)

        if not user_id:
            raise ValueError("Missing required parameter: user_id")

        # Limit max_results
        max_results = min(max_results, 50)

        self.logger.info(
            "email_tool_executing",
            user_id=user_id,
            max_results=max_results,
            only_unread=only_unread,
        )

        try:
            # Try Gmail first
            google_token = await self.token_repo.get_by_user_and_provider(
                user_id, OAuthProvider.GOOGLE
            )

            if google_token:
                return await self._get_gmail_messages(
                    user_id, google_token, max_results, only_unread
                )

            # Try Outlook
            microsoft_token = await self.token_repo.get_by_user_and_provider(
                user_id, OAuthProvider.MICROSOFT
            )

            if microsoft_token:
                return await self._get_outlook_messages(
                    user_id, microsoft_token, max_results, only_unread
                )

            # No email connected
            self.logger.warning("email_tool_no_connection", user_id=user_id)
            return {
                "error": "No email account connected",
                "message": "Please connect your Google or Microsoft account to access email messages.",
                "messages": [],
            }

        except Exception as e:
            self.logger.error("email_tool_error", user_id=user_id, error=str(e))
            raise Exception(f"Failed to retrieve email messages: {str(e)}") from e

    async def _get_gmail_messages(
        self, user_id: str, token, max_results: int, only_unread: bool
    ) -> dict[str, Any]:
        """Get messages from Gmail."""
        try:
            # Refresh token if needed
            if token.needs_refresh:
                oauth_client = GoogleOAuthClient(self.settings.google_oauth)
                token = oauth_client.refresh_token(token)
                await self.token_repo.save(token)

            # Create credentials
            credentials = GoogleCredentials(
                token=token.access_token,
                refresh_token=token.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.google_oauth.google_client_id,
                client_secret=self.settings.google_oauth.google_client_secret,
                scopes=token.scopes,
            )

            # Get messages
            gmail_client = GoogleGmailClient(credentials)
            messages = gmail_client.get_messages(user_id, max_results=max_results)

            # Filter unread if requested
            if only_unread:
                messages = [msg for msg in messages if not msg.is_read]

            # Update last used
            await self.token_repo.update_last_used(token.token_id)

            # Format messages
            formatted_messages = [
                {
                    "subject": msg.subject,
                    "from": {
                        "email": msg.from_address.email,
                        "name": msg.from_address.name,
                    },
                    "snippet": msg.snippet,
                    "sent_at": msg.sent_at.isoformat(),
                    "is_read": msg.is_read,
                    "is_important": msg.is_important,
                }
                for msg in messages
            ]

            self.logger.info(
                "email_tool_success_gmail",
                user_id=user_id,
                messages_count=len(formatted_messages),
                unread_count=sum(1 for m in messages if not m.is_read),
            )

            return {
                "provider": "Gmail",
                "messages_count": len(formatted_messages),
                "unread_count": sum(1 for m in formatted_messages if not m["is_read"]),
                "messages": formatted_messages,
            }

        except Exception as e:
            self.logger.error("gmail_error", user_id=user_id, error=str(e))
            raise

    async def _get_outlook_messages(
        self, user_id: str, token, max_results: int, only_unread: bool
    ) -> dict[str, Any]:
        """Get messages from Outlook."""
        try:
            # Refresh token if needed
            if token.needs_refresh:
                oauth_client = MicrosoftOAuthClient(self.settings.microsoft_oauth)
                token = oauth_client.refresh_token(token)
                await self.token_repo.save(token)

            # Get messages
            email_client = MicrosoftEmailClient(token.access_token)
            messages = await email_client.get_messages(user_id, max_results=max_results)

            # Filter unread if requested
            if only_unread:
                messages = [msg for msg in messages if not msg.is_read]

            # Update last used
            await self.token_repo.update_last_used(token.token_id)

            # Format messages
            formatted_messages = [
                {
                    "subject": msg.subject,
                    "from": {
                        "email": msg.from_address.email,
                        "name": msg.from_address.name,
                    },
                    "snippet": msg.snippet,
                    "sent_at": msg.sent_at.isoformat(),
                    "is_read": msg.is_read,
                    "is_important": msg.is_important,
                }
                for msg in messages
            ]

            self.logger.info(
                "email_tool_success_outlook",
                user_id=user_id,
                messages_count=len(formatted_messages),
                unread_count=sum(1 for m in messages if not m.is_read),
            )

            return {
                "provider": "Microsoft Outlook",
                "messages_count": len(formatted_messages),
                "unread_count": sum(1 for m in formatted_messages if not m["is_read"]),
                "messages": formatted_messages,
            }

        except Exception as e:
            self.logger.error("outlook_error", user_id=user_id, error=str(e))
            raise
