## AION Architecture Documentation

### Overview

AION follows **Clean Architecture** principles with clear separation of concerns across four main layers:

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                    │
│              (FastAPI, API Routes, DTOs)                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Application Layer                      │
│           (Use Cases, Business Logic)                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   Domain Layer                          │
│        (Entities, Repository Interfaces)                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│               Infrastructure Layer                      │
│  (Qdrant, Neo4j, PostgreSQL, OpenRouter)               │
└─────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. Domain Layer (`src/domain/`)
**Pure business logic, no external dependencies**

**Entities:**
- `Memory`: Long-term memory items with metadata
- `Document`: Knowledge base document chunks
- `Conversation`: Chat conversation and messages
- `GraphEntity`: Knowledge graph entities and relationships
- `Tool`: Base class for function calling tools (BaseTool, ToolParameter)

**Repository Interfaces:**
- `IMemoryRepository`: Contract for memory storage
- `IDocumentRepository`: Contract for document storage
- `IConversationRepository`: Contract for conversation storage
- `IGraphRepository`: Contract for graph operations

**Key Principle:** Domain entities know nothing about databases, APIs, or external services.

#### 2. Application Layer (`src/application/`)
**Business logic orchestration**

**Use Cases:**
- `ChatUseCase`: Orchestrates full conversation flow
- `RAGUseCase`: Retrieval-Augmented Generation pipeline
- `CreateMemoryUseCase`: Memory creation with embeddings
- `SearchMemoriesUseCase`: Semantic memory search
- `ConsolidateMemoriesUseCase`: Memory maintenance

**DTOs:**
- `ChatRequest/ChatResponse`
- `MemoryCreateRequest/MemoryResponse`
- `RAGRequest/RAGResponse`

**Key Principle:** Use cases coordinate between repositories and services to implement business requirements.

#### 3. Infrastructure Layer (`src/infrastructure/`)
**External service implementations**

**Vector Store (Qdrant):**
- `QdrantClientWrapper`: Low-level Qdrant operations
- `QdrantMemoryRepository`: Memory storage implementation
- `QdrantDocumentRepository`: Document storage implementation

**Graph Database (Neo4j):**
- `Neo4jClientWrapper`: Graph database client
- `Neo4jGraphRepository`: Graph operations implementation

**Relational Database (PostgreSQL):**
- `DatabaseManager`: SQLAlchemy async session management
- `PostgreSQLConversationRepository`: Conversation storage

**LLM & Embeddings (OpenRouter):**
- `OpenRouterClient`: HTTP client with retry logic
- `LLMService`: High-level LLM operations (with function calling support)
- `EmbeddingService`: Text-to-vector conversion

**Function Calling Tools:**
- `ToolRegistry`: Manages tool registration and execution
- `CalculatorTool`: Mathematical calculations
- `WebSearchTool`: DuckDuckGo web search (no API key required)
- `CodeExecutorTool`: Sandboxed Python code execution
- `KnowledgeBaseTool`: Search memories and documents

#### 4. Presentation Layer (`src/presentation/`)
**HTTP API and user interface**

**API Routes:**
- `/api/v1/health`: Health checks
- `/api/v1/chat`: Conversation endpoint
- `/api/v1/memories`: Memory CRUD operations

**Dependencies:**
- Dependency injection for use cases
- Request/response validation
- Error handling

### Data Flow

#### Chat Request Flow

```
1. User → POST /api/v1/chat (with use_tools=true)
2. ChatRequest (DTO) validated
3. ChatUseCase.execute_quick()
   ├─→ Get/Create Conversation (PostgreSQL)
   ├─→ RAGUseCase.execute()
   │   ├─→ Generate query embedding (OpenRouter)
   │   ├─→ Search memories (Qdrant)
   │   ├─→ Search documents (Qdrant)
   │   ├─→ Search knowledge graph (Neo4j)
   │   ├─→ Assemble context
   │   └─→ LLMService.chat_with_tools() [Agentic Loop]
   │       ├─→ Send request with tools (OpenRouter)
   │       ├─→ If tool call requested:
   │       │   ├─→ ToolRegistry.execute_tool()
   │       │   ├─→ Return tool result to LLM
   │       │   └─→ Repeat (max 5 iterations)
   │       └─→ Final answer + tools_used
   ├─→ Update conversation (PostgreSQL)
   └─→ Background: Extract memories & entities
4. ChatResponse (DTO) returned with tools_used
5. User ← JSON response
```

#### Function Calling Flow (Agentic Loop)

```
1. LLMService.chat_with_tools() called
2. Send request with tool definitions to LLM
3. LLM decides to use tool (e.g., "calculator")
4. ToolRegistry.execute_tool("calculator", {"expression": "156 * 78"})
5. Tool executes → returns result (12168)
6. Result sent back to LLM
7. LLM uses result to formulate final answer
8. Response returned with tools_used metadata
```

#### Memory Creation Flow

```
1. User → POST /api/v1/memories
2. MemoryCreateRequest validated
3. CreateMemoryUseCase.execute()
   ├─→ Generate embedding (OpenRouter)
   ├─→ Create Memory entity
   └─→ Store in Qdrant
4. MemoryResponse returned
```

### Database Schemas

#### Qdrant Collections

**memories:**
```python
{
    "memory_id": UUID,
    "short_text": str,
    "memory_type": enum,
    "timestamp": datetime,
    "last_referenced_at": datetime,
    "relevance_score": float,
    "num_times_referenced": int,
    "sensitivity": enum,
    "embedding": vector[1536],
    "source": str,
    "metadata": dict
}
```

