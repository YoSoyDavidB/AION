"""
Advanced text chunking strategies for optimal RAG performance.

Implements multiple chunking strategies:
- Semantic chunking (topic-based)
- Hierarchical chunking (sections and paragraphs)
- Sentence-aware chunking with overlap
"""

import hashlib
import re
from typing import Literal
from uuid import uuid4

from src.config.settings import get_settings
from src.shared.logging import LoggerMixin


ChunkingStrategy = Literal["semantic", "hierarchical", "sentence_aware", "fixed"]


class AdvancedTextChunker(LoggerMixin):
    """
    Advanced text chunking with multiple strategies.

    Optimizes chunks for retrieval by respecting:
    - Document structure (headers, paragraphs)
    - Semantic boundaries (topic shifts)
    - Sentence integrity
    - Optimal chunk sizes for embedding models
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        strategy: ChunkingStrategy = "sentence_aware",
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target chunk size in characters (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
            strategy: Chunking strategy to use
        """
        super().__init__()
        settings = get_settings()
        self.chunk_size = chunk_size or settings.sync.chunk_size
        self.chunk_overlap = chunk_overlap or settings.sync.chunk_overlap
        self.strategy = strategy

        # Min and max chunk sizes
        self.min_chunk_size = max(100, self.chunk_size // 4)
        self.max_chunk_size = self.chunk_size * 2

        self.logger.info(
            "text_chunker_initialized",
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
            strategy=strategy
        )

    def chunk_text(
        self,
        text: str,
        metadata: dict | None = None,
        strategy: ChunkingStrategy | None = None
    ) -> list[dict]:
        """
        Chunk text using specified strategy.

        Args:
            text: Full text to chunk
            metadata: Optional metadata to include in each chunk
            strategy: Override default strategy

        Returns:
            List of chunk dictionaries with content and metadata
        """
        strategy = strategy or self.strategy

        self.logger.info(
            "chunking_text",
            text_length=len(text),
            strategy=strategy
        )

        if strategy == "semantic":
            chunks = self._chunk_semantic(text, metadata)
        elif strategy == "hierarchical":
            chunks = self._chunk_hierarchical(text, metadata)
        elif strategy == "sentence_aware":
            chunks = self._chunk_sentence_aware(text, metadata)
        else:  # fixed
            chunks = self._chunk_fixed(text, metadata)

        self.logger.info(
            "chunking_complete",
            num_chunks=len(chunks),
            avg_chunk_size=sum(len(c["content"]) for c in chunks) // len(chunks) if chunks else 0
        )

        return chunks

    def _chunk_sentence_aware(
        self,
        text: str,
        metadata: dict | None = None
    ) -> list[dict]:
        """
        Chunk text respecting sentence boundaries.

        This is the most balanced strategy for general use.
        """
        # Split into sentences
        sentences = self._split_sentences(text)

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            # If adding this sentence would exceed chunk size
            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Create chunk from current sentences
                chunk_content = " ".join(current_chunk)
                chunks.append(
                    self._create_chunk(
                        chunk_content,
                        chunk_index,
                        metadata
                    )
                )
                chunk_index += 1

                # Keep overlap sentences for next chunk
                overlap_chars = 0
                overlap_sentences = []

                # Add sentences from the end until we reach overlap size
                for sent in reversed(current_chunk):
                    if overlap_chars + len(sent) <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_chars += len(sent)
                    else:
                        break

                current_chunk = overlap_sentences
                current_size = overlap_chars

            current_chunk.append(sentence)
            current_size += sentence_size

        # Add remaining chunk
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            chunks.append(
                self._create_chunk(
                    chunk_content,
                    chunk_index,
                    metadata
                )
            )

        return chunks

    def _chunk_hierarchical(
        self,
        text: str,
        metadata: dict | None = None
    ) -> list[dict]:
        """
        Chunk text respecting document hierarchy (sections, paragraphs).

        Useful for structured documents like markdown or technical docs.
        """
        # Split by headers first (markdown style)
        sections = self._split_by_headers(text)

        chunks = []
        chunk_index = 0

        for section_header, section_text in sections:
            # Split section into paragraphs
            paragraphs = [p.strip() for p in section_text.split('\n\n') if p.strip()]

            current_chunk = []
            current_size = 0

            # Add header to metadata
            section_metadata = (metadata or {}).copy()
            if section_header:
                section_metadata["section"] = section_header

            for paragraph in paragraphs:
                paragraph_size = len(paragraph)

                # If paragraph alone is too large, split it further
                if paragraph_size > self.max_chunk_size:
                    # If we have accumulated content, save it first
                    if current_chunk:
                        chunk_content = "\n\n".join(current_chunk)
                        chunks.append(
                            self._create_chunk(
                                chunk_content,
                                chunk_index,
                                section_metadata
                            )
                        )
                        chunk_index += 1
                        current_chunk = []
                        current_size = 0

                    # Split large paragraph by sentences
                    sub_chunks = self._chunk_sentence_aware(paragraph, section_metadata)
                    for sub_chunk in sub_chunks:
                        sub_chunk["chunk_index"] = chunk_index
                        chunks.append(sub_chunk)
                        chunk_index += 1

                # If adding paragraph would exceed limit
                elif current_size + paragraph_size > self.chunk_size and current_chunk:
                    chunk_content = "\n\n".join(current_chunk)
                    chunks.append(
                        self._create_chunk(
                            chunk_content,
                            chunk_index,
                            section_metadata
                        )
                    )
                    chunk_index += 1
                    current_chunk = []
                    current_size = 0

                current_chunk.append(paragraph)
                current_size += paragraph_size

            # Add remaining content
            if current_chunk:
                chunk_content = "\n\n".join(current_chunk)
                chunks.append(
                    self._create_chunk(
                        chunk_content,
                        chunk_index,
                        section_metadata
                    )
                )
                chunk_index += 1

        return chunks

    def _chunk_semantic(
        self,
        text: str,
        metadata: dict | None = None
    ) -> list[dict]:
        """
        Chunk text based on semantic similarity.

        Uses simple heuristics for topic changes:
        - Paragraph breaks
        - Transition words
        - Repeated keywords
        """
        # For now, use hierarchical as a good proxy
        # In the future, this could use embeddings to detect topic shifts
        return self._chunk_hierarchical(text, metadata)

    def _chunk_fixed(
        self,
        text: str,
        metadata: dict | None = None
    ) -> list[dict]:
        """
        Simple fixed-size chunking with overlap.

        Fallback strategy, less optimal for retrieval.
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    self._create_chunk(
                        chunk_text,
                        chunk_index,
                        metadata
                    )
                )
                chunk_index += 1

            start = end - self.chunk_overlap

            if end >= len(text):
                break

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences using regex.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Pattern to split on sentence endings
        # Handles periods, exclamation marks, question marks
        # Avoids splitting on abbreviations (e.g., Mr., Dr., etc.)
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+'

        sentences = re.split(pattern, text)

        # Clean up
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _split_by_headers(self, text: str) -> list[tuple[str, str]]:
        """
        Split text by markdown-style headers.

        Args:
            text: Input text

        Returns:
            List of (header, content) tuples
        """
        sections = []

        # Pattern for markdown headers (# Header, ## Subheader, etc.)
        header_pattern = r'^(#{1,6})\s+(.+)$'

        lines = text.split('\n')
        current_header = None
        current_content = []

        for line in lines:
            match = re.match(header_pattern, line)

            if match:
                # Save previous section
                if current_content:
                    sections.append((
                        current_header,
                        '\n'.join(current_content)
                    ))

                # Start new section
                current_header = match.group(2)
                current_content = []
            else:
                current_content.append(line)

        # Add last section
        if current_content:
            sections.append((
                current_header,
                '\n'.join(current_content)
            ))

        # If no headers found, return entire text as single section
        if not sections or (len(sections) == 1 and sections[0][0] is None):
            return [(None, text)]

        return sections

    def _create_chunk(
        self,
        content: str,
        chunk_index: int,
        metadata: dict | None = None
    ) -> dict:
        """
        Create standardized chunk dictionary.

        Args:
            content: Chunk content
            chunk_index: Index of this chunk
            metadata: Optional metadata

        Returns:
            Chunk dictionary
        """
        chunk_data = {
            "content": content,
            "chunk_index": chunk_index,
            "char_count": len(content),
            "chunk_id": str(uuid4()),
            "chunk_hash": hashlib.md5(content.encode()).hexdigest()[:16],
        }

        if metadata:
            chunk_data.update(metadata)

        return chunk_data
