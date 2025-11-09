"""
API routes for third-party integrations (Google, Microsoft).
"""

import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google.oauth2.credentials import Credentials as GoogleCredentials

from src.config.settings import get_settings
from src.domain.entities.oauth_token import OAuthProvider, OAuthToken
from src.domain.entities.calendar_event import CalendarEvent
from src.domain.entities.email import Email
from src.infrastructure.integrations import (
    GoogleOAuthClient,
    GoogleCalendarClient,
    GoogleGmailClient,
    MicrosoftOAuthClient,
    MicrosoftCalendarClient,
    MicrosoftEmailClient,
)
from src.infrastructure.persistence.oauth_token_repository import OAuthTokenRepository
from src.shared.logging import get_logger

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = get_logger(__name__)

# Temporary state storage (in production, use Redis or database)
_oauth_states = {}


class IntegrationStatusResponse(BaseModel):
    """Integration status response."""

    provider: str
    is_connected: bool
    user_email: str | None = None
    user_name: str | None = None
    connected_at: str | None = None


class CalendarEventResponse(BaseModel):
    """Calendar event response."""

    event_id: str
    title: str
    description: str | None
    start_time: str
    end_time: str
    location: str | None
    is_all_day: bool
    organizer_email: str | None
    attendees: List[dict]


class EmailResponse(BaseModel):
    """Email response."""

    email_id: str
    subject: str
    from_address: dict
    snippet: str | None
    sent_at: str
    is_read: bool
    is_important: bool


def get_token_repository() -> OAuthTokenRepository:
    """Get OAuth token repository."""
    settings = get_settings()
    return OAuthTokenRepository(settings.security.oauth_encryption_key)


# ============================================================================
# Google OAuth Routes
# ============================================================================


@router.get("/google/authorize")
async def google_authorize(user_id: str = Query(..., description="User ID")):
    """
    Initiate Google OAuth flow.

    Returns a redirect to Google's authorization page.
    """
    settings = get_settings()

    if not settings.google_oauth.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    # Generate state token
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {"provider": "google", "user_id": user_id}

    # Get authorization URL
    client = GoogleOAuthClient(settings.google_oauth)
    auth_url = client.get_authorization_url(state)

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """
    Handle Google OAuth callback.

    Exchanges the authorization code for an access token.
    """
    # Verify state
    state_data = _oauth_states.pop(state, None)
    if not state_data or state_data["provider"] != "google":
        raise HTTPException(status_code=400, detail="Invalid state token")

    user_id = state_data["user_id"]

    # Exchange code for token
    settings = get_settings()
    client = GoogleOAuthClient(settings.google_oauth)

    try:
        token = client.exchange_code_for_token(code, user_id)
        await token_repo.save(token)

        logger.info("google_oauth_connected", user_id=user_id, email=token.provider_user_email)

        # Redirect to frontend settings page
        return RedirectResponse(url=f"http://localhost:5174/settings?google_connected=true")

    except Exception as e:
        logger.error("google_oauth_callback_failed", error=str(e))
        return RedirectResponse(url=f"http://localhost:5174/settings?error=google_auth_failed")