**kb_documents:**
```python
{
    "doc_id": UUID,
    "chunk_id": str,
    "path": str,
    "title": str,
    "content": str,
    "heading": str,
    "tags": list[str],
    "created_at": datetime,
    "updated_at": datetime,
    "language": str,
    "embedding": vector[1536],
    "source_type": str,
    "metadata": dict
}
```

#### Neo4j Graph Schema

**Nodes:**
- `Entity`: Generic entity node
  - Properties: entity_id, name, entity_type, description, properties, created_at, updated_at

**Relationships:**
- `RELATED_TO`
- `MENTIONED_IN`
- `PART_OF`
- `CREATED_BY`
- `WORKS_ON`

**Constraints:**
- Unique: `Entity.entity_id`
- Index: `Entity.name`, `Entity.entity_type`

#### PostgreSQL Tables

**conversations:**
```sql
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    summary TEXT,
    metadata JSONB,
    total_tokens INTEGER
);
```

**messages:**
```sql
CREATE TABLE messages (
    message_id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(conversation_id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,
    token_count INTEGER
);
```

### Key Design Patterns

#### 1. Repository Pattern
Abstract data access behind interfaces, allowing easy swapping of storage backends.

#### 2. Dependency Injection
Use FastAPI's dependency injection for loose coupling and testability.

#### 3. Use Case Pattern
Each business operation is encapsulated in a dedicated use case class.

#### 4. DTO Pattern
Separate internal domain models from external API contracts.

#### 5. Factory Pattern
Centralized creation of complex objects (clients, services).

### Configuration Management

All configuration is centralized in `src/config/settings.py` using Pydantic Settings:

- **Type-safe** configuration
- **Environment variables** support
- **Validation** on startup
- **Grouped by concern** (API, Database, Security, etc.)

### Error Handling

**Exception Hierarchy:**
```
AIONException (base)
├── DomainException
│   ├── EntityNotFoundError
│   └── EntityValidationError
├── ApplicationException
│   ├── UseCaseExecutionError
│   └── InvalidInputError
├── InfrastructureException
│   ├── VectorStoreError
│   ├── GraphDatabaseError
│   ├── LLMServiceError
│   └── EmbeddingServiceError
└── PresentationException
    ├── AuthenticationError
    └── APIValidationError
```

All exceptions are mapped to appropriate HTTP status codes via `get_http_status_code()`.

### Logging

**Structured logging** with `structlog`:
- JSON output in production
- Console-friendly in development
- Contextual information (request_id, user_id, etc.)
- Centralized in `src/shared/logging.py`

### Testing Strategy

```
tests/
├── unit/           # Pure unit tests (domain, use cases)
├── integration/    # Integration tests (repositories, services)
└── e2e/           # End-to-end API tests
```

**Test Principles:**
- Mock external services in unit tests
- Use test containers for integration tests
- Measure code coverage (target: >80%)

### Security Considerations

1. **Data Encryption**: Sensitive data encrypted at rest
2. **API Authentication**: JWT tokens for user authentication
3. **Rate Limiting**: Prevent abuse (configurable)
4. **Input Validation**: Pydantic schemas validate all inputs
5. **SQL Injection**: SQLAlchemy ORM prevents SQL injection
6. **CORS**: Configurable allowed origins
7. **Secrets Management**: Environment variables for credentials

### Scalability Considerations

**Current Architecture:**
- Single instance deployment
- Suitable for 1-100 concurrent users
- Handles ~50K documents and ~10K memories

**Future Scalability:**
- **Horizontal Scaling**: Add API replicas behind load balancer
- **Database Sharding**: Shard Qdrant by user_id
- **Caching**: Add Redis for frequently accessed data
- **Async Queue**: Use Celery for long-running tasks
- **CDN**: Serve static content from CDN

### Monitoring & Observability

**Recommended Tools:**
- **Logging**: Structured logs → ELK Stack
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry → Jaeger
- **Alerting**: PagerDuty / Opsgenie

**Key Metrics to Monitor:**
- Request latency (p50, p95, p99)
- Error rates by endpoint
- Database query performance
- Vector search latency
- LLM API response times
- Memory usage
- Active conversations

### Deployment Architecture

**Development:**
```
localhost:8000 (FastAPI)
localhost:6333 (Qdrant)
localhost:7687 (Neo4j)
localhost:5432 (PostgreSQL)
```

**Production (Recommended):**
```
Load Balancer
   ├─→ API Instance 1
   ├─→ API Instance 2
   └─→ API Instance N
       ↓
┌──────────────────────┐
│  Managed Services    │
├──────────────────────┤
│  Qdrant Cloud        │
│  Neo4j Aura          │
│  AWS RDS (Postgres)  │
└──────────────────────┘
```

### API Versioning

- Current version: `/api/v1/`
- Future versions: `/api/v2/`, etc.
- Maintain backward compatibility for at least 2 versions

### Documentation Standards

- **Code Documentation**: Docstrings for all public methods
- **API Documentation**: Auto-generated with FastAPI/OpenAPI
- **Architecture**: This document
- **Setup Guide**: `docs/SETUP.md`
- **User Guide**: `README.md`

---

**Last Updated**: November 2025
**Version**: 1.0.0
**Author**: David Buitrago
