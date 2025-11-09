"""
Microsoft OAuth2 and Graph API client for Outlook Calendar and Email.
"""

from datetime import datetime, timedelta
from typing import List

import msal
from msgraph import GraphServiceClient
from msgraph.generated.models.message import Message as GraphMessage
from msgraph.generated.models.event import Event as GraphEvent
from azure.identity import ClientSecretCredential

from src.config.settings import MicrosoftOAuthSettings
from src.domain.entities.calendar_event import CalendarEvent
from src.domain.entities.email import Email, EmailAddress
from src.domain.entities.oauth_token import OAuthProvider, OAuthToken
from src.shared.logging import get_logger

logger = get_logger(__name__)


class MicrosoftOAuthClient:
    """Microsoft OAuth2 client for authentication."""

    def __init__(self, settings: MicrosoftOAuthSettings):
        """Initialize Microsoft OAuth client."""
        self.settings = settings
        self.msal_app = msal.ConfidentialClientApplication(
            settings.microsoft_client_id,
            authority=settings.authority,
            client_credential=settings.microsoft_client_secret,
        )
        logger.info("microsoft_oauth_client_initialized")

    def get_authorization_url(self, state: str) -> str:
        """Get OAuth authorization URL."""
        auth_url = self.msal_app.get_authorization_request_url(
            scopes=self.settings.microsoft_scopes,
            state=state,
            redirect_uri=self.settings.microsoft_redirect_uri,
        )
        return auth_url

    def exchange_code_for_token(self, code: str, user_id: str) -> OAuthToken:
        """Exchange authorization code for access token."""
        result = self.msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.settings.microsoft_scopes,
            redirect_uri=self.settings.microsoft_redirect_uri,
        )

        if "error" in result:
            error_msg = result.get("error_description", result.get("error"))
            logger.error("microsoft_token_exchange_failed", error=error_msg)
            raise ValueError(f"Token exchange failed: {error_msg}")

        # Get user info
        user_info = result.get("id_token_claims", {})

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600))

        return OAuthToken(
            user_id=user_id,
            provider=OAuthProvider.MICROSOFT,
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            token_type="Bearer",
            expires_at=expires_at,
            scopes=result.get("scope", "").split() if result.get("scope") else self.settings.microsoft_scopes,
            provider_user_id=user_info.get("oid"),
            provider_user_email=user_info.get("preferred_username") or user_info.get("email"),
            provider_user_name=user_info.get("name"),
        )

    def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresh an expired token."""
        if not token.refresh_token:
            raise ValueError("No refresh token available")

        result = self.msal_app.acquire_token_by_refresh_token(
            token.refresh_token,
            scopes=token.scopes,
        )

        if "error" in result:
            error_msg = result.get("error_description", result.get("error"))
            logger.error("microsoft_token_refresh_failed", error=error_msg)
            raise ValueError(f"Token refresh failed: {error_msg}")

        # Update token
        token.access_token = result["access_token"]
        if result.get("refresh_token"):
            token.refresh_token = result["refresh_token"]
        token.expires_at = datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600))
        token.updated_at = datetime.utcnow()

        return token


class MicrosoftCalendarClient:
    """Microsoft Graph Calendar API client."""

    def __init__(self, access_token: str):
        """Initialize Microsoft Calendar client."""
        self.access_token = access_token
        logger.info("microsoft_calendar_client_initialized")

    async def get_events(
        self,
        user_id: str,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 100,
    ) -> List[CalendarEvent]:
        """Get calendar events using direct API calls."""
        try:
            import httpx

            # Default to next 30 days if not specified
            if not time_min:
                time_min = datetime.utcnow()
            if not time_max:
                time_max = datetime.utcnow() + timedelta(days=30)

            # Build filter query
            filter_query = f"start/dateTime ge '{time_min.isoformat()}' and end/dateTime le '{time_max.isoformat()}'"

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me/events",
                    headers=headers,
                    params={
                        "$filter": filter_query,
                        "$top": max_results,
                        "$orderby": "start/dateTime",
                    },
                )
                response.raise_for_status()
                data = response.json()

            events = data.get("value", [])
            return [self._parse_event(event, user_id) for event in events]

        except Exception as e:
            logger.error("get_microsoft_calendar_events_failed", error=str(e))
            raise

    def _parse_event(self, event_data: dict, user_id: str) -> CalendarEvent:
        """Parse Microsoft Graph event to domain entity."""
        # Parse start/end times
        start_info = event_data["start"]
        end_info = event_data["end"]

        start_time = datetime.fromisoformat(start_info["dateTime"])
        end_time = datetime.fromisoformat(end_info["dateTime"])
        is_all_day = event_data.get("isAllDay", False)

        # Parse attendees
        attendees = []
        for attendee in event_data.get("attendees", []):
            email_address = attendee.get("emailAddress", {})
            attendees.append({
                "email": email_address.get("address"),
                "name": email_address.get("name"),
                "response_status": attendee.get("status", {}).get("response"),
            })

        # Parse organizer
        organizer = event_data.get("organizer", {}).get("emailAddress", {})

        # Parse meeting URL
        meeting_url = None
        if event_data.get("onlineMeeting"):
            meeting_url = event_data["onlineMeeting"].get("joinUrl")

        return CalendarEvent(
            user_id=user_id,
            provider=OAuthProvider.MICROSOFT,
            provider_event_id=event_data["id"],
            calendar_id=event_data.get("calendarId", "default"),
            title=event_data.get("subject", "No Title"),
            description=event_data.get("bodyPreview") or event_data.get("body", {}).get("content"),
            location=event_data.get("location", {}).get("displayName"),
            start_time=start_time,
            end_time=end_time,
            is_all_day=is_all_day,
            timezone=start_info.get("timeZone"),
            organizer_email=organizer.get("address"),
            organizer_name=organizer.get("name"),
            attendees=attendees,
            status=event_data.get("responseStatus", {}).get("response"),
            is_recurring=bool(event_data.get("recurrence")),
            recurrence_rule=str(event_data.get("recurrence")) if event_data.get("recurrence") else None,
            meeting_url=meeting_url,
            conference_data=event_data.get("onlineMeeting"),
            raw_data=event_data,
        )


class MicrosoftEmailClient:
    """Microsoft Graph Mail API client."""

    def __init__(self, access_token: str):
        """Initialize Microsoft Email client."""
        self.access_token = access_token
        logger.info("microsoft_email_client_initialized")

    async def get_messages(
        self,
        user_id: str,
        max_results: int = 50,
        folder: str = "inbox",
    ) -> List[Email]:
        """Get email messages using direct API calls."""
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder}/messages",
                    headers=headers,
                    params={
                        "$top": max_results,
                        "$orderby": "receivedDateTime desc",
                        "$select": "id,subject,bodyPreview,from,toRecipients,ccRecipients,receivedDateTime,isRead,importance,flag,hasAttachments,internetMessageId,conversationId",
                    },
                )
                response.raise_for_status()
                data = response.json()

            messages = data.get("value", [])
            emails = []

            for message in messages:
                # Get full message body
                email = await self._get_message_details(message["id"], user_id, headers)
                if email:
                    emails.append(email)

            return emails

        except Exception as e:
            logger.error("get_microsoft_email_messages_failed", error=str(e))
            raise

    async def _get_message_details(self, message_id: str, user_id: str, headers: dict) -> Email | None:
        """Get detailed message information."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://graph.microsoft.com/v1.0/me/messages/{message_id}",
                    headers=headers,
                )
                response.raise_for_status()
                message_data = response.json()

            return self._parse_message(message_data, user_id)

        except Exception as e:
            logger.error("get_message_details_failed", error=str(e), message_id=message_id)
            return None

    def _parse_message(self, message_data: dict, user_id: str) -> Email:
        """Parse Microsoft Graph message to domain entity."""
        # Parse from address
        from_info = message_data.get("from", {}).get("emailAddress", {})
        from_email = EmailAddress(
            email=from_info.get("address", ""),
            name=from_info.get("name")
        )

        # Parse to addresses
        to_emails = [
            EmailAddress(email=addr["emailAddress"]["address"], name=addr["emailAddress"].get("name"))
            for addr in message_data.get("toRecipients", [])
        ]

        # Parse cc addresses
        cc_emails = [
            EmailAddress(email=addr["emailAddress"]["address"], name=addr["emailAddress"].get("name"))
            for addr in message_data.get("ccRecipients", [])
        ]

        # Parse body
        body_info = message_data.get("body", {})
        body_html = body_info.get("content") if body_info.get("contentType") == "html" else None
        body_text = body_info.get("content") if body_info.get("contentType") == "text" else message_data.get("bodyPreview")

        # Parse flags
        is_read = message_data.get("isRead", False)
        is_important = message_data.get("importance") == "high"
        is_starred = message_data.get("flag", {}).get("flagStatus") == "flagged"

        return Email(
            user_id=user_id,
            provider=OAuthProvider.MICROSOFT,
            provider_email_id=message_data["id"],
            thread_id=message_data.get("conversationId"),
            from_address=from_email,
            to_addresses=to_emails,
            cc_addresses=cc_emails,
            subject=message_data.get("subject", "No Subject"),
            body_text=body_text,
            body_html=body_html,
            snippet=message_data.get("bodyPreview"),
            sent_at=datetime.fromisoformat(message_data["sentDateTime"].replace("Z", "+00:00")),
            received_at=datetime.fromisoformat(message_data["receivedDateTime"].replace("Z", "+00:00")) if message_data.get("receivedDateTime") else None,
            is_read=is_read,
            is_important=is_important,
            is_starred=is_starred,
            labels=message_data.get("categories", []),
            folder=message_data.get("parentFolderId", "inbox"),
            has_attachments=message_data.get("hasAttachments", False),
            raw_data=message_data,
        )
