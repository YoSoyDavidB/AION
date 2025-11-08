# AION Project Structure

Complete overview of the AION codebase organization.

## Project Statistics

- **Total Python Files**: 54
- **Lines of Code**: ~5,000+
- **Architecture**: Clean Architecture (4 layers)
- **Test Coverage Target**: >80%

## Directory Structure

```
AION/
├── src/                                    # Source code
│   ├── config/                            # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py                    # Pydantic Settings (grouped configs)
│   │
│   ├── domain/                            # Domain layer (pure business logic)
│   │   ├── entities/                      # Domain entities
│   │   │   ├── __init__.py
│   │   │   ├── memory.py                  # Memory entity + types
│   │   │   ├── document.py                # Document entity
│   │   │   ├── conversation.py            # Conversation + Message entities
│   │   │   └── graph_entity.py            # Graph entities + relationships
│   │   ├── repositories/                  # Repository interfaces
│   │   │   ├── __init__.py
│   │   │   ├── memory_repository.py
│   │   │   ├── document_repository.py
│   │   │   ├── conversation_repository.py
│   │   │   └── graph_repository.py
│   │   └── services/                      # Domain services (placeholder)
│   │
│   ├── application/                       # Application layer (use cases)
│   │   ├── dtos/                          # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── chat_dto.py                # ChatRequest, ChatResponse
│   │   │   ├── memory_dto.py              # Memory DTOs
│   │   │   └── rag_dto.py                 # RAG DTOs
│   │   └── use_cases/                     # Business logic orchestration
│   │       ├── __init__.py
│   │       ├── memory_use_cases.py        # Memory CRUD + Search
│   │       ├── rag_use_case.py            # RAG pipeline
│   │       └── chat_use_case.py           # Chat orchestration
│   │
│   ├── infrastructure/                    # Infrastructure layer (external services)
│   │   ├── llm/                           # Language Model services
│   │   │   ├── __init__.py
│   │   │   ├── openrouter_client.py       # HTTP client for OpenRouter
│   │   │   └── llm_service.py             # High-level LLM operations
│   │   ├── embeddings/                    # Embedding services
│   │   │   ├── __init__.py
│   │   │   └── embedding_service.py       # Text-to-vector conversion
│   │   ├── vector_store/                  # Qdrant implementations
│   │   │   ├── __init__.py
│   │   │   ├── qdrant_client.py           # Qdrant wrapper
│   │   │   ├── memory_repository_impl.py  # Memory storage
│   │   │   └── document_repository_impl.py # Document storage
│   │   ├── graph_db/                      # Neo4j implementations
│   │   │   ├── __init__.py
│   │   │   ├── neo4j_client.py            # Neo4j wrapper
│   │   │   └── graph_repository_impl.py   # Graph operations
│   │   ├── database/                      # PostgreSQL (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   ├── models.py                  # SQLAlchemy models
│   │   │   ├── connection.py              # Session management
│   │   │   └── conversation_repository_impl.py
│   │   └── github_sync/                   # GitHub sync (placeholder)
│   │
│   ├── presentation/                      # Presentation layer (API)
│   │   ├── api/                           # FastAPI application
│   │   │   ├── routes/                    # API endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health.py              # Health checks
│   │   │   │   ├── chat.py                # Chat endpoints
│   │   │   │   └── memory.py              # Memory endpoints
│   │   │   └── dependencies.py            # Dependency injection
│   │   └── schemas/                       # Pydantic schemas (placeholder)
│   │
│   ├── shared/                            # Shared utilities
│   │   ├── __init__.py
│   │   ├── logging.py                     # Structured logging (structlog)
│   │   └── exceptions.py                  # Custom exceptions
│   │
│   └── main.py                            # FastAPI application entry point
│
├── tests/                                 # Test suite
│   ├── unit/                              # Unit tests
│   ├── integration/                       # Integration tests
│   └── e2e/                               # End-to-end tests
│
├── scripts/                               # Utility scripts
│   └── init_db.py                         # Database initialization
│
├── docs/                                  # Documentation
│   ├── SETUP.md                           # Setup guide
│   ├── ARCHITECTURE.md                    # Architecture documentation
│   └── PROJECT_STRUCTURE.md               # This file
│
├── logs/                                  # Application logs (gitignored)
├── obsidian_vault/                        # Synced Obsidian vault (gitignored)
├── qdrant_storage/                        # Qdrant data (gitignored)
├── neo4j_data/                            # Neo4j data (gitignored)
├── postgres_data/                         # PostgreSQL data (gitignored)
│
├── .env                                   # Environment variables (gitignored)
├── .env.example                           # Environment template
├── .gitignore                             # Git ignore rules
├── docker-compose.yml                     # Docker services
├── Dockerfile                             # API container
├── Makefile                               # Development commands
├── pyproject.toml                         # Poetry configuration
├── poetry.lock                            # Dependency lock file
├── README.md                              # Project README
└── Functional and Technical Specification Document.md
```

## Key Files by Purpose

### Configuration
- `src/config/settings.py` - Centralized configuration with Pydantic
- `.env` - Environment variables
- `pyproject.toml` - Project metadata and dependencies

### Domain Layer (Business Logic)
**Entities:**
- `src/domain/entities/memory.py` - Memory entity with decay/boost logic
- `src/domain/entities/document.py` - Document chunk entity
- `src/domain/entities/conversation.py` - Conversation and Message entities
- `src/domain/entities/graph_entity.py` - Graph entities and relationships

