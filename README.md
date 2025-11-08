# AION - AI Personal Assistant with Long-Term Memory

AION is an intelligent personal assistant that maintains long-term memory across conversations, integrates with your Obsidian knowledge base, and provides contextually rich responses through semantic understanding.

## Features

- **Long-Term Memory**: Remembers key facts, preferences, and conversations across sessions
- **Obsidian Integration**: Seamlessly syncs and searches your Obsidian vault from GitHub
- **Semantic Search**: RAG pipeline for intelligent context retrieval
- **Entity Relationships**: Knowledge graph using Neo4j for advanced reasoning
- **Multi-Agent Architecture**: Specialized agents for memory, retrieval, and synchronization
- **Privacy-First**: All data encrypted at rest, complete user control

## Architecture

AION follows Clean Architecture principles with clear separation of concerns:

```
src/
├── domain/           # Business entities and rules
├── application/      # Use cases and business logic
├── infrastructure/   # External services (Qdrant, Neo4j, OpenRouter)
├── presentation/     # API layer (FastAPI)
└── shared/          # Common utilities
```

### Tech Stack

- **Backend**: FastAPI + LangChain
- **Vector Store**: Qdrant
- **Graph Database**: Neo4j
- **Relational DB**: PostgreSQL
- **LLM Provider**: OpenRouter
- **Embeddings**: OpenRouter (configurable models)
- **Orchestration**: Python + LangChain

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry (for dependency management)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd AION
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Install dependencies (for local development)**
   ```bash
   poetry install
   poetry shell
   ```

5. **Run database migrations**
   ```bash
   poetry run python scripts/init_db.py
   ```

6. **Start the development server**
   ```bash
   poetry run uvicorn src.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Configuration

### Required Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `GITHUB_TOKEN`: GitHub personal access token for Obsidian sync
- `NEO4J_PASSWORD`: Neo4j database password
- `POSTGRES_PASSWORD`: PostgreSQL password

See `.env.example` for complete configuration options.

## Project Structure

```
AION/
├── src/
│   ├── config/              # Application configuration
│   ├── domain/              # Business entities and interfaces
│   │   ├── entities/        # Memory, Document, Conversation
│   │   ├── repositories/    # Repository interfaces
│   │   └── services/        # Domain services
│   ├── application/         # Use cases
│   │   ├── use_cases/       # Business logic
│   │   └── dtos/            # Data transfer objects
│   ├── infrastructure/      # External integrations
│   │   ├── vector_store/    # Qdrant implementation
│   │   ├── graph_db/        # Neo4j implementation
│   │   ├── llm/             # OpenRouter LLM client
│   │   ├── embeddings/      # Embedding service
│   │   └── github_sync/     # Obsidian vault sync
│   ├── presentation/        # API layer
│   │   ├── api/             # FastAPI routes
│   │   └── schemas/         # Pydantic schemas
│   └── shared/              # Utilities and helpers
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
└── docker-compose.yml       # Service orchestration
```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_memory.py
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Lint code
poetry run ruff check src tests

# Type checking
poetry run mypy src
```

### Pre-commit Hooks

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## API Documentation

Once the server is running, visit:

- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Key Endpoints

- `POST /api/v1/chat` - Send message to assistant
- `GET /api/v1/memories` - Retrieve stored memories
- `POST /api/v1/memories` - Create new memory
- `DELETE /api/v1/memories/{id}` - Delete specific memory
- `POST /api/v1/sync` - Trigger Obsidian vault sync
- `GET /api/v1/search` - Search knowledge base

## Agents

### Memory Agent
Extracts and manages long-term memories from conversations.

### Retriever Agent
Performs semantic search across memories and documents.

### Knowledge Sync Agent
Synchronizes and indexes Obsidian vault from GitHub.

### Conversation Agent
Main orchestrator that coordinates other agents.

## Database Schema

### Qdrant Collections

#### `memories`
- Stores semantic embeddings of user memories
- Fields: memory_id, short_text, type, timestamp, relevance_score, embedding

#### `kb_documents`
- Stores chunked Obsidian documents
- Fields: doc_id, chunk_id, path, title, heading, tags, embedding

### Neo4j Graph
- Entities: Person, Project, Concept, Document
- Relationships: RELATED_TO, MENTIONED_IN, PART_OF

## Security

- All sensitive data encrypted at rest
- API key authentication required
- Rate limiting enabled by default
- User data isolation
- Complete data deletion on request

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

- Built with FastAPI and LangChain
- Powered by OpenRouter for flexible LLM access
- Vector storage by Qdrant
- Graph database by Neo4j

---

**Author**: David Buitrago
**Version**: 1.0.0
**Last Updated**: November 2025
