"""
Calendar Event entity for storing calendar events from Google and Microsoft.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.domain.entities.oauth_token import OAuthProvider


class CalendarEvent(BaseModel):
    """Calendar event entity."""

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    user_id: str = Field(..., description="User ID who owns this event")
    provider: OAuthProvider = Field(..., description="Calendar provider")
    provider_event_id: str = Field(..., description="Event ID from provider")
    calendar_id: str = Field(..., description="Calendar ID from provider")

    # Event details
    title: str = Field(..., description="Event title/summary")
    description: str | None = Field(default=None, description="Event description")
    location: str | None = Field(default=None, description="Event location")

    # Time details
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    is_all_day: bool = Field(default=False, description="Is an all-day event")
    timezone: str | None = Field(default=None, description="Event timezone")

    # Attendees and organization
    organizer_email: str | None = Field(default=None, description="Event organizer email")
    organizer_name: str | None = Field(default=None, description="Event organizer name")
    attendees: list[dict] = Field(default_factory=list, description="List of attendees")

    # Status and visibility
    status: str | None = Field(default=None, description="Event status (confirmed, tentative, cancelled)")
    is_recurring: bool = Field(default=False, description="Is a recurring event")
    recurrence_rule: str | None = Field(default=None, description="Recurrence rule (RRULE)")

    # Meeting details
    meeting_url: str | None = Field(default=None, description="Video conference URL")
    conference_data: dict | None = Field(default=None, description="Conference/meeting data")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    synced_at: datetime = Field(default_factory=datetime.utcnow, description="Last sync timestamp")

    # Raw data from provider for reference
    raw_data: dict | None = Field(default=None, description="Raw event data from provider")

    @property
    def is_upcoming(self) -> bool:
        """Check if event is upcoming (starts in the future)."""
        return self.start_time > datetime.utcnow()

    @property
    def is_ongoing(self) -> bool:
        """Check if event is currently happening."""
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time

    @property
    def is_past(self) -> bool:
        """Check if event has ended."""
        return self.end_time < datetime.utcnow()

    @property
    def duration_minutes(self) -> int:
        """Get event duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    class Config:
        """Pydantic config."""
        from_attributes = True
