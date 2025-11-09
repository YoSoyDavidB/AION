"""
Obsidian vault synchronization agent.

This agent syncs markdown files from a GitHub repository (Obsidian vault)
to the AION knowledge base automatically.
"""

import base64
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Set
from uuid import UUID

from github import Github
from github.ContentFile import ContentFile
from github.GithubException import GithubException

from src.application.dtos.document_dto import DocumentUploadRequest
from src.application.use_cases.document_use_cases import (
    DeleteDocumentUseCase,
    UploadDocumentUseCase,
)
from src.domain.entities.sync_state import SyncState, SyncStatus
from src.infrastructure.persistence.sync_state_repository import SyncStateRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


class ObsidianSyncAgent:
    """
    Agent for syncing Obsidian vault from GitHub to AION.

    Connects to a GitHub repository and syncs markdown files to the
    document knowledge base. Tracks sync state to avoid duplicates.
    """

    def __init__(
        self,
        github_token: str,
        repo_owner: str,
        repo_name: str,
        branch: str,
        user_id: str,
        upload_use_case: UploadDocumentUseCase,
        delete_use_case: DeleteDocumentUseCase,
        sync_repo: SyncStateRepository | None = None,
        excluded_folders: Set[str] | None = None,
    ):
        """
        Initialize Obsidian sync agent.

        Args:
            github_token: GitHub personal access token
            repo_owner: Repository owner (username or organization)
            repo_name: Repository name
            branch: Branch to sync from (e.g., 'main')
            user_id: User ID for document ownership
            upload_use_case: Use case for uploading documents
            delete_use_case: Use case for deleting documents
            sync_repo: Repository for sync state (creates new if None)
            excluded_folders: Folders to exclude from sync
        """
        self.github = Github(github_token)
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.user_id = user_id
        self.upload_use_case = upload_use_case
        self.delete_use_case = delete_use_case
        self.sync_repo = sync_repo or SyncStateRepository()
        self.excluded_folders = excluded_folders or {
            ".obsidian",
            ".git",
            ".trash",
            "templates",
        }

        try:
            self.repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            logger.info(
                "obsidian_sync_agent_initialized",
                repo=f"{repo_owner}/{repo_name}",
                branch=branch,
            )
        except GithubException as e:
            raise ValueError(f"Failed to access repository: {e}")

    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from sync."""
        path_parts = Path(path).parts
        return any(folder in self.excluded_folders for folder in path_parts)

    def _get_markdown_files_recursive(
        self, contents: List[ContentFile], current_path: str = ""
    ) -> List[ContentFile]:
        """Recursively get all markdown files from repository."""
        markdown_files = []

        for content in contents:
            full_path = f"{current_path}/{content.path}" if current_path else content.path

            # Skip excluded paths
            if self._should_exclude_path(content.path):
                continue

            if content.type == "dir":
                # Recursively get files from subdirectory
                try:
                    sub_contents = self.repo.get_contents(content.path, ref=self.branch)
                    if isinstance(sub_contents, list):
                        markdown_files.extend(
                            self._get_markdown_files_recursive(sub_contents, content.path)
                        )
                except GithubException as e:
                    logger.warning(
                        "failed_to_access_directory", path=content.path, error=str(e)
                    )
            elif content.type == "file" and content.path.endswith(".md"):
                markdown_files.append(content)

        return markdown_files

    def scan_vault(self) -> List[ContentFile]:
        """
        Scan GitHub repository for markdown files.

        Returns:
            List of ContentFile objects representing markdown files
        """
        try:
            contents = self.repo.get_contents("", ref=self.branch)
            if not isinstance(contents, list):
                contents = [contents]

            markdown_files = self._get_markdown_files_recursive(contents)

            logger.info("vault_scanned", file_count=len(markdown_files))
            return markdown_files

        except GithubException as e:
            logger.error("vault_scan_failed", error=str(e))
            raise ValueError(f"Failed to scan repository: {e}")

    def extract_frontmatter_tags(self, content: str) -> List[str]:
        """
        Extract tags from YAML frontmatter.

        Args:
            content: File content

        Returns:
            List of tags
        """
        tags = []

        # Check for YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]

                # Extract tags from frontmatter
                tag_match = re.search(r"^tags:\s*\[?(.*?)\]?$", frontmatter, re.MULTILINE)
                if tag_match:
                    tag_str = tag_match.group(1)
                    # Handle both comma-separated and YAML list formats
                    tags = [
                        tag.strip().strip('"').strip("'")
                        for tag in re.split(r"[,\n]", tag_str)
                        if tag.strip()
                    ]

        # Also extract inline tags (#tag)
        inline_tags = re.findall(r"#(\w+)", content)
        tags.extend(inline_tags)

        # Remove duplicates and obsidian-specific tags
        tags = list(set(tags))
        tags = [tag for tag in tags if not tag.startswith("obsidian")]

        return tags

    def get_file_title(self, content: str, file_path: str) -> str:
        """
        Extract title from markdown file content.

        Tries to get title from:
        1. YAML frontmatter title field
        2. First H1 heading
        3. Filename

        Args:
            content: File content
            file_path: Path to file (for fallback)

        Returns:
            File title
        """
        try:
            # Check frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    title_match = re.search(
                        r"^title:\s*[\"']?(.*?)[\"']?$", frontmatter, re.MULTILINE
                    )
                    if title_match:
                        return title_match.group(1).strip()

            # Check for first H1
            h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if h1_match:
                return h1_match.group(1).strip()

        except Exception as e:
            logger.warning("failed_to_extract_title", file=file_path, error=str(e))

        # Fallback to filename without extension
        return Path(file_path).stem

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA256 hash of file content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def sync_file(self, file: ContentFile) -> SyncState:
        """
        Sync a single file from GitHub to the knowledge base.

        Args:
            file: GitHub ContentFile object

        Returns:
            Updated sync state
        """
        try:
            # Decode file content
            content = base64.b64decode(file.content).decode("utf-8")
            content_hash = self.compute_content_hash(content)

            # Use file path as identifier
            file_path = Path(file.path)

            # Check existing sync state
            existing_state = self.sync_repo.get(file_path)

            # Check if sync is needed
            if existing_state:
                if (
                    existing_state.status == SyncStatus.SYNCED
                    and existing_state.file_hash == content_hash
                ):
                    logger.debug("file_already_synced", file=file.path)
                    return existing_state

            # Extract metadata
            title = self.get_file_title(content, file.path)
            tags = self.extract_frontmatter_tags(content)

            # Create upload request
            request = DocumentUploadRequest(
                user_id=self.user_id,
                title=title,
                tags=tags,
            )

            # Upload document
            logger.info("syncing_file", file=file.path, title=title)
            response = await self.upload_use_case.execute(
                request, content.encode("utf-8"), file.path
            )

            # Get last modified from GitHub
            # Note: GitHub API doesn't provide file mtime, using current time
            last_modified = datetime.utcnow()

            # Create sync state
            state = SyncState(
                file_path=file_path,
                user_id=self.user_id,
                last_modified=last_modified,
                last_synced=datetime.utcnow(),
                status=SyncStatus.SYNCED,
                doc_id=response.doc_id,
                file_hash=content_hash,
            )

            # Save state
            self.sync_repo.save(state)

            logger.info(
                "file_synced",
                file=file.path,
                doc_id=str(response.doc_id),
                chunks=response.num_chunks,
            )

            return state

        except Exception as e:
            logger.error("sync_file_failed", file=file.path, error=str(e))

            # Create failed state
            state = SyncState(
                file_path=Path(file.path),
                user_id=self.user_id,
                last_modified=datetime.utcnow(),
                last_synced=datetime.utcnow(),
                status=SyncStatus.FAILED,
                error_message=str(e),
                file_hash="",
            )

            self.sync_repo.save(state)
            return state

    async def sync_vault(self, force: bool = False) -> dict:
        """
        Sync entire vault from GitHub.

        Args:
            force: Force sync all files even if already synced

        Returns:
            Sync summary with counts
        """
        logger.info(
            "starting_vault_sync",
            repo=f"{self.repo_owner}/{self.repo_name}",
            branch=self.branch,
            force=force,
        )

        # Scan vault
        files = self.scan_vault()

        synced_count = 0
        failed_count = 0
        skipped_count = 0

        # Sync each file
        for file in files:
            try:
                # Decode content to compute hash
                content = base64.b64decode(file.content).decode("utf-8")
                current_hash = self.compute_content_hash(content)

                # Check if sync needed
                if not force:
                    existing_state = self.sync_repo.get(Path(file.path))
                    if (
                        existing_state
                        and existing_state.status == SyncStatus.SYNCED
                        and existing_state.file_hash == current_hash
                    ):
                        skipped_count += 1
                        continue

                # Sync file
                state = await self.sync_file(file)

                if state.status == SyncStatus.SYNCED:
                    synced_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error("file_sync_error", file=file.path, error=str(e))
                failed_count += 1

        summary = {
            "total_files": len(files),
            "synced": synced_count,
            "failed": failed_count,
            "skipped": skipped_count,
        }

        logger.info("vault_sync_completed", **summary)
        return summary

    async def cleanup_deleted_files(self) -> int:
        """
        Remove sync states for files that no longer exist in GitHub repo.

        Returns:
            Number of states cleaned up
        """
        states = self.sync_repo.get_by_user(self.user_id)
        cleaned = 0

        # Get current files in repo
        try:
            current_files = self.scan_vault()
            current_paths = {file.path for file in current_files}
        except Exception as e:
            logger.error("failed_to_scan_repo_for_cleanup", error=str(e))
            return 0

        for state in states:
            if str(state.file_path) not in current_paths:
                logger.info("cleaning_deleted_file", file=str(state.file_path))

                # Delete from knowledge base if doc_id exists
                if state.doc_id:
                    try:
                        await self.delete_use_case.execute(state.doc_id, self.user_id)
                    except Exception as e:
                        logger.error(
                            "failed_to_delete_document",
                            doc_id=str(state.doc_id),
                            error=str(e),
                        )

                # Remove sync state
                self.sync_repo.delete(state.file_path)
                cleaned += 1

        logger.info("cleanup_completed", files_cleaned=cleaned)
        return cleaned
