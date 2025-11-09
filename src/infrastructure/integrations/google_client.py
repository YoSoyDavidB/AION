"""
Google OAuth2 and API client for Calendar and Gmail.
"""

from datetime import datetime, timedelta
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from src.config.settings import GoogleOAuthSettings
from src.domain.entities.calendar_event import CalendarEvent
from src.domain.entities.email import Email, EmailAddress
from src.domain.entities.oauth_token import OAuthProvider, OAuthToken
from src.shared.logging import get_logger

logger = get_logger(__name__)


class GoogleOAuthClient:
    """Google OAuth2 client for authentication."""

    def __init__(self, settings: GoogleOAuthSettings):
        """Initialize Google OAuth client."""
        self.settings = settings
        logger.info("google_oauth_client_initialized")

    def get_authorization_url(self, state: str) -> str:
        """Get OAuth authorization URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.settings.google_redirect_uri],
                }
            },
            scopes=self.settings.google_scopes,
        )
        flow.redirect_uri = self.settings.google_redirect_uri

        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",
        )

        return authorization_url

    def exchange_code_for_token(self, code: str, user_id: str) -> OAuthToken:
        """Exchange authorization code for access token."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.settings.google_redirect_uri],
                }
            },
            scopes=self.settings.google_scopes,
        )
        flow.redirect_uri = self.settings.google_redirect_uri
        flow.fetch_token(code=code)

        credentials = flow.credentials

        # Get user info
        user_info = self._get_user_info(credentials)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.timestamp() - datetime.utcnow().timestamp() if credentials.expiry else 3600)

        return OAuthToken(
            user_id=user_id,
            provider=OAuthProvider.GOOGLE,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_type="Bearer",
            expires_at=expires_at,
            scopes=credentials.scopes or self.settings.google_scopes,
            provider_user_id=user_info.get("id"),
            provider_user_email=user_info.get("email"),
            provider_user_name=user_info.get("name"),
        )

    def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresh an expired token."""
        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.google_client_id,
            client_secret=self.settings.google_client_secret,
            scopes=token.scopes,
        )

        credentials.refresh(Request())

        # Update token
        token.access_token = credentials.token
        if credentials.refresh_token:
            token.refresh_token = credentials.refresh_token
        token.expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.timestamp() - datetime.utcnow().timestamp() if credentials.expiry else 3600)
        token.updated_at = datetime.utcnow()

        return token

    def _get_user_info(self, credentials: Credentials) -> dict:
        """Get user info from Google."""
        try:
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            logger.error("get_google_user_info_failed", error=str(e))
            return {}


class GoogleCalendarClient:
    """Google Calendar API client."""

    def __init__(self, credentials: Credentials):
        """Initialize Google Calendar client."""
        self.service = build("calendar", "v3", credentials=credentials)
        logger.info("google_calendar_client_initialized")

    def get_events(
        self,
        user_id: str,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 100,
    ) -> List[CalendarEvent]:
        """Get calendar events."""
        try:
            # Default to next 30 days if not specified
            if not time_min:
                time_min = datetime.utcnow()
            if not time_max:
                time_max = datetime.utcnow() + timedelta(days=30)

            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = events_result.get("items", [])

            return [self._parse_event(event, user_id) for event in events]

        except Exception as e:
            logger.error("get_google_calendar_events_failed", error=str(e))
            raise

    def _parse_event(self, event_data: dict, user_id: str) -> CalendarEvent:
        """Parse Google Calendar event to domain entity."""
        start = event_data["start"]
        end = event_data["end"]

        # Parse start/end times
        if "dateTime" in start:
            start_time = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
            is_all_day = False
        else:
            # All-day event
            start_time = datetime.fromisoformat(start["date"] + "T00:00:00")
            end_time = datetime.fromisoformat(end["date"] + "T23:59:59")
            is_all_day = True

        # Parse attendees
        attendees = []
        for attendee in event_data.get("attendees", []):
            attendees.append({
                "email": attendee.get("email"),
                "name": attendee.get("displayName"),
                "response_status": attendee.get("responseStatus"),
            })

        return CalendarEvent(
            user_id=user_id,
            provider=OAuthProvider.GOOGLE,
            provider_event_id=event_data["id"],
            calendar_id=event_data.get("organizer", {}).get("email", "primary"),
            title=event_data.get("summary", "No Title"),
            description=event_data.get("description"),
            location=event_data.get("location"),
            start_time=start_time,
            end_time=end_time,
            is_all_day=is_all_day,
            timezone=start.get("timeZone"),
            organizer_email=event_data.get("organizer", {}).get("email"),
            organizer_name=event_data.get("organizer", {}).get("displayName"),
            attendees=attendees,
            status=event_data.get("status"),
            is_recurring=bool(event_data.get("recurrence")),
            recurrence_rule=event_data.get("recurrence", [None])[0] if event_data.get("recurrence") else None,
            meeting_url=event_data.get("hangoutLink"),
            conference_data=event_data.get("conferenceData"),
            raw_data=event_data,
        )


class GoogleGmailClient:
    """Google Gmail API client."""

    def __init__(self, credentials: Credentials):
        """Initialize Gmail client."""
        self.service = build("gmail", "v1", credentials=credentials)
        logger.info("google_gmail_client_initialized")

    def get_messages(
        self,
        user_id: str,
        max_results: int = 50,
        query: str = "in:inbox",
    ) -> List[Email]:
        """Get Gmail messages."""
        try:
            results = self.service.users().messages().list(
                userId="me",
                maxResults=max_results,
                q=query,
            ).execute()

            messages = results.get("messages", [])

            emails = []
            for message in messages:
                email = self._get_message_details(message["id"], user_id)
                if email:
                    emails.append(email)

            return emails

        except Exception as e:
            logger.error("get_gmail_messages_failed", error=str(e))
            raise

    def _get_message_details(self, message_id: str, user_id: str) -> Email | None:
        """Get detailed message information."""
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            return self._parse_message(message, user_id)

        except Exception as e:
            logger.error("get_message_details_failed", error=str(e), message_id=message_id)
            return None

    def _parse_message(self, message_data: dict, user_id: str) -> Email:
        """Parse Gmail message to domain entity."""
        headers = {h["name"]: h["value"] for h in message_data["payload"]["headers"]}

        # Parse email addresses
        from_email = self._parse_email_address(headers.get("From", ""))
        to_emails = [self._parse_email_address(addr) for addr in headers.get("To", "").split(",")]
        cc_emails = [self._parse_email_address(addr) for addr in headers.get("Cc", "").split(",")] if headers.get("Cc") else []

        # Get body
        body_text, body_html = self._extract_body(message_data["payload"])

        # Parse labels
        labels = message_data.get("labelIds", [])
        is_read = "UNREAD" not in labels
        is_starred = "STARRED" in labels
        is_important = "IMPORTANT" in labels

        return Email(
            user_id=user_id,
            provider=OAuthProvider.GOOGLE,
            provider_email_id=message_data["id"],
            thread_id=message_data.get("threadId"),
            from_address=from_email,
            to_addresses=to_emails,
            cc_addresses=cc_emails,
            subject=headers.get("Subject", "No Subject"),
            body_text=body_text,
            body_html=body_html,
            snippet=message_data.get("snippet"),
            sent_at=datetime.fromtimestamp(int(message_data["internalDate"]) / 1000),
            is_read=is_read,
            is_important=is_important,
            is_starred=is_starred,
            labels=labels,
            has_attachments=any(part.get("filename") for part in message_data["payload"].get("parts", [])),
            raw_data=message_data,
        )

    def _parse_email_address(self, email_str: str) -> EmailAddress:
        """Parse email address string."""
        import re
        # Try to extract name and email from "Name <email@example.com>" format
        match = re.match(r"^(.+?)\s*<(.+?)>$", email_str.strip())
        if match:
            return EmailAddress(name=match.group(1).strip(), email=match.group(2).strip())
        return EmailAddress(email=email_str.strip())

    def _extract_body(self, payload: dict) -> tuple[str | None, str | None]:
        """Extract text and HTML body from message payload."""
        body_text = None
        body_html = None

        if "body" in payload and payload["body"].get("data"):
            import base64
            body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and part["body"].get("data"):
                    import base64
                    body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                elif part["mimeType"] == "text/html" and part["body"].get("data"):
                    import base64
                    body_html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

        return body_text, body_html
