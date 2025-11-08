"""
Document processing utilities for extracting text from various formats.
"""

import hashlib
import re
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from src.config.settings import get_settings
from src.shared.exceptions import ValidationError
from src.shared.logging import LoggerMixin


class DocumentProcessor(LoggerMixin):
    """
    Processes documents and extracts text content.

    Supports: PDF, TXT, MD, and other text formats.
    """

    def __init__(self) -> None:
        """Initialize document processor."""
        self.settings = get_settings()
        self.chunk_size = self.settings.sync.chunk_size
        self.chunk_overlap = self.settings.sync.chunk_overlap

    def extract_text(self, file_content: bytes, filename: str) -> str:
        """
        Extract text from a file based on its extension.

        Args:
            file_content: Raw file bytes
            filename: Original filename with extension

        Returns:
            Extracted text content

        Raises:
            ValidationError: If file type is not supported
        """
        extension = Path(filename).suffix.lower()

        if extension == ".pdf":
            return self._extract_from_pdf(file_content)
        elif extension in [".txt", ".md", ".markdown"]:
            return self._extract_from_text(file_content)
        else:
            raise ValidationError(
                f"Unsupported file type: {extension}",
                details={"filename": filename, "extension": extension},
            )

    def _extract_from_pdf(self, file_content: bytes) -> str:
        """
        Extract text from PDF file.

        Args:
            file_content: PDF file bytes

        Returns:
            Extracted text
        """
        try:
            import io

            # Try PyPDF2 first
            try:
                from PyPDF2 import PdfReader

                pdf_file = io.BytesIO(file_content)
                reader = PdfReader(pdf_file)

                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                full_text = "\n\n".join(text_parts)
                self.logger.info(
                    "pdf_text_extracted",
                    num_pages=len(reader.pages),
                    text_length=len(full_text),
                )
                return full_text

            except ImportError:
                self.logger.warning("pypdf2_not_installed", fallback="basic_extraction")
                # Fallback: basic text extraction (won't work well but prevents crash)
                return file_content.decode("utf-8", errors="ignore")

        except Exception as e:
            self.logger.error("pdf_extraction_failed", error=str(e))
            raise ValidationError(
                f"Failed to extract text from PDF: {str(e)}",
                details={"error": str(e)},
            ) from e

    def _extract_from_text(self, file_content: bytes) -> str:
        """
        Extract text from plain text or markdown file.

        Args:
            file_content: Text file bytes

        Returns:
            Decoded text
        """
        try:
            # Try UTF-8 first, then fall back to latin-1
            try:
                text = file_content.decode("utf-8")
            except UnicodeDecodeError:
                text = file_content.decode("latin-1")

            self.logger.info("text_extracted", text_length=len(text))
            return text

        except Exception as e:
            self.logger.error("text_extraction_failed", error=str(e))
            raise ValidationError(
                f"Failed to extract text: {str(e)}",
                details={"error": str(e)},
            ) from e

    def chunk_text(self, text: str, metadata: dict | None = None) -> list[dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full text to chunk
            metadata: Optional metadata to include in each chunk

        Returns:
            List of chunk dictionaries with content and metadata
        """
        # Clean text
        text = self._clean_text(text)

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # If not the last chunk, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                search_start = max(start, end - 100)
                search_text = text[search_start:end + 100]

                # Find the last sentence ending
                sentence_ends = [
                    m.end() + search_start
                    for m in re.finditer(r'[.!?]\s+', search_text)
                ]

                if sentence_ends:
                    # Use the last sentence ending before our target
                    suitable_ends = [pos for pos in sentence_ends if pos <= end + 50]
                    if suitable_ends:
                        end = suitable_ends[-1]

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_data = {
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                }

                if metadata:
                    chunk_data.update(metadata)

                # Generate unique chunk ID as UUID
                chunk_data["chunk_id"] = str(uuid4())
                # Also store content hash for deduplication
                chunk_data["chunk_hash"] = hashlib.md5(chunk_text.encode()).hexdigest()[:16]

                chunks.append(chunk_data)
                chunk_index += 1

            # Move start position with overlap
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if end >= len(text):
                break

        self.logger.info(
            "text_chunked",
            num_chunks=len(chunks),
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
        )

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove multiple consecutive spaces
        text = re.sub(r' {2,}', ' ', text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    def get_file_hash(self, file_content: bytes) -> str:
        """
        Generate hash for file content.

        Args:
            file_content: File bytes

        Returns:
            MD5 hash of content
        """
        return hashlib.md5(file_content).hexdigest()
