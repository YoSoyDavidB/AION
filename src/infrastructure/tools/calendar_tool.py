"""
Calendar tool for accessing user's calendar events.
"""

from datetime import datetime, timedelta
from typing import Any

from google.oauth2.credentials import Credentials as GoogleCredentials

from src.config.settings import get_settings
from src.domain.entities.oauth_token import OAuthProvider
from src.domain.entities.tool import BaseTool, ToolParameter
from src.infrastructure.integrations import (
    GoogleCalendarClient,
    GoogleOAuthClient,
    MicrosoftCalendarClient,
    MicrosoftOAuthClient,
)
from src.infrastructure.persistence.oauth_token_repository import OAuthTokenRepository
from src.shared.logging import LoggerMixin


class CalendarTool(BaseTool, LoggerMixin):
    """
    Calendar tool for retrieving user's calendar events.

    Automatically detects which calendar provider (Google/Microsoft)
    is connected and fetches upcoming events.
    """

    def __init__(self, token_repo: OAuthTokenRepository):
        """
        Initialize Calendar tool.

        Args:
            token_repo: OAuth token repository for accessing user credentials
        """
        self.token_repo = token_repo
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "get_calendar_events"

    @property
    def description(self) -> str:
        return """Get upcoming calendar events from the user's connected calendar (Google Calendar or Outlook Calendar).
Use this tool when the user asks about:
- Their schedule or calendar
- Upcoming meetings or events
- What they have planned today/this week
- If they're free at a certain time
- Meeting details or event information

The tool automatically detects which calendar provider is connected (Google or Microsoft) and retrieves events accordingly.
Returns a list of upcoming events with titles, times, locations, and attendees."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="user_id",
                type="string",
                description="User ID to get calendar events for",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of events to return (default: 10, max: 50)",
                required=False,
            ),
            ToolParameter(
                name="days_ahead",
                type="number",
                description="Number of days ahead to look for events (default: 7)",
                required=False,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Get calendar events.

        Args:
            user_id: User ID
            max_results: Maximum events to return (default 10)
            days_ahead: Days ahead to search (default 7)

        Returns:
            Dictionary with calendar events or error message

        Raises:
            ValueError: If required parameters are missing
            Exception: If calendar access fails
        """
        user_id = kwargs.get("user_id")
        max_results = int(kwargs.get("max_results", 10))
        days_ahead = int(kwargs.get("days_ahead", 7))

        if not user_id:
            raise ValueError("Missing required parameter: user_id")

        # Limit max_results
        max_results = min(max_results, 50)

        self.logger.info(
            "calendar_tool_executing",
            user_id=user_id,
            max_results=max_results,
            days_ahead=days_ahead,
        )

        try:
            # Try Google Calendar first
            google_token = await self.token_repo.get_by_user_and_provider(
                user_id, OAuthProvider.GOOGLE
            )

            if google_token:
                return await self._get_google_calendar_events(
                    user_id, google_token, max_results
                )

            # Try Microsoft Calendar
            microsoft_token = await self.token_repo.get_by_user_and_provider(
                user_id, OAuthProvider.MICROSOFT
            )

            if microsoft_token:
                return await self._get_microsoft_calendar_events(
                    user_id, microsoft_token, max_results
                )

            # No calendar connected
            self.logger.warning("calendar_tool_no_connection", user_id=user_id)
            return {
                "error": "No calendar connected",
                "message": "Please connect your Google or Microsoft account to access calendar events.",
                "events": [],
            }

        except Exception as e:
            self.logger.error("calendar_tool_error", user_id=user_id, error=str(e))
            raise Exception(f"Failed to retrieve calendar events: {str(e)}") from e

    async def _get_google_calendar_events(
        self, user_id: str, token, max_results: int
    ) -> dict[str, Any]:
        """Get events from Google Calendar."""
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

            # Get events
            calendar_client = GoogleCalendarClient(credentials)
            events = calendar_client.get_events(user_id, max_results=max_results)

            # Update last used
            await self.token_repo.update_last_used(token.token_id)

            # Format events
            formatted_events = [
                {
                    "title": event.title,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "location": event.location,
                    "is_all_day": event.is_all_day,
                    "organizer": event.organizer_email,
                    "attendees": [
                        {"email": att.get("email"), "name": att.get("displayName")}
                        for att in event.attendees
                    ],
                    "description": event.description[:200] + "..."
                    if event.description and len(event.description) > 200
                    else event.description,
                }
                for event in events
            ]

            self.logger.info(
                "calendar_tool_success_google",
                user_id=user_id,
                events_count=len(formatted_events),
            )

            return {
                "provider": "Google Calendar",
                "events_count": len(formatted_events),
                "events": formatted_events,
            }

        except Exception as e:
            self.logger.error("google_calendar_error", user_id=user_id, error=str(e))
            raise

    async def _get_microsoft_calendar_events(
        self, user_id: str, token, max_results: int
    ) -> dict[str, Any]:
        """Get events from Microsoft Calendar."""
        try:
            # Refresh token if needed
            if token.needs_refresh:
                oauth_client = MicrosoftOAuthClient(self.settings.microsoft_oauth)
                token = oauth_client.refresh_token(token)
                await self.token_repo.save(token)

            # Get events
            calendar_client = MicrosoftCalendarClient(token.access_token)
            events = await calendar_client.get_events(user_id, max_results=max_results)

            # Update last used
            await self.token_repo.update_last_used(token.token_id)

            # Format events
            formatted_events = [
                {
                    "title": event.title,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "location": event.location,
                    "is_all_day": event.is_all_day,
                    "organizer": event.organizer_email,
                    "attendees": [
                        {"email": att.get("email"), "name": att.get("name")}
                        for att in event.attendees
                    ],
                    "description": event.description[:200] + "..."
                    if event.description and len(event.description) > 200
                    else event.description,
                }
                for event in events
            ]

            self.logger.info(
                "calendar_tool_success_microsoft",
                user_id=user_id,
                events_count=len(formatted_events),
            )

            return {
                "provider": "Microsoft Outlook Calendar",
                "events_count": len(formatted_events),
                "events": formatted_events,
            }

        except Exception as e:
            self.logger.error(
                "microsoft_calendar_error", user_id=user_id, error=str(e)
            )
            raise