**Interfaces:**
- `src/domain/repositories/*.py` - Repository contracts (no implementations)

### Application Layer (Use Cases)
- `src/application/use_cases/memory_use_cases.py` - Memory CRUD operations
- `src/application/use_cases/rag_use_case.py` - RAG pipeline orchestration
- `src/application/use_cases/chat_use_case.py` - Chat conversation flow
- `src/application/dtos/*.py` - Request/Response DTOs

### Infrastructure Layer (External Services)
**Vector Store:**
- `src/infrastructure/vector_store/qdrant_client.py` - Qdrant operations
- `src/infrastructure/vector_store/memory_repository_impl.py` - Memory storage
- `src/infrastructure/vector_store/document_repository_impl.py` - Document storage

**Graph Database:**
- `src/infrastructure/graph_db/neo4j_client.py` - Neo4j operations
- `src/infrastructure/graph_db/graph_repository_impl.py` - Entity/relationship storage

**Relational Database:**
- `src/infrastructure/database/models.py` - SQLAlchemy models
- `src/infrastructure/database/connection.py` - Session management
- `src/infrastructure/database/conversation_repository_impl.py` - Conversation storage

**LLM Services:**
- `src/infrastructure/llm/openrouter_client.py` - OpenRouter HTTP client
- `src/infrastructure/llm/llm_service.py` - LLM operations (chat, extraction, etc.)
- `src/infrastructure/embeddings/embedding_service.py` - Embedding generation

### Presentation Layer (API)
- `src/main.py` - FastAPI app initialization
- `src/presentation/api/routes/health.py` - Health check endpoints
- `src/presentation/api/routes/chat.py` - Chat API endpoints
- `src/presentation/api/routes/memory.py` - Memory API endpoints
- `src/presentation/api/dependencies.py` - Dependency injection setup

### Utilities
- `src/shared/logging.py` - Structured logging with structlog
- `src/shared/exceptions.py` - Custom exception hierarchy

### DevOps
- `docker-compose.yml` - Multi-service Docker setup
- `Dockerfile` - API container definition
- `Makefile` - Development commands
- `scripts/init_db.py` - Database initialization

## Module Dependencies

```
┌──────────────────┐
│   Presentation   │ ─┐
└──────────────────┘  │
                      │
┌──────────────────┐  │
│   Application    │ ◄┘
└──────────────────┘
         │
         ▼
┌──────────────────┐
│     Domain       │  ← No dependencies on other layers
└──────────────────┘
         ▲
         │
┌──────────────────┐
│ Infrastructure   │
└──────────────────┘
```

**Dependency Rules:**
- **Domain** has no dependencies (pure Python)
- **Application** depends only on Domain
- **Infrastructure** implements Domain interfaces
- **Presentation** depends on Application and Infrastructure (via DI)

## Code Organization Principles

### 1. Separation of Concerns
Each layer has a single, well-defined responsibility.

### 2. Dependency Inversion
High-level modules don't depend on low-level modules. Both depend on abstractions.

### 3. Interface Segregation
Repository interfaces are specific to each entity type.

### 4. Single Responsibility
Each class/module has one reason to change.

### 5. Open/Closed
Open for extension, closed for modification.

## Import Patterns

```python
# Domain layer - no external imports
from src.domain.entities.memory import Memory
from src.domain.repositories.memory_repository import IMemoryRepository

# Application layer - imports from domain
from src.domain.entities.memory import Memory
from src.application.dtos.memory_dto import MemoryResponse

# Infrastructure - imports from domain (implements interfaces)
from src.domain.repositories.memory_repository import IMemoryRepository
from src.infrastructure.vector_store.qdrant_client import QdrantClient

# Presentation - imports from application
from src.application.use_cases.memory_use_cases import CreateMemoryUseCase
from src.application.dtos.memory_dto import MemoryCreateRequest
```

## Testing Structure

```
tests/
├── unit/                          # Fast, isolated tests
│   ├── domain/                    # Test entities
│   ├── application/               # Test use cases (mock repos)
│   └── infrastructure/            # Test individual services
├── integration/                   # Test with real services
│   ├── test_qdrant_repository.py
│   ├── test_neo4j_repository.py
│   └── test_postgres_repository.py
└── e2e/                          # End-to-end API tests
    ├── test_chat_flow.py
    └── test_memory_flow.py
```

## Configuration Files

- `.env` - Local environment variables
- `.env.example` - Template for environment variables
- `pyproject.toml` - Poetry dependencies and tool configuration
- `docker-compose.yml` - Multi-container Docker setup
- `Dockerfile` - API service container
- `Makefile` - Development workflow commands
- `.gitignore` - Files to ignore in git

## Next Steps for Development

1. **Implement GitHub Sync Agent** - Complete Obsidian vault synchronization
2. **Add Tests** - Write unit, integration, and e2e tests
3. **Implement Authentication** - Add JWT-based user authentication
4. **Add Caching** - Implement Redis for frequent queries
5. **Monitoring** - Add Prometheus metrics and health checks
6. **Documentation** - Generate API documentation
7. **CI/CD** - Set up GitHub Actions for testing and deployment

---

**Last Updated**: November 2025
