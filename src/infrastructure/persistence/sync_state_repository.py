"""
SQLite-based repository for sync state persistence.
"""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import UUID

from src.domain.entities.sync_state import SyncState, SyncStatus
from src.shared.logging import get_logger

logger = get_logger(__name__)


class SyncStateRepository:
    """Repository for managing file sync state using SQLite."""

    def __init__(self, db_path: str = "data/sync_state.db"):
        """
        Initialize sync state repository.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    file_path TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    last_synced TEXT,
                    status TEXT NOT NULL,
                    doc_id TEXT,
                    error_message TEXT,
                    file_hash TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON sync_state(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON sync_state(status)
            """)
            conn.commit()

    def save(self, state: SyncState) -> None:
        """Save or update sync state."""
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO sync_state (
                    file_path, user_id, last_modified, last_synced,
                    status, doc_id, error_message, file_hash,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    last_modified = excluded.last_modified,
                    last_synced = excluded.last_synced,
                    status = excluded.status,
                    doc_id = excluded.doc_id,
                    error_message = excluded.error_message,
                    file_hash = excluded.file_hash,
                    updated_at = excluded.updated_at
                """,
                (
                    str(state.file_path),
                    state.user_id,
                    state.last_modified.isoformat(),
                    state.last_synced.isoformat() if state.last_synced else None,
                    state.status.value,
                    str(state.doc_id) if state.doc_id else None,
                    state.error_message,
                    state.file_hash,
                    now,
                    now,
                ),
            )
            conn.commit()

    def get(self, file_path: Path) -> SyncState | None:
        """Get sync state for a file."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM sync_state WHERE file_path = ?
                """,
                (str(file_path),),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return SyncState(
                file_path=Path(row["file_path"]),
                user_id=row["user_id"],
                last_modified=datetime.fromisoformat(row["last_modified"]),
                last_synced=datetime.fromisoformat(row["last_synced"])
                if row["last_synced"]
                else None,
                status=SyncStatus(row["status"]),
                doc_id=UUID(row["doc_id"]) if row["doc_id"] else None,
                error_message=row["error_message"],
                file_hash=row["file_hash"],
            )

    def get_by_user(self, user_id: str) -> List[SyncState]:
        """Get all sync states for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM sync_state WHERE user_id = ?
                ORDER BY last_modified DESC
                """,
                (user_id,),
            )

            states = []
            for row in cursor.fetchall():
                states.append(
                    SyncState(
                        file_path=Path(row["file_path"]),
                        user_id=row["user_id"],
                        last_modified=datetime.fromisoformat(row["last_modified"]),
                        last_synced=datetime.fromisoformat(row["last_synced"])
                        if row["last_synced"]
                        else None,
                        status=SyncStatus(row["status"]),
                        doc_id=UUID(row["doc_id"]) if row["doc_id"] else None,
                        error_message=row["error_message"],
                        file_hash=row["file_hash"],
                    )
                )

            return states

    def get_pending(self, user_id: str) -> List[SyncState]:
        """Get all pending or failed sync states for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM sync_state
                WHERE user_id = ? AND (status = ? OR status = ?)
                ORDER BY last_modified ASC
                """,
                (user_id, SyncStatus.PENDING.value, SyncStatus.FAILED.value),
            )

            states = []
            for row in cursor.fetchall():
                states.append(
                    SyncState(
                        file_path=Path(row["file_path"]),
                        user_id=row["user_id"],
                        last_modified=datetime.fromisoformat(row["last_modified"]),
                        last_synced=datetime.fromisoformat(row["last_synced"])
                        if row["last_synced"]
                        else None,
                        status=SyncStatus(row["status"]),
                        doc_id=UUID(row["doc_id"]) if row["doc_id"] else None,
                        error_message=row["error_message"],
                        file_hash=row["file_hash"],
                    )
                )

            return states

    def delete(self, file_path: Path) -> None:
        """Delete sync state for a file."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                DELETE FROM sync_state WHERE file_path = ?
                """,
                (str(file_path),),
            )
            conn.commit()

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
