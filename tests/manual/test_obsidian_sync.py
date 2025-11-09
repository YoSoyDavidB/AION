"""
Script to test Obsidian vault synchronization.
Run this script to test the sync agent with sample files.
"""

import asyncio
from pathlib import Path

from src.application.agents.obsidian_sync_agent import ObsidianSyncAgent
from src.application.use_cases.document_use_cases import (
    DeleteDocumentUseCase,
    UploadDocumentUseCase,
)
from src.infrastructure.vector_store.document_repository_impl import (
    QdrantDocumentRepository,
)
from src.shared.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


async def create_sample_vault():
    """Create sample Obsidian vault with test files."""
    vault_path = Path("./obsidian_vault")
    vault_path.mkdir(exist_ok=True)

    # Sample file 1: Meeting notes
    (vault_path / "Meeting with ACME Corp.md").write_text(
        """---
title: Meeting with ACME Corp
tags: [meeting, acme, client]
date: 2025-01-09
---

# Meeting with ACME Corp

## Attendees
- David Buitrago
- John Smith (ACME CEO)
- Sarah Johnson (ACME CTO)

## Discussion Points

### Project Timeline
- Q1: Requirements gathering and design
- Q2: Development phase
- Q3: Testing and QA
- Q4: Deployment and launch

### Technology Stack
We agreed on the following stack:
- Backend: Python + FastAPI
- Frontend: React + TypeScript
- Database: PostgreSQL + Neo4j
- Vector DB: Qdrant

### Next Steps
1. Finalize contract details
2. Set up project repository
3. Schedule kickoff meeting
4. Assign team members

#project #planning
""",
        encoding="utf-8",
    )

    # Sample file 2: Technical notes
    (vault_path / "RAG System Architecture.md").write_text(
        """---
title: RAG System Architecture
tags: [architecture, rag, ai]
---

# RAG System Architecture

## Overview
Our Retrieval-Augmented Generation (RAG) system combines vector search with language models.

## Components

### Vector Database (Qdrant)
- Stores document embeddings
- Fast similarity search
- Collection for documents and memories

### Embedding Model
- Using `text-embedding-3-small` from OpenAI
- 1536 dimensions
- Accessed via OpenRouter

### Document Processing Pipeline
1. **Ingestion**: Accept PDF, TXT, MD files
2. **Chunking**: Split into 500-token chunks with 50-token overlap
3. **Embedding**: Generate vector representations
4. **Storage**: Save to Qdrant with metadata

### Retrieval Process
1. User query embedding
2. Vector similarity search
3. Context assembly
4. LLM generation with Claude 3.5 Sonnet

## Knowledge Graph Integration
Neo4j stores:
- Entities (people, organizations, concepts)
- Relationships between entities
- Properties and metadata

#technical #architecture
""",
        encoding="utf-8",
    )

    # Sample file 3: Daily note
    (vault_path / "2025-01-09.md").write_text(
        """# Daily Note - January 9, 2025

## Tasks
- [x] Review AION architecture
- [x] Implement Obsidian sync agent
- [ ] Test Knowledge Graph integration
- [ ] Update documentation

## Notes
Working on the Obsidian integration today. The sync agent will automatically:
- Scan the vault for markdown files
- Extract metadata from frontmatter
- Upload to the knowledge base
- Track sync state in SQLite

## Ideas
- Could add bidirectional sync later
- Maybe integrate with GitHub for backup
- Consider adding conflict resolution

#daily-note
""",
        encoding="utf-8",
    )

    logger.info("sample_vault_created", path=str(vault_path.absolute()))
    print(f"\n✓ Created sample vault at: {vault_path.absolute()}")
    print(f"  - 3 sample markdown files")
    print(f"  - With YAML frontmatter and tags\n")


async def test_sync():
    """Test the Obsidian sync agent."""
    print("=" * 60)
    print("OBSIDIAN SYNC AGENT TEST")
    print("=" * 60)

    # Create sample vault
    await create_sample_vault()

    # Initialize dependencies
    doc_repo = QdrantDocumentRepository()
    upload_use_case = UploadDocumentUseCase(document_repo=doc_repo)
    delete_use_case = DeleteDocumentUseCase(document_repo=doc_repo)

    # Create sync agent
    agent = ObsidianSyncAgent(
        vault_path="./obsidian_vault",
        user_id="david",
        upload_use_case=upload_use_case,
        delete_use_case=delete_use_case,
    )

    # Run sync
    print("\n📁 Scanning vault...")
    files = agent.scan_vault()
    print(f"   Found {len(files)} markdown files")

    print("\n🔄 Syncing files to knowledge base...")
    summary = await agent.sync_vault()

    print("\n" + "=" * 60)
    print("SYNC SUMMARY")
    print("=" * 60)
    print(f"Total files:  {summary['total_files']}")
    print(f"Synced:       {summary['synced']}")
    print(f"Failed:       {summary['failed']}")
    print(f"Skipped:      {summary['skipped']}")
    print("=" * 60)

    if summary['synced'] > 0:
        print(f"\n✓ Successfully synced {summary['synced']} files to AION!")
        print("  You can now search these documents in the Knowledge Base")

    if summary['failed'] > 0:
        print(f"\n✗ {summary['failed']} files failed to sync")


if __name__ == "__main__":
    asyncio.run(test_sync())
