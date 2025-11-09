"""
Sync state entity for tracking synchronized files.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID


class SyncStatus(str, Enum):
    """Status of file synchronization."""

    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    DELETED = "deleted"


@dataclass
class SyncState:
    """
    Represents the synchronization state of a file.

    Attributes:
        file_path: Absolute path to the synced file
        last_modified: Last modification time of the file
        last_synced: When the file was last synced
        status: Current sync status
        doc_id: Document ID in the system (if synced)
        user_id: User who owns this sync
        error_message: Error message if sync failed
        file_hash: Hash of file content for change detection
    """

    file_path: Path
    last_modified: datetime
    last_synced: datetime | None
    status: SyncStatus
    user_id: str
    doc_id: UUID | None = None
    error_message: str | None = None
    file_hash: str | None = None

    @property
    def needs_update(self) -> bool:
        """Check if file needs to be re-synced."""
        if self.status == SyncStatus.FAILED:
            return True
        if self.last_synced is None:
            return True
        return self.last_modified > self.last_synced

    @property
    def relative_path(self) -> str:
        """Get relative path from vault root."""
        return str(self.file_path)
