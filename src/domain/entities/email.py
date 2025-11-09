"""
Email entity for storing emails from Gmail and Outlook.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.domain.entities.oauth_token import OAuthProvider


class EmailAddress(BaseModel):
    """Email address with optional name."""

    email: str = Field(..., description="Email address")
    name: str | None = Field(default=None, description="Display name")


class Email(BaseModel):
    """Email entity."""

    email_id: UUID = Field(default_factory=uuid4, description="Unique email identifier")
    user_id: str = Field(..., description="User ID who owns this email")
    provider: OAuthProvider = Field(..., description="Email provider")
    provider_email_id: str = Field(..., description="Email ID from provider")
    thread_id: str | None = Field(default=None, description="Thread/conversation ID")

    # Email headers
    from_address: EmailAddress = Field(..., description="Sender email address")
    to_addresses: list[EmailAddress] = Field(default_factory=list, description="Recipient email addresses")
    cc_addresses: list[EmailAddress] = Field(default_factory=list, description="CC email addresses")
    bcc_addresses: list[EmailAddress] = Field(default_factory=list, description="BCC email addresses")
    reply_to: EmailAddress | None = Field(default=None, description="Reply-to email address")

    # Email content
    subject: str = Field(..., description="Email subject")
    body_text: str | None = Field(default=None, description="Plain text body")
    body_html: str | None = Field(default=None, description="HTML body")
    snippet: str | None = Field(default=None, description="Email snippet/preview")

    # Metadata
    sent_at: datetime = Field(..., description="Email sent timestamp")
    received_at: datetime | None = Field(default=None, description="Email received timestamp")
    is_read: bool = Field(default=False, description="Has been read")
    is_important: bool = Field(default=False, description="Marked as important/priority")
    is_starred: bool = Field(default=False, description="Starred/flagged")
    labels: list[str] = Field(default_factory=list, description="Email labels/categories")
    folder: str | None = Field(default=None, description="Email folder (Inbox, Sent, etc.)")

    # Attachments
    has_attachments: bool = Field(default=False, description="Has attachments")
    attachments: list[dict] = Field(default_factory=list, description="Attachment metadata")

    # Sync metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    synced_at: datetime = Field(default_factory=datetime.utcnow, description="Last sync timestamp")

    # Raw data from provider for reference
    raw_data: dict | None = Field(default=None, description="Raw email data from provider")

    @property
    def is_recent(self) -> bool:
        """Check if email was received in the last 24 hours."""
        from datetime import timedelta
        threshold = datetime.utcnow() - timedelta(hours=24)
        return (self.received_at or self.sent_at) > threshold

    @property
    def all_recipients(self) -> list[EmailAddress]:
        """Get all recipients (to + cc + bcc)."""
        return self.to_addresses + self.cc_addresses + self.bcc_addresses

    class Config:
        """Pydantic config."""
        from_attributes = True