@router.delete("/google/disconnect")
async def google_disconnect(
    user_id: str = Query(..., description="User ID"),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """Disconnect Google account."""
    success = await token_repo.delete_by_user_and_provider(user_id, OAuthProvider.GOOGLE)
    if success:
        logger.info("google_oauth_disconnected", user_id=user_id)
        return {"message": "Google account disconnected"}
    raise HTTPException(status_code=404, detail="No Google connection found")


@router.get("/google/status", response_model=IntegrationStatusResponse)
async def google_status(
    user_id: str = Query(..., description="User ID"),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """Get Google connection status."""
    token = await token_repo.get_by_user_and_provider(user_id, OAuthProvider.GOOGLE)

    if token:
        return IntegrationStatusResponse(
            provider="google",
            is_connected=True,
            user_email=token.provider_user_email,
            user_name=token.provider_user_name,
            connected_at=token.created_at.isoformat(),
        )

    return IntegrationStatusResponse(provider="google", is_connected=False)


@router.get("/google/calendar/events", response_model=List[CalendarEventResponse])
async def get_google_calendar_events(
    user_id: str = Query(..., description="User ID"),
    max_results: int = Query(50, description="Max number of events", ge=1, le=100),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """Get Google Calendar events."""
    token = await token_repo.get_by_user_and_provider(user_id, OAuthProvider.GOOGLE)
    if not token:
        raise HTTPException(status_code=404, detail="Google not connected")

    # Refresh token if needed
    if token.needs_refresh:
        settings = get_settings()
        oauth_client = GoogleOAuthClient(settings.google_oauth)
        token = oauth_client.refresh_token(token)
        await token_repo.save(token)

    # Get events
    credentials = GoogleCredentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=get_settings().google_oauth.google_client_id,
        client_secret=get_settings().google_oauth.google_client_secret,
        scopes=token.scopes,
    )

    calendar_client = GoogleCalendarClient(credentials)
    events = calendar_client.get_events(user_id, max_results=max_results)

    await token_repo.update_last_used(token.token_id)

    return [
        CalendarEventResponse(
            event_id=str(event.event_id),
            title=event.title,
            description=event.description,
            start_time=event.start_time.isoformat(),
            end_time=event.end_time.isoformat(),
            location=event.location,
            is_all_day=event.is_all_day,
            organizer_email=event.organizer_email,
            attendees=event.attendees,
        )
        for event in events
    ]


@router.get("/google/gmail/messages", response_model=List[EmailResponse])
async def get_google_gmail_messages(
    user_id: str = Query(..., description="User ID"),
    max_results: int = Query(20, description="Max number of messages", ge=1, le=50),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """Get Gmail messages."""
    token = await token_repo.get_by_user_and_provider(user_id, OAuthProvider.GOOGLE)
    if not token:
        raise HTTPException(status_code=404, detail="Google not connected")

    # Refresh token if needed
    if token.needs_refresh:
        settings = get_settings()
        oauth_client = GoogleOAuthClient(settings.google_oauth)
        token = oauth_client.refresh_token(token)
        await token_repo.save(token)

    # Get messages
    credentials = GoogleCredentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=get_settings().google_oauth.google_client_id,
        client_secret=get_settings().google_oauth.google_client_secret,
        scopes=token.scopes,
    )

    gmail_client = GoogleGmailClient(credentials)
    emails = gmail_client.get_messages(user_id, max_results=max_results)

    await token_repo.update_last_used(token.token_id)

    return [
        EmailResponse(
            email_id=str(email.email_id),
            subject=email.subject,
            from_address={"email": email.from_address.email, "name": email.from_address.name},
            snippet=email.snippet,
            sent_at=email.sent_at.isoformat(),
            is_read=email.is_read,
            is_important=email.is_important,
        )
        for email in emails
    ]


# ============================================================================
# Microsoft OAuth Routes
# ============================================================================


@router.get("/microsoft/authorize")
async def microsoft_authorize(user_id: str = Query(..., description="User ID")):
    """
    Initiate Microsoft OAuth flow.

    Returns a redirect to Microsoft's authorization page.
    """
    settings = get_settings()

    if not settings.microsoft_oauth.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Microsoft OAuth not configured. Please set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET.",
        )

    # Generate state token
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {"provider": "microsoft", "user_id": user_id}

    # Get authorization URL
    client = MicrosoftOAuthClient(settings.microsoft_oauth)
    auth_url = client.get_authorization_url(state)

    return RedirectResponse(url=auth_url)


@router.get("/microsoft/callback")
async def microsoft_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """
    Handle Microsoft OAuth callback.

    Exchanges the authorization code for an access token.
    """
    # Verify state
    state_data = _oauth_states.pop(state, None)
    if not state_data or state_data["provider"] != "microsoft":
        raise HTTPException(status_code=400, detail="Invalid state token")

    user_id = state_data["user_id"]

    # Exchange code for token
    settings = get_settings()
    client = MicrosoftOAuthClient(settings.microsoft_oauth)

    try:
        token = client.exchange_code_for_token(code, user_id)
        await token_repo.save(token)

        logger.info("microsoft_oauth_connected", user_id=user_id, email=token.provider_user_email)

        # Redirect to frontend settings page
        return RedirectResponse(url=f"http://localhost:5174/settings?microsoft_connected=true")

    except Exception as e:
        logger.error("microsoft_oauth_callback_failed", error=str(e))
        return RedirectResponse(url=f"http://localhost:5174/settings?error=microsoft_auth_failed")


@router.delete("/microsoft/disconnect")
async def microsoft_disconnect(
    user_id: str = Query(..., description="User ID"),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """Disconnect Microsoft account."""
    success = await token_repo.delete_by_user_and_provider(user_id, OAuthProvider.MICROSOFT)
    if success:
        logger.info("microsoft_oauth_disconnected", user_id=user_id)
        return {"message": "Microsoft account disconnected"}
    raise HTTPException(status_code=404, detail="No Microsoft connection found")


@router.get("/microsoft/status", response_model=IntegrationStatusResponse)
async def microsoft_status(
    user_id: str = Query(..., description="User ID"),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """Get Microsoft connection status."""
    token = await token_repo.get_by_user_and_provider(user_id, OAuthProvider.MICROSOFT)

    if token:
        return IntegrationStatusResponse(
            provider="microsoft",
            is_connected=True,
            user_email=token.provider_user_email,
            user_name=token.provider_user_name,
            connected_at=token.created_at.isoformat(),
        )

    return IntegrationStatusResponse(provider="microsoft", is_connected=False)


@router.get("/microsoft/calendar/events", response_model=List[CalendarEventResponse])
async def get_microsoft_calendar_events(
    user_id: str = Query(..., description="User ID"),
    max_results: int = Query(50, description="Max number of events", ge=1, le=100),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """Get Microsoft Calendar events."""
    token = await token_repo.get_by_user_and_provider(user_id, OAuthProvider.MICROSOFT)
    if not token:
        raise HTTPException(status_code=404, detail="Microsoft not connected")

    # Refresh token if needed
    if token.needs_refresh:
        settings = get_settings()
        oauth_client = MicrosoftOAuthClient(settings.microsoft_oauth)
        token = oauth_client.refresh_token(token)
        await token_repo.save(token)

    # Get events
    calendar_client = MicrosoftCalendarClient(token.access_token)
    events = await calendar_client.get_events(user_id, max_results=max_results)

    await token_repo.update_last_used(token.token_id)

    return [
        CalendarEventResponse(
            event_id=str(event.event_id),
            title=event.title,
            description=event.description,
            start_time=event.start_time.isoformat(),
            end_time=event.end_time.isoformat(),
            location=event.location,
            is_all_day=event.is_all_day,
            organizer_email=event.organizer_email,
            attendees=event.attendees,
        )
        for event in events
    ]


@router.get("/microsoft/email/messages", response_model=List[EmailResponse])
async def get_microsoft_email_messages(
    user_id: str = Query(..., description="User ID"),
    max_results: int = Query(20, description="Max number of messages", ge=1, le=50),
    token_repo: OAuthTokenRepository = Depends(get_token_repository),
):
    """Get Outlook email messages."""
    token = await token_repo.get_by_user_and_provider(user_id, OAuthProvider.MICROSOFT)
    if not token:
        raise HTTPException(status_code=404, detail="Microsoft not connected")

    # Refresh token if needed
    if token.needs_refresh:
        settings = get_settings()
        oauth_client = MicrosoftOAuthClient(settings.microsoft_oauth)
        token = oauth_client.refresh_token(token)
        await token_repo.save(token)

    # Get messages
    email_client = MicrosoftEmailClient(token.access_token)
    emails = await email_client.get_messages(user_id, max_results=max_results)

    await token_repo.update_last_used(token.token_id)

    return [
        EmailResponse(
            email_id=str(email.email_id),
            subject=email.subject,
            from_address={"email": email.from_address.email, "name": email.from_address.name},
            snippet=email.snippet,
            sent_at=email.sent_at.isoformat(),
            is_read=email.is_read,
            is_important=email.is_important,
        )
        for email in emails
    ]
